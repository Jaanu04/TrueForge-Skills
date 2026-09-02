from __future__ import annotations

from typing import Any, Dict, Iterable

from agentic_workflow.catalogue.matcher import resolve_catalogue_candidate
from agentic_workflow.catalogue.service import (
    augment_audience_catalogue,
    ensure_catalogue_snapshot,
    refresh_catalogue_snapshot,
)

from .state import persist_state, set_known_fields


def _compact(rows: Iterable[Dict[str, Any]], *, limit: int = 25) -> list[Dict[str, Any]]:
    output = []
    for row in list(rows or [])[: max(1, limit)]:
        item = {"id": row.get("id"), "name": row.get("name")}
        if row.get("parent_product_id") not in (None, ""):
            item["parent_product_id"] = row.get("parent_product_id")
            item["parent_product_name"] = row.get("parent_product_name")
        if row.get("recipient_count") not in (None, ""):
            item["recipient_count"] = row.get("recipient_count")
        output.append(item)
    return output


def _contains_query(row: Dict[str, Any], query: str) -> bool:
    q = " ".join(str(query or "").casefold().split())
    if not q:
        return True
    return q in " ".join(str(row.get("name") or "").casefold().split())


def catalogue_health(state: Dict[str, Any], *, force: bool = False) -> Dict[str, Any]:
    snapshot = refresh_catalogue_snapshot(state) if force else ensure_catalogue_snapshot(state)
    persist_state(state)
    return {
        "ok": bool(snapshot.get("products") and snapshot.get("communication_types")),
        "snapshot_id": snapshot.get("snapshot_id"),
        "stale": bool(snapshot.get("stale")),
        "counts": {
            "products": len(snapshot.get("products") or []),
            "sub_products": len(snapshot.get("sub_products") or []),
            "communication_types": len(snapshot.get("communication_types") or []),
            "audiences": len(snapshot.get("audiences") or []),
        },
        "errors": list(snapshot.get("errors") or []),
    }


def list_products(state: Dict[str, Any], query: str = "", limit: int = 25) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    rows = [row for row in snapshot.get("products") or [] if _contains_query(row, query)]
    persist_state(state)
    return {"ok": bool(rows), "items": _compact(rows, limit=limit), "total": len(rows), "snapshot_id": snapshot.get("snapshot_id"), "errors": list(snapshot.get("errors") or [])}


def validate_product(state: Dict[str, Any], product: str, sub_product: str = "") -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    resolution = resolve_catalogue_candidate(product, snapshot.get("products") or [], field="product_or_offer", state=state, allow_semantic=False)
    if resolution.status != "matched" or not resolution.selected:
        persist_state(state)
        return {"ok": False, "status": resolution.status, "message": "I could not safely validate that product against the current Resulticks catalogue.", "candidates": _compact(resolution.candidates or [], limit=8), "confidence": resolution.confidence}
    selected = resolution.selected
    updates = {"product_or_offer": selected.get("name"), "product_name": selected.get("name"), "product_id": selected.get("id"), "product_item": selected.get("item") or {}, "product_validated": True}
    sub_result: Dict[str, Any] | None = None
    if str(sub_product or "").strip():
        children = (snapshot.get("sub_products_by_product_id") or {}).get(str(selected.get("id"))) or []
        child_resolution = resolve_catalogue_candidate(sub_product, children, field="sub_product", state=state, allow_semantic=False)
        if child_resolution.status != "matched" or not child_resolution.selected:
            persist_state(state)
            return {"ok": False, "status": child_resolution.status, "message": f"The product '{selected.get('name')}' is valid, but I could not safely validate that sub-product.", "product": {"id": selected.get("id"), "name": selected.get("name")}, "sub_product_candidates": _compact(child_resolution.candidates or children, limit=8)}
        child = child_resolution.selected
        updates.update({"sub_product": child.get("name"), "sub_product_name": child.get("name"), "sub_product_id": child.get("id"), "sub_product_item": child.get("item") or {}, "sub_product_validated": True})
        sub_result = {"id": child.get("id"), "name": child.get("name")}
    set_known_fields(state, updates)
    return {"ok": True, "product": {"id": selected.get("id"), "name": selected.get("name")}, "sub_product": sub_result, "message": f"Validated product: {selected.get('name')}" + (f" / {sub_result['name']}" if sub_result else "")}


