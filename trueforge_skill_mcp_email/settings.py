from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from config_loader import get_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _bool(value: Any, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def enabled() -> bool:
    env = os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_ENABLED")
    if env is not None:
        return _bool(env, True)
    return _bool(get_config("trueforge_skill_mcp_email_poc.enabled", default=True), True)


def host() -> str:
    return str(
        os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_HOST")
        or get_config("trueforge_skill_mcp_email_poc.host", default="127.0.0.1")
        or "127.0.0.1"
    ).strip()


def port() -> int:
    value = os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_PORT") or get_config(
        "trueforge_skill_mcp_email_poc.port", default=8833
    )
    try:
        return int(value)
    except Exception:
        return 8833


def request_context_file() -> Path | None:
    value = (
        os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_REQUEST_CONTEXT_FILE")
        or get_config("trueforge_skill_mcp_email_poc.request_context_file", default="")
        or ""
    )
    text = str(value).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def mcp_allowed_hosts() -> list[str]:
    configured = os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_ALLOWED_HOSTS", "")
    values = [x.strip() for x in configured.split(",") if x.strip()]
    if values:
        return values
    p = port()
    return [f"localhost:{p}", f"127.0.0.1:{p}", "localhost", "127.0.0.1"]


def mcp_allowed_origins() -> list[str]:
    configured = os.getenv("TRUEFORGE_EMAIL_SKILL_MCP_ALLOWED_ORIGINS", "")
    values = [x.strip() for x in configured.split(",") if x.strip()]
    if values:
        return values
    return [
        "http://localhost:8790",
        "http://127.0.0.1:8790",
        f"http://localhost:{port()}",
        f"http://127.0.0.1:{port()}",
    ]
