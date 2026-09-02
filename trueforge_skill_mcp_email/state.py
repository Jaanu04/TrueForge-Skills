from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Iterable

from sdc_session_manager import SDCSessionManager
from agentic_workflow.common.setup_policy import default_setup_values
from agentic_workflow.graph.nodes.update_state import sync_known_fields_to_session
from agentic_workflow.mcp_tools.business_utils import real_tools_enabled

from .context import normalized_context

_SESSION_PREFIX = "tf-skill-email-"


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}, 0, "0"):
            return value
    return None


def new_spaceid() -> str:
    return _SESSION_PREFIX + uuid.uuid4().hex[:20]


def normalize_spaceid(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return new_spaceid()
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    if not safe:
        return new_spaceid()
    return safe[:120]


def _recover_known_fields(session: Dict[str, Any]) -> Dict[str, Any]:
    agentic = session.get("agentic") if isinstance(session.get("agentic"), dict) else {}
    known = dict(agentic.get("known_fields") or {})
    metadata = session.get("metadata") if isinstance(session.get("metadata"), dict) else {}
    initial = metadata.get("initial_config") if isinstance(metadata.get("initial_config"), dict) else {}
    wdf = session.get("workflow_data_final") if isinstance(session.get("workflow_data_final"), dict) else {}
    email_snap = (
        ((session.get("channel_snapshots") or {}).get("EMAIL") or {})
        if isinstance(session.get("channel_snapshots"), dict)
        else {}
    )

    aliases = {
        "audience": (metadata.get("audience"), metadata.get("audience_list_name"), initial.get("audience")),
        "audience_id": (metadata.get("segmentationListId"), initial.get("segmentationListId"), wdf.get("target_list_id")),
        "audience_count": (wdf.get("total_audience"), email_snap.get("totalAudience")),
        "product_or_offer": (metadata.get("product_name"), metadata.get("topic"), initial.get("product_name")),
        "product_name": (metadata.get("product_name"), metadata.get("topic"), initial.get("product_name")),
        "product_id": (metadata.get("product_id"), initial.get("product_id")),
        "sub_product": (metadata.get("sub_product_name"), metadata.get("edm_topic"), initial.get("sub_product")),
        "sub_product_id": (metadata.get("sub_product_id"), initial.get("sub_product_id")),
        "communication_type": (metadata.get("communication_type"), initial.get("communication_type"), wdf.get("communication_type")),
        "communication_type_id": (metadata.get("communication_type_id"), initial.get("communication_type_id")),
        "campaign_name": (metadata.get("campaign_name"), initial.get("campaign_name"), wdf.get("campaign_name")),
        "start_date": (initial.get("start_date"), wdf.get("start_date")),
        "end_date": (initial.get("end_date"), wdf.get("end_date")),
        "subject": (wdf.get("subject"), metadata.get("subject")),
        "preview_text": (wdf.get("preview"), metadata.get("preview_text")),
        "campaign_id": (wdf.get("campaign_id"), email_snap.get("campaignId"), email_snap.get("communicationID")),
        "channel_detail_id": (wdf.get("email_id"), wdf.get("channel_detail_id"), email_snap.get("channelDetailId"), email_snap.get("emailChannelDetailId")),
        "blast_schedule_guid": (wdf.get("blast_schedule_guid"), email_snap.get("blastScheduleGuid")),
        "communication_status": (wdf.get("communication_status"), email_snap.get("communicationStatus")),
        "approval_status": (wdf.get("approval_status"), email_snap.get("approvalStatus")),
        "edm_html": (wdf.get("edm_html"), metadata.get("edm_html")),
    }
    for key, candidates in aliases.items():
        if known.get(key) in (None, "", [], {}, 0, "0"):
            value = _first_non_empty(*candidates)
            if value not in (None, "", [], {}):
                known[key] = value
    return known


def build_state(spaceid: str, *, prompt: str = "", intent_type: str = "create") -> Dict[str, Any]:
    sid = normalize_spaceid(spaceid)
    manager = SDCSessionManager()
    session = manager.load_session(sid) or {}
    payload, context = normalized_context(sid, prompt)

    session["spaceid"] = sid
    session["space_id"] = sid
    session.setdefault("context", {}).update(
        {key: value for key, value in context.items() if key not in {"raw_request", "edmHTML"} and value not in (None, "", [], {})}
    )
    session.setdefault("agentic", {})["channel"] = "EMAIL"
    session.setdefault("metadata", {})
    session.setdefault("workflow_data_final", {})

    known = _recover_known_fields(session)
    known["channel"] = "EMAIL"
    for key, value in default_setup_values().items():
        known.setdefault(key, value)

    state: Dict[str, Any] = {
        "request": payload,
        "context": context,
        "session": session,
        "latest_prompt": str(prompt or ""),
        "channel": "EMAIL",
        "known_fields": known,
        "normalized_intent": {
            "intent_type": intent_type,
            "channel": "EMAIL",
            "extracted_fields": {},
        },
        "errors": [],
        "token_usage": {},
    }
    sync_known_fields_to_session(state)
    return state


def persist_state(state: Dict[str, Any]) -> None:
    state["channel"] = "EMAIL"
    state.setdefault("known_fields", {})["channel"] = "EMAIL"
    sync_known_fields_to_session(state)
    sid = str((state.get("context") or {}).get("spaceid") or (state.get("session") or {}).get("spaceid") or "")
    if sid:
        SDCSessionManager().save_session(sid, state.get("session") or {})


def set_known_fields(state: Dict[str, Any], values: Dict[str, Any], *, replace_empty: bool = False) -> list[str]:
    known = state.setdefault("known_fields", {})
    changed: list[str] = []
    for key, value in (values or {}).items():
        if key == "channel":
            continue
        if not replace_empty and value in (None, "", [], {}):
            continue
        if known.get(key) != value:
            known[key] = value
            changed.append(key)
    known["channel"] = "EMAIL"
    persist_state(state)
    return changed


def clear_known_fields(state: Dict[str, Any], fields: Iterable[str]) -> None:
    known = state.setdefault("known_fields", {})
    agentic_known = state.setdefault("session", {}).setdefault("agentic", {}).setdefault("known_fields", {})
    for field in fields:
        known.pop(field, None)
        agentic_known.pop(field, None)
    persist_state(state)


def session_summary(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="", intent_type="state_question")
    session = state.get("session") or {}
    agentic = session.get("agentic") if isinstance(session.get("agentic"), dict) else {}
    known = state.get("known_fields") or {}
    email_snap = (
        ((session.get("channel_snapshots") or {}).get("EMAIL") or {})
        if isinstance(session.get("channel_snapshots"), dict)
        else {}
    )
    campaign_id = _first_non_empty(known.get("campaign_id"), email_snap.get("campaignId"))
    channel_detail_id = _first_non_empty(known.get("channel_detail_id"), email_snap.get("channelDetailId"))
    canonical_html = str(known.get("edm_html") or "").strip()
    canonical_draft = bool(campaign_id and channel_detail_id and canonical_html)
    draft_created = canonical_draft if real_tools_enabled() else bool(canonical_draft or agentic.get("draft_created"))

    return {
        "spaceid": normalize_spaceid(spaceid),
        "channel": "EMAIL",
        "workflow_status": _first_non_empty(
            agentic.get("workflow_status"),
            agentic.get("last_workflow_status"),
            session.get("status"),
            "EMAIL_SKILL_MCP_READY",
        ),
        "draft_created": draft_created,
        "canonical_draft_verified": canonical_draft,
        "setup_confirmed": bool(agentic.get("email_setup_confirmed")),
        "campaign_id": campaign_id,
        "channel_detail_id": channel_detail_id,
        "communication_status": _first_non_empty(known.get("communication_status"), email_snap.get("communicationStatus")),
        "approval_status": _first_non_empty(known.get("approval_status"), email_snap.get("approvalStatus")),
        "pending_field": _first_non_empty(agentic.get("pending_field"), ""),
        "known_fields": {
            key: value
            for key, value in known.items()
            if value not in (None, "", [], {}) and key not in {"edm_html", "product_item", "sub_product_item", "communication_type_item", "audience_item"}
        },
        "edm_html_available": bool(str(known.get("edm_html") or "").strip()),
        "edm_html_length": len(str(known.get("edm_html") or "")),
    }
