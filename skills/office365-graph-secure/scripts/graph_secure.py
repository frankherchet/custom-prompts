#!/usr/bin/env python3
"""Secure Microsoft Graph CLI using a local token file only."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
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
TOKEN_FILE_INSECURE_MODE_MASK = stat.S_IRWXG | stat.S_IRWXO
JWT_RE = re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
SECRET_FIELDS = {
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "authorization",
    "proxy-authorization",
}


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


def parse_json_maybe(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


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
    method: str,
    path: str,
    graph_version: str,
    extra_headers: dict[str, str],
    body_file: str | None,
    body_json: str | None,
    timeout_sec: int,
) -> dict[str, Any]:
    token = acquire_file_access_token()
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


def run_doctor() -> dict[str, Any]:
    token_path = os.path.abspath(os.path.expanduser(os.getenv("MS_GRAPH_ACCESS_TOKEN_FILE", "")))
    return {
        "ok": True,
        "auth_mode": "access-token-file",
        "required_env": {
            "MS_GRAPH_ACCESS_TOKEN_FILE": bool(os.getenv("MS_GRAPH_ACCESS_TOKEN_FILE")),
        },
        "graph_version": os.getenv("MS_GRAPH_API_VERSION", DEFAULT_GRAPH_VERSION),
        "token_file": inspect_private_file(token_path) if token_path else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Secure Microsoft Graph CLI that reads the bearer token from MS_GRAPH_ACCESS_TOKEN_FILE."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Validate token-file configuration without printing secret values.")

    request_parser = subparsers.add_parser("request", help="Call Microsoft Graph securely.")
    request_parser.add_argument("--method", default="GET")
    request_parser.add_argument("--path", required=True)
    request_parser.add_argument("--graph-version", default=DEFAULT_GRAPH_VERSION)
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
            emit_json(run_doctor())
            return 0

        if args.command == "request":
            payload = request_graph(
                method=args.method,
                path=args.path,
                graph_version=args.graph_version,
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