def list_sub_products(state: Dict[str, Any], product: str = "", limit: int = 25) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    known = state.get("known_fields") or {}
    product_id = known.get("product_id")
    product_name = known.get("product_name") or known.get("product_or_offer")
    if str(product or "").strip():
        resolution = resolve_catalogue_candidate(product, snapshot.get("products") or [], field="product_or_offer", state=state, allow_semantic=False)
        if resolution.status != "matched" or not resolution.selected:
            return {"ok": False, "message": "Validate the parent product first.", "candidates": _compact(resolution.candidates or [], limit=8)}
        product_id = resolution.selected.get("id")
        product_name = resolution.selected.get("name")
    if not product_id:
        return {"ok": False, "message": "Validate a product before requesting its sub-products."}
    rows = (snapshot.get("sub_products_by_product_id") or {}).get(str(product_id)) or []
    persist_state(state)
    return {"ok": True, "product": {"id": product_id, "name": product_name}, "items": _compact(rows, limit=limit), "total": len(rows)}


def list_communication_types(state: Dict[str, Any], query: str = "", limit: int = 25) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    rows = [row for row in snapshot.get("communication_types") or [] if _contains_query(row, query)]
    persist_state(state)
    return {"ok": bool(rows), "items": _compact(rows, limit=limit), "total": len(rows), "errors": list(snapshot.get("errors") or [])}


def validate_communication_type(state: Dict[str, Any], communication_type: str) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    resolution = resolve_catalogue_candidate(communication_type, snapshot.get("communication_types") or [], field="communication_type", state=state, allow_semantic=False)
    if resolution.status != "matched" or not resolution.selected:
        persist_state(state)
        return {"ok": False, "status": resolution.status, "message": "I could not safely validate that communication type.", "candidates": _compact(resolution.candidates or [], limit=8)}
    selected = resolution.selected
    set_known_fields(state, {"communication_type": selected.get("name"), "communication_type_id": selected.get("id"), "communication_type_item": selected.get("item") or {}, "communication_type_validated": True})
    return {"ok": True, "communication_type": {"id": selected.get("id"), "name": selected.get("name")}, "message": f"Validated communication type: {selected.get('name')}"}


def list_audiences(state: Dict[str, Any], query: str = "", limit: int = 25) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    if str(query or "").strip():
        snapshot = augment_audience_catalogue(state, query)
    rows = [row for row in snapshot.get("audiences") or [] if _contains_query(row, query)]
    persist_state(state)
    return {"ok": bool(rows), "items": _compact(rows, limit=limit), "total": len(rows), "errors": list(snapshot.get("errors") or [])}


def validate_audience(state: Dict[str, Any], audience: str) -> Dict[str, Any]:
    snapshot = ensure_catalogue_snapshot(state)
    snapshot = augment_audience_catalogue(state, audience)
    resolution = resolve_catalogue_candidate(audience, snapshot.get("audiences") or [], field="audience", state=state, allow_semantic=False)
    if resolution.status != "matched" or not resolution.selected:
        persist_state(state)
        return {"ok": False, "status": resolution.status, "message": "I could not safely validate that audience/list against the current Resulticks audience service.", "candidates": _compact(resolution.candidates or [], limit=8)}
    selected = resolution.selected
    set_known_fields(state, {"audience": selected.get("name"), "audience_id": selected.get("id"), "audience_count": selected.get("recipient_count"), "audience_item": selected.get("item") or {}, "audience_validated": True})
    return {"ok": True, "audience": {"id": selected.get("id"), "name": selected.get("name"), "recipient_count": selected.get("recipient_count")}, "message": f"Validated audience: {selected.get('name')}"}
