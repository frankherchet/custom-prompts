#!/usr/bin/env python3
"""Create or update the local Microsoft Graph token file safely."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import sys
import tempfile
from typing import Any


DEFAULT_TOKEN_PATH = os.path.expanduser("~/.config/codex-secrets/ms-graph-token.json")
DIR_MODE = 0o700
FILE_MODE = 0o600
INSECURE_MODE_MASK = stat.S_IRWXG | stat.S_IRWXO


class CliError(Exception):
    """Raised for user-facing command errors."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update a local Microsoft Graph token file with secure permissions."
    )
    parser.add_argument(
        "--path",
        default=DEFAULT_TOKEN_PATH,
        help=f"Token file path. Default: {DEFAULT_TOKEN_PATH}",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read the token from stdin instead of prompting without echo.",
    )
    parser.add_argument(
        "--print-export",
        action="store_true",
        help="Print the export command for MS_GRAPH_ACCESS_TOKEN_FILE after writing.",
    )
    return parser


def ensure_secure_directory(path: str) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=DIR_MODE, exist_ok=True)
    os.chmod(directory, DIR_MODE)


def read_token(use_stdin: bool) -> str:
    if use_stdin:
        token = sys.stdin.read().strip()
    else:
        first = getpass.getpass("Microsoft Graph access token: ").strip()
        second = getpass.getpass("Repeat token: ").strip()
        if first != second:
            raise CliError("The two token entries did not match.")
        token = first

    if not token:
        raise CliError("Token must not be empty.")
    return token


def write_json_atomic(path: str, payload: dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    fd, temp_path = tempfile.mkstemp(prefix=".ms-graph-token-", dir=directory, text=True)
    try:
        os.fchmod(fd, FILE_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, path)
        os.chmod(path, FILE_MODE)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def inspect_path(path: str) -> dict[str, Any]:
    exists = os.path.exists(path)
    info: dict[str, Any] = {
        "path": path,
        "exists": exists,
        "is_regular_file": False,
        "owner_only_permissions": False,
    }
    if not exists:
        return info
    stats = os.stat(path)
    info["is_regular_file"] = stat.S_ISREG(stats.st_mode)
    info["owner_only_permissions"] = not bool(stats.st_mode & INSECURE_MODE_MASK)
    return info


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    token_path = os.path.abspath(os.path.expanduser(args.path))

    try:
        ensure_secure_directory(token_path)
        token = read_token(args.stdin)
        write_json_atomic(token_path, {"access_token": token})
        info = inspect_path(token_path)
        output = {
            "ok": True,
            "path": info["path"],
            "exists": info["exists"],
            "is_regular_file": info["is_regular_file"],
            "owner_only_permissions": info["owner_only_permissions"],
        }
        if args.print_export:
            output["export"] = f'export MS_GRAPH_ACCESS_TOKEN_FILE="{token_path}"'
        json.dump(output, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except CliError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stderr, indent=2, sort_keys=True)
        sys.stderr.write("\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
