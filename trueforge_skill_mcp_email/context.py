from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from agentic_workflow.api.request_context import extract_request_context

from . import settings

_LOCK = threading.RLock()


def _load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Request context file was not found: {path}. Copy request_context.example.json "
            "to request_context.local.json and fill it from a working /workflow/process request."
        )
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Request context file must contain one JSON object: {path}")
    return value


def base_request_context() -> Dict[str, Any]:
    """Reload the configured context on every call so refreshed auth is picked up."""
    path = settings.request_context_file()
    if path is None:
        return {}
    with _LOCK:
        return deepcopy(_load_json_file(path))


def build_request_payload(spaceid: str, prompt: str = "") -> Dict[str, Any]:
    payload = base_request_context()
    payload["spaceid"] = spaceid
    payload["conversationid"] = payload.get("conversationid") or spaceid
    payload["prompt"] = str(prompt or "")
    payload["channel"] = "EMAIL"
    payload["_trueforge_skill_mcp_poc"] = True

    nested = payload.get("req") if isinstance(payload.get("req"), dict) else {}
    if nested:
        nested = deepcopy(nested)
        nested["spaceid"] = spaceid
        nested["userprompt"] = str(prompt or "")
        nested["prompt"] = str(prompt or "")
        payload["req"] = nested
    return payload


def normalized_context(spaceid: str, prompt: str = "") -> tuple[Dict[str, Any], Dict[str, Any]]:
    payload = build_request_payload(spaceid, prompt)
    ctx = extract_request_context(payload)
    context = ctx.to_dict()
    context["spaceid"] = spaceid
    context["latest_prompt"] = str(prompt or "")
    context["raw_request"] = payload
    return payload, context


def validate_request_context() -> Dict[str, Any]:
    """Return actionable diagnostics without exposing auth tokens or secrets."""
    path = settings.request_context_file()
    if path is None:
        return {
            "ok": False,
            "message": "No request-context file is configured.",
            "missing": ["request_context_file"],
        }
    try:
        payload = base_request_context()
        ctx = extract_request_context(payload)
    except Exception as exc:
        return {"ok": False, "message": str(exc), "missing": []}

    required = {
        "clientId": ctx.clientId,
        "departmentId": ctx.departmentId,
        "userId": ctx.userId,
        "camp_ServerIP": ctx.camp_ServerIP,
        "camp_DatabaseName": ctx.camp_DatabaseName,
        "cust_ServerIP": ctx.cust_ServerIP,
        "cust_DatabaseName": ctx.cust_DatabaseName,
        "aud_ServerIP": ctx.aud_ServerIP,
        "aud_DatabaseName": ctx.aud_DatabaseName,
        "authorization": ctx.authorization,
        "reqs": ctx.reqs,
    }

    def incomplete(value: Any) -> bool:
        if value in (None, "", [], {}, 0, "0"):
            return True
        text = str(value).strip().upper()
        return text.startswith("YOUR_") or text.startswith("PASTE_")

    missing = [key for key, value in required.items() if incomplete(value)]
    return {
        "ok": not missing,
        "path": str(path),
        "missing": missing,
        "scope": {
            "t1": ctx.t1,
            "b1": ctx.b1,
            "clientId": ctx.clientId,
            "departmentId": ctx.departmentId,
            "userId": ctx.userId,
            "camp_DatabaseName": ctx.camp_DatabaseName,
            "cust_DatabaseName": ctx.cust_DatabaseName,
            "aud_DatabaseName": ctx.aud_DatabaseName,
            "has_authorization": bool(ctx.authorization),
            "has_reqs": bool(ctx.reqs),
        },
        "message": "Request context is ready." if not missing else "Request context is incomplete.",
    }
