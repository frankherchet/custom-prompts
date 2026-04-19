#!/usr/bin/env python3
"""Secure Microsoft Graph CLI for Office 365 / Microsoft 365 tasks."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from typing import Any
from urllib import error, parse, request


GRAPH_HOST = "graph.microsoft.com"
GRAPH_RESOURCE = f"https://{GRAPH_HOST}"
DEFAULT_GRAPH_VERSION = os.getenv("MS_GRAPH_API_VERSION", "v1.0")
DEFAULT_TIMEOUT_SEC = int(os.getenv("MS_GRAPH_TIMEOUT_SEC", "60"))
DEFAULT_USER_AGENT = os.getenv(
    "MS_GRAPH_USER_AGENT",
    "codex-office365-graph-secure/1.0",
)
DEFAULT_BROWSER_REDIRECT_URI = os.getenv(
    "MS_GRAPH_REDIRECT_URI",
    "http://127.0.0.1:8765/callback",
)
DEFAULT_TOKEN_CACHE_FILE = os.path.expanduser(
    os.getenv("MS_GRAPH_TOKEN_CACHE_FILE", "~/.config/codex-secrets/ms-graph-auth.json")
)
DEFAULT_BROWSER_TIMEOUT_SEC = int(os.getenv("MS_GRAPH_BROWSER_TIMEOUT_SEC", "300"))
TOKEN_EXPIRY_SKEW_SEC = 120

JWT_RE = re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
SECRET_FIELDS = {
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "authorization",
    "proxy-authorization",
}
DEFAULT_DEVICE_SCOPES = ["User.Read"]
BROWSER_OIDC_SCOPES = ["offline_access", "openid", "profile"]
TOKEN_FILE_INSECURE_MODE_MASK = stat.S_IRWXG | stat.S_IRWXO
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


class CliError(Exception):
    """Raised for user-facing command errors."""


class HttpFailure(Exception):
    """Carries a sanitized HTTP failure response."""

    def __init__(self, status: int, headers: dict[str, str], body: str) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status
        self.headers = headers
        self.body = body


def redact_text(value: str) -> str:
    return JWT_RE.sub("[REDACTED_TOKEN]", value)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            lowered = key.lower()
            if lowered in SECRET_FIELDS or lowered.endswith("_token"):
                sanitized[key] = child if isinstance(child, bool) or child is None else "[REDACTED]"
            else:
                sanitized[key] = sanitize_value(child)
        return sanitized
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def error_payload(message: str, *, status: int | None = None, details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "error": redact_text(message)}
    if status is not None:
        payload["status"] = status
    if details is not None:
        payload["details"] = sanitize_value(details)
    return payload


def emit_json(payload: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(sanitize_value(payload), stream, indent=2, sort_keys=True)
    stream.write("\n")


def getenv_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise CliError(f"Missing required environment variable: {name}")
    return value


def split_env_scopes(raw: str) -> list[str]:
    parts = re.split(r"[\s,]+", raw.strip())
    return [part for part in parts if part]


def unique_scopes(scopes: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for scope in scopes:
        if scope not in seen:
            unique.append(scope)
            seen.add(scope)
    return unique


def get_scopes(explicit: list[str]) -> list[str]:
    raw_items = explicit or split_env_scopes(os.getenv("MS_GRAPH_SCOPES", ""))
    scopes = raw_items or DEFAULT_DEVICE_SCOPES
    unique = unique_scopes(scopes)
    if any(scope.endswith("/.default") or scope == ".default" for scope in unique) and len(unique) > 1:
        raise CliError("Do not mix .default with other delegated scopes.")
    return unique


def get_browser_login_scopes(explicit: list[str]) -> list[str]:
    scopes = get_scopes(explicit)
    if any(scope.endswith("/.default") or scope == ".default" for scope in scopes):
        raise CliError("browser-login does not support .default. Use delegated scopes such as User.Read.")
    return unique_scopes(scopes + BROWSER_OIDC_SCOPES)


def token_endpoint(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def device_code_endpoint(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/devicecode"


def authorization_endpoint(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"


def parse_json(text: str) -> Any:
    return json.loads(text)


def parse_json_maybe(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def do_request(
    req: request.Request,
    *,
    timeout_sec: int,
) -> tuple[int, dict[str, str], str, str]:
    try:
        with request.urlopen(req, timeout=timeout_sec) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
            return response.status, dict(response.headers.items()), body, response.headers.get("Content-Type", "")
    except error.HTTPError as exc:
        charset = exc.headers.get_content_charset() or "utf-8"
        body = exc.read().decode(charset, errors="replace")
        raise HttpFailure(exc.code, dict(exc.headers.items()), body) from None
    except error.URLError as exc:
        raise CliError(f"Network error: {exc.reason}") from None


def form_post(url: str, form: dict[str, str], *, timeout_sec: int) -> Any:
    data = parse.urlencode(form).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": DEFAULT_USER_AGENT,
        },
        method="POST",
    )
    _, _, body, _ = do_request(req, timeout_sec=timeout_sec)
    try:
        return parse_json(body)
    except json.JSONDecodeError as exc:
        raise CliError(f"Token endpoint returned invalid JSON: {exc}") from None


def inspect_private_file(path: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": path,
        "exists": False,
        "is_regular_file": False,
        "owner_only_permissions": False,
    }
    if not path:
        return info
    try:
        stats = os.stat(path)
    except OSError:
        return info

    info["exists"] = True
    info["is_regular_file"] = stat.S_ISREG(stats.st_mode)
    info["owner_only_permissions"] = not bool(stats.st_mode & TOKEN_FILE_INSECURE_MODE_MASK)
    return info


def ensure_private_parent_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if not directory:
        return
    os.makedirs(directory, mode=PRIVATE_DIR_MODE, exist_ok=True)
    os.chmod(directory, PRIVATE_DIR_MODE)


def write_private_json(path: str, payload: dict[str, Any]) -> None:
    ensure_private_parent_dir(path)
    directory = os.path.dirname(path) or "."
    fd, temp_path = tempfile.mkstemp(prefix=".graph-auth-", dir=directory, text=True)
    try:
        os.fchmod(fd, PRIVATE_FILE_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, path)
        os.chmod(path, PRIVATE_FILE_MODE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def load_private_json(path: str) -> dict[str, Any] | None:
    info = inspect_private_file(path)
    if not info["exists"]:
        return None
    if not info["is_regular_file"]:
        raise CliError(f"{path} must be a regular file.")
    if not info["owner_only_permissions"]:
        raise CliError(f"{path} permissions are too broad. Require owner-only access, for example chmod 600.")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise CliError(f"{path} must contain valid JSON.") from exc
    if not isinstance(data, dict):
        raise CliError(f"{path} must contain a JSON object.")
    return data


def default_token_cache_path() -> str:
    return os.path.abspath(os.path.expanduser(DEFAULT_TOKEN_CACHE_FILE))


def acquire_client_credentials_token(timeout_sec: int) -> str:
    tenant = getenv_required("MS_GRAPH_TENANT_ID")
    client_id = getenv_required("MS_GRAPH_CLIENT_ID")
    client_secret = getenv_required("MS_GRAPH_CLIENT_SECRET")
    payload = form_post(
        token_endpoint(tenant),
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": f"{GRAPH_RESOURCE}/.default",
        },
        timeout_sec=timeout_sec,
    )
    token = payload.get("access_token")
    if not token:
        raise CliError("Token response did not include an access token.")
    return token


def acquire_device_code_token(scopes: list[str], timeout_sec: int) -> str:
    tenant = getenv_required("MS_GRAPH_TENANT_ID")
    client_id = getenv_required("MS_GRAPH_CLIENT_ID")
    payload = form_post(
        device_code_endpoint(tenant),
        {
            "client_id": client_id,
            "scope": " ".join(scopes),
        },
        timeout_sec=timeout_sec,
    )

    device_code = payload.get("device_code")
    if not device_code:
        raise CliError("Device code response did not include a device_code.")

    message = payload.get("message")
    if message:
        print(message, file=sys.stderr)
    else:
        verification_uri = payload.get("verification_uri", "https://microsoft.com/devicelogin")
        user_code = payload.get("user_code", "<missing-user-code>")
        print(f"Open {verification_uri} and enter code {user_code}", file=sys.stderr)

    interval = int(payload.get("interval", 5))
    expires_at = time.time() + int(payload.get("expires_in", 900))

    while time.time() < expires_at:
        time.sleep(interval)
        try:
            token_payload = form_post(
                token_endpoint(tenant),
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": client_id,
                    "device_code": device_code,
                },
                timeout_sec=timeout_sec,
            )
        except HttpFailure as exc:
            data = parse_json_maybe(exc.body) or {}
            code = data.get("error")
            if code == "authorization_pending":
                continue
            if code == "slow_down":
                interval += 5
                continue
            if code in {"authorization_declined", "expired_token", "bad_verification_code"}:
                raise CliError(f"Device code flow failed: {code}") from None
            raise CliError(
                f"Device code polling failed with HTTP {exc.status}: {redact_text(exc.body)}"
            ) from None

        token = token_payload.get("access_token")
        if token:
            return token
        raise CliError("Token response did not include an access token.")

    raise CliError("Device code expired before sign-in completed.")


def acquire_env_access_token() -> str:
    token = getenv_required("MS_GRAPH_ACCESS_TOKEN").strip()
    os.environ.pop("MS_GRAPH_ACCESS_TOKEN", None)
    if not token:
        raise CliError("MS_GRAPH_ACCESS_TOKEN is empty.")
    return token


def parse_token_file_content(raw: str) -> str:
    stripped = raw.strip()
    if not stripped:
        raise CliError("Token file is empty.")

    parsed = parse_json_maybe(stripped)
    if isinstance(parsed, dict):
        token = parsed.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise CliError("Token JSON file must contain a non-empty access_token string.")
        return token.strip()

    return stripped


def acquire_file_access_token() -> str:
    token_path = os.path.abspath(os.path.expanduser(getenv_required("MS_GRAPH_ACCESS_TOKEN_FILE")))
    info = inspect_private_file(token_path)
    if not info["exists"]:
        raise CliError("MS_GRAPH_ACCESS_TOKEN_FILE does not exist.")
    if not info["is_regular_file"]:
        raise CliError("MS_GRAPH_ACCESS_TOKEN_FILE must point to a regular file.")
    if not info["owner_only_permissions"]:
        raise CliError("Token file permissions are too broad. Require owner-only access, for example chmod 600.")

    with open(token_path, "r", encoding="utf-8") as handle:
        return parse_token_file_content(handle.read())


def get_browser_redirect_uri() -> str:
    return DEFAULT_BROWSER_REDIRECT_URI


def validate_browser_redirect_uri(redirect_uri: str) -> parse.ParseResult:
    parsed = parse.urlparse(redirect_uri)
    if parsed.scheme != "http":
        raise CliError("browser-login currently requires an http localhost redirect URI.")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise CliError("browser-login redirect URI must use localhost or 127.0.0.1.")
    if not parsed.port:
        raise CliError("browser-login redirect URI must include an explicit port.")
    if parsed.query or parsed.fragment:
        raise CliError("browser-login redirect URI must not include a query string or fragment.")
    return parsed


def make_code_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(64)).decode("ascii").rstrip("=")


def make_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def cached_scope_set(payload: dict[str, Any]) -> set[str]:
    return set(split_env_scopes(str(payload.get("scope", ""))))


def browser_cache_matches(payload: dict[str, Any], scopes: list[str]) -> bool:
    required_scopes = set(get_browser_login_scopes(scopes))
    return (
        payload.get("tenant") == os.getenv("MS_GRAPH_TENANT_ID")
        and payload.get("client_id") == os.getenv("MS_GRAPH_CLIENT_ID")
        and payload.get("redirect_uri") == get_browser_redirect_uri()
        and required_scopes.issubset(cached_scope_set(payload))
    )


def token_is_fresh(payload: dict[str, Any]) -> bool:
    access_token = payload.get("access_token")
    expires_at = int(payload.get("expires_at", 0) or 0)
    return bool(access_token) and expires_at > int(time.time()) + TOKEN_EXPIRY_SKEW_SEC


def normalize_token_payload(
    token_payload: dict[str, Any],
    *,
    scopes: list[str],
    auth_mode: str,
) -> dict[str, Any]:
    access_token = token_payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise CliError("Token response did not include an access token.")
    refresh_token = token_payload.get("refresh_token")
    expires_in_raw = token_payload.get("expires_in", 3600)
    try:
        expires_in = int(expires_in_raw)
    except (TypeError, ValueError) as exc:
        raise CliError(f"Invalid expires_in value in token response: {expires_in_raw}") from exc

    scope_string = token_payload.get("scope")
    if not isinstance(scope_string, str) or not scope_string.strip():
        scope_string = " ".join(get_browser_login_scopes(scopes))

    normalized = {
        "access_token": access_token.strip(),
        "expires_at": int(time.time()) + expires_in,
        "obtained_at": int(time.time()),
        "scope": scope_string,
        "token_type": token_payload.get("token_type"),
        "tenant": os.getenv("MS_GRAPH_TENANT_ID"),
        "client_id": os.getenv("MS_GRAPH_CLIENT_ID"),
        "redirect_uri": get_browser_redirect_uri(),
        "auth_mode": auth_mode,
    }
    if isinstance(refresh_token, str) and refresh_token.strip():
        normalized["refresh_token"] = refresh_token.strip()
    if isinstance(token_payload.get("id_token"), str) and token_payload["id_token"].strip():
        normalized["id_token"] = token_payload["id_token"].strip()
    return normalized


def open_browser(authorize_url: str) -> None:
    print("Opening browser for Microsoft sign-in...", file=sys.stderr)
    opened = webbrowser.open(authorize_url, new=1, autoraise=True)
    if not opened:
        print("Browser open failed. Open this URL manually:", file=sys.stderr)
        print(authorize_url, file=sys.stderr)


def wait_for_browser_callback(
    redirect_uri: str,
    *,
    state: str,
    timeout_sec: int,
) -> str:
    parsed_redirect = validate_browser_redirect_uri(redirect_uri)
    callback_event = Event()
    callback_payload: dict[str, str] = {}
    expected_path = parsed_redirect.path or "/"

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed_request = parse.urlparse(self.path)
            if parsed_request.path != expected_path:
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Not found.\n")
                return

            params = parse.parse_qs(parsed_request.query)
            callback_payload.update({key: values[0] for key, values in params.items() if values})
            callback_event.set()

            is_error = "error" in callback_payload
            self.send_response(400 if is_error else 200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            body = (
                "<html><body><h1>Microsoft Graph login failed</h1>"
                "<p>You can close this window and return to the terminal.</p></body></html>"
                if is_error
                else "<html><body><h1>Microsoft Graph login complete</h1>"
                "<p>You can close this window and return to the terminal.</p></body></html>"
            )
            self.wfile.write(body.encode("utf-8"))

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    class ReusableHTTPServer(HTTPServer):
        allow_reuse_address = True

    try:
        server = ReusableHTTPServer((parsed_redirect.hostname or "127.0.0.1", parsed_redirect.port), CallbackHandler)
    except OSError as exc:
        raise CliError(
            f"Unable to bind local callback server on {redirect_uri}. "
            "Check that the port is free and the redirect URI matches the registered app."
        ) from exc

    server.timeout = 1

    def serve() -> None:
        deadline = time.time() + timeout_sec
        while not callback_event.is_set() and time.time() < deadline:
            server.handle_request()

    worker = Thread(target=serve, daemon=True)
    worker.start()
    callback_event.wait(timeout_sec)
    server.server_close()
    worker.join(timeout=1)

    if not callback_event.is_set():
        raise CliError("Timed out waiting for the Microsoft login callback.")

    if callback_payload.get("state") != state:
        raise CliError("Browser login state mismatch.")
    if "error" in callback_payload:
        description = callback_payload.get("error_description", callback_payload["error"])
        raise CliError(f"Browser login failed: {description}")
    code = callback_payload.get("code")
    if not code:
        raise CliError("Browser login callback did not include an authorization code.")
    return code


def exchange_authorization_code(
    *,
    code: str,
    code_verifier: str,
    scopes: list[str],
    timeout_sec: int,
) -> dict[str, Any]:
    tenant = getenv_required("MS_GRAPH_TENANT_ID")
    client_id = getenv_required("MS_GRAPH_CLIENT_ID")
    redirect_uri = get_browser_redirect_uri()
    payload = form_post(
        token_endpoint(tenant),
        {
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": " ".join(get_browser_login_scopes(scopes)),
            "code_verifier": code_verifier,
        },
        timeout_sec=timeout_sec,
    )
    return normalize_token_payload(payload, scopes=scopes, auth_mode="browser-login")


def refresh_browser_login_token(scopes: list[str], timeout_sec: int) -> dict[str, Any] | None:
    cache_path = default_token_cache_path()
    cached = load_private_json(cache_path)
    if not cached or not browser_cache_matches(cached, scopes):
        return None
    refresh_token = cached.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        return None

    tenant = getenv_required("MS_GRAPH_TENANT_ID")
    client_id = getenv_required("MS_GRAPH_CLIENT_ID")
    try:
        payload = form_post(
            token_endpoint(tenant),
            {
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.strip(),
                "scope": " ".join(get_browser_login_scopes(scopes)),
            },
            timeout_sec=timeout_sec,
        )
    except HttpFailure as exc:
        error_data = parse_json_maybe(exc.body) or {}
        if isinstance(error_data, dict) and error_data.get("error") in {"invalid_grant", "interaction_required"}:
            return None
        raise

    normalized = normalize_token_payload(payload, scopes=scopes, auth_mode="browser-login")
    write_private_json(cache_path, normalized)
    return normalized


def interactive_browser_login(scopes: list[str], timeout_sec: int) -> dict[str, Any]:
    tenant = getenv_required("MS_GRAPH_TENANT_ID")
    client_id = getenv_required("MS_GRAPH_CLIENT_ID")
    redirect_uri = get_browser_redirect_uri()
    validate_browser_redirect_uri(redirect_uri)

    code_verifier = make_code_verifier()
    state = secrets.token_urlsafe(24)
    authorize_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": " ".join(get_browser_login_scopes(scopes)),
        "state": state,
        "code_challenge": make_code_challenge(code_verifier),
        "code_challenge_method": "S256",
    }
    authorize_url = f"{authorization_endpoint(tenant)}?{parse.urlencode(authorize_params)}"
    open_browser(authorize_url)
    code = wait_for_browser_callback(redirect_uri, state=state, timeout_sec=timeout_sec)
    normalized = exchange_authorization_code(
        code=code,
        code_verifier=code_verifier,
        scopes=scopes,
        timeout_sec=timeout_sec,
    )
    write_private_json(default_token_cache_path(), normalized)
    return normalized


def acquire_browser_login_token(scopes: list[str], timeout_sec: int) -> str:
    cache_path = default_token_cache_path()
    cached = load_private_json(cache_path)
    if cached and browser_cache_matches(cached, scopes) and token_is_fresh(cached):
        return str(cached["access_token"])

    refreshed = refresh_browser_login_token(scopes, timeout_sec)
    if refreshed and token_is_fresh(refreshed):
        return str(refreshed["access_token"])

    interactive = interactive_browser_login(scopes, timeout_sec)
    return str(interactive["access_token"])


def build_browser_login_result(scopes: list[str], token_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "auth_mode": "browser-login",
        "redirect_uri": get_browser_redirect_uri(),
        "token_cache": inspect_private_file(default_token_cache_path()),
        "expires_at": token_payload.get("expires_at"),
        "scopes": get_browser_login_scopes(scopes),
    }


def run_browser_login(scopes: list[str], timeout_sec: int) -> dict[str, Any]:
    cache_path = default_token_cache_path()
    cached = load_private_json(cache_path)
    if cached and browser_cache_matches(cached, scopes) and token_is_fresh(cached):
        return build_browser_login_result(scopes, cached)

    refreshed = refresh_browser_login_token(scopes, timeout_sec)
    if refreshed and token_is_fresh(refreshed):
        return build_browser_login_result(scopes, refreshed)

    interactive = interactive_browser_login(scopes, timeout_sec)
    return build_browser_login_result(scopes, interactive)


def acquire_token(auth_mode: str, scopes: list[str], timeout_sec: int) -> str:
    if auth_mode == "client-credentials":
        return acquire_client_credentials_token(timeout_sec)
    if auth_mode == "device-code":
        return acquire_device_code_token(scopes, timeout_sec)
    if auth_mode == "browser-login":
        return acquire_browser_login_token(scopes, timeout_sec)
    if auth_mode == "access-token-env":
        return acquire_env_access_token()
    if auth_mode == "access-token-file":
        return acquire_file_access_token()
    raise CliError(f"Unsupported auth mode: {auth_mode}")


def normalize_headers(header_args: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in header_args:
        if "=" in item:
            key, value = item.split("=", 1)
        elif ":" in item:
            key, value = item.split(":", 1)
        else:
            raise CliError(f"Invalid header format: {item}")
        key = key.strip()
        value = value.strip()
        if not key:
            raise CliError(f"Invalid empty header name in: {item}")
        lowered = key.lower()
        if lowered in {"authorization", "proxy-authorization"}:
            raise CliError("Do not provide Authorization headers manually.")
        headers[key] = value
    return headers


def load_body(body_file: str | None, body_json: str | None) -> tuple[bytes | None, str | None]:
    if body_file and body_json:
        raise CliError("Use either --body-file or --body-json, not both.")
    if not body_file and not body_json:
        return None, None

    if body_file:
        with open(body_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        try:
            payload = json.loads(body_json or "")
        except json.JSONDecodeError as exc:
            raise CliError(f"--body-json is not valid JSON: {exc}") from None

    return json.dumps(payload).encode("utf-8"), "application/json"


def build_graph_url(path: str, graph_version: str) -> str:
    if not path:
        raise CliError("Missing --path.")

    parsed = parse.urlparse(path)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https" or parsed.netloc != GRAPH_HOST:
            raise CliError("Absolute paths must target https://graph.microsoft.com only.")
        return path

    normalized = path.lstrip("/")
    if normalized.startswith("v1.0/") or normalized.startswith("beta/"):
        return f"{GRAPH_RESOURCE}/{normalized}"
    return f"{GRAPH_RESOURCE}/{graph_version.strip('/')}/{normalized}"


def request_graph(
    *,
    auth_mode: str,
    method: str,
    path: str,
    graph_version: str,
    scopes: list[str],
    extra_headers: dict[str, str],
    body_file: str | None,
    body_json: str | None,
    timeout_sec: int,
) -> dict[str, Any]:
    token = acquire_token(auth_mode, scopes, timeout_sec)
    url = build_graph_url(path, graph_version)
    body_bytes, content_type = load_body(body_file, body_json)

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    headers.update(extra_headers)
    if content_type:
        headers["Content-Type"] = content_type

    req = request.Request(url, data=body_bytes, headers=headers, method=method.upper())

    status, response_headers, body, response_content_type = do_request(req, timeout_sec=timeout_sec)

    parsed_body: Any
    if "json" in response_content_type.lower():
        parsed_body = parse_json_maybe(body)
        if parsed_body is None:
            parsed_body = redact_text(body)
    else:
        parsed_body = redact_text(body)

    return {
        "ok": True,
        "status": status,
        "request_id": response_headers.get("request-id"),
        "client_request_id": response_headers.get("client-request-id"),
        "retry_after": response_headers.get("retry-after"),
        "body": sanitize_value(parsed_body),
    }


def run_doctor(auth_mode: str) -> dict[str, Any]:
    required: list[str]
    if auth_mode == "client-credentials":
        required = ["MS_GRAPH_TENANT_ID", "MS_GRAPH_CLIENT_ID", "MS_GRAPH_CLIENT_SECRET"]
    elif auth_mode in {"device-code", "browser-login"}:
        required = ["MS_GRAPH_TENANT_ID", "MS_GRAPH_CLIENT_ID"]
    elif auth_mode == "access-token-env":
        required = ["MS_GRAPH_ACCESS_TOKEN"]
    elif auth_mode == "access-token-file":
        required = ["MS_GRAPH_ACCESS_TOKEN_FILE"]
    else:
        raise CliError(f"Unsupported auth mode: {auth_mode}")
    present = {name: bool(os.getenv(name)) for name in required}
    return {
        "ok": True,
        "auth_mode": auth_mode,
        "required_env": present,
        "graph_version": os.getenv("MS_GRAPH_API_VERSION", DEFAULT_GRAPH_VERSION),
        "default_device_scopes": get_scopes([]) if auth_mode == "device-code" else [],
        "redirect_uri": get_browser_redirect_uri() if auth_mode == "browser-login" else None,
        "token_file": (
            inspect_private_file(os.path.abspath(os.path.expanduser(os.getenv("MS_GRAPH_ACCESS_TOKEN_FILE", ""))))
            if auth_mode == "access-token-file" and os.getenv("MS_GRAPH_ACCESS_TOKEN_FILE")
            else None
        ),
        "token_cache": inspect_private_file(default_token_cache_path()) if auth_mode == "browser-login" else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secure Microsoft Graph CLI that keeps tokens out of model-visible inputs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_choices = [
        "client-credentials",
        "device-code",
        "browser-login",
        "access-token-env",
        "access-token-file",
    ]

    doctor = subparsers.add_parser("doctor", help="Validate env configuration without printing secret values.")
    doctor.add_argument(
        "--auth-mode",
        choices=auth_choices,
        default=os.getenv("MS_GRAPH_AUTH_MODE", "client-credentials"),
    )

    login = subparsers.add_parser("login", help="Acquire and cache a delegated token through browser-login.")
    login.add_argument("--auth-mode", choices=["browser-login"], default="browser-login")
    login.add_argument("--scope", action="append", default=[])
    login.add_argument("--timeout-sec", type=int, default=DEFAULT_BROWSER_TIMEOUT_SEC)

    request_parser = subparsers.add_parser("request", help="Call Microsoft Graph securely.")
    request_parser.add_argument(
        "--auth-mode",
        choices=auth_choices,
        default=os.getenv("MS_GRAPH_AUTH_MODE", "client-credentials"),
    )
    request_parser.add_argument("--method", default="GET")
    request_parser.add_argument("--path", required=True)
    request_parser.add_argument("--graph-version", default=DEFAULT_GRAPH_VERSION)
    request_parser.add_argument("--scope", action="append", default=[])
    request_parser.add_argument("--header", action="append", default=[])
    request_parser.add_argument("--body-file")
    request_parser.add_argument("--body-json")
    request_parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            emit_json(run_doctor(args.auth_mode))
            return 0

        if args.command == "login":
            emit_json(run_browser_login(get_scopes(args.scope), args.timeout_sec))
            return 0

        if args.command == "request":
            payload = request_graph(
                auth_mode=args.auth_mode,
                method=args.method,
                path=args.path,
                graph_version=args.graph_version,
                scopes=get_scopes(args.scope),
                extra_headers=normalize_headers(args.header),
                body_file=args.body_file,
                body_json=args.body_json,
                timeout_sec=args.timeout_sec,
            )
            emit_json(payload)
            return 0

        raise CliError(f"Unsupported command: {args.command}")
    except HttpFailure as exc:
        details = parse_json_maybe(exc.body) or redact_text(exc.body)
        emit_json(
            error_payload(
                f"HTTP {exc.status}",
                status=exc.status,
                details={
                    "request_id": exc.headers.get("request-id"),
                    "retry_after": exc.headers.get("retry-after"),
                    "body": details,
                },
            ),
            stream=sys.stderr,
        )
        return 1
    except CliError as exc:
        emit_json(error_payload(str(exc)), stream=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
