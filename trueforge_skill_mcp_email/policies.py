from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import yaml

POLICY_FILE = Path(__file__).resolve().parent / "policies" / "email_rules.yaml"


def load_policy() -> Dict[str, Any]:
    with POLICY_FILE.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    return value if isinstance(value, dict) else {}


def required_setup_fields() -> list[str]:
    values = load_policy().get("required_setup_fields") or ["audience", "product_or_offer", "communication_type"]
    return [str(value) for value in values]


def missing_setup_fields(known: Dict[str, Any]) -> list[str]:
    aliases = {
        "product_or_offer": ("product_or_offer", "product_name"),
        "audience": ("audience",),
        "communication_type": ("communication_type",),
    }
    missing: list[str] = []
    for field in required_setup_fields():
        keys = aliases.get(field, (field,))
        if not any(known.get(key) not in (None, "", [], {}) for key in keys):
            missing.append(field)
    return missing


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", str(value or "").strip()))


def guard_setup_complete(known: Dict[str, Any]) -> tuple[bool, list[str]]:
    missing = missing_setup_fields(known)
    return (not missing), missing


def guard_test_preview(known: Dict[str, Any], draft_created: bool) -> tuple[bool, str]:
    if not draft_created:
        return False, "Create and save the Email draft before sending a Test Preview."
    recipient = str(known.get("test_recipient") or "").strip()
    if recipient and not valid_email(recipient):
        return False, "The Test Preview recipient is not a valid email address."
    return True, ""


def guard_rfa(known: Dict[str, Any], draft_created: bool) -> tuple[bool, str]:
    if not draft_created:
        return False, "Create and save the Email draft before requesting approval."
    approver = str(known.get("approver_email") or "").strip()
    if approver and not valid_email(approver):
        return False, "The approver email address is invalid."
    return True, ""
