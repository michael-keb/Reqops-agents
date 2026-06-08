"""Local signal card store — mirrors ReqOps ThoughtNode CRUD for dev/testing."""

from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .actions import validate_add, validate_add_draft, validate_edit, validate_remove
from .columns import COLUMN_BY_ID, SignalColumn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return secrets.token_hex(12)


@dataclass
class MutationResult:
    ok: bool
    action: str
    error: str | None = None
    conflict: bool = False
    not_found: bool = False
    node: dict[str, Any] | None = None


@dataclass
class SignalStore:
    session_dir: Path
    _nodes: list[dict[str, Any]] = field(default_factory=list)
    _revisions: list[dict[str, Any]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def store_dir(self) -> Path:
        return self.session_dir / "signals-v01"

    @property
    def store_path(self) -> Path:
        return self.store_dir / "store.json"

    def load(self) -> None:
        path = self.store_path
        if not path.is_file():
            self._nodes = []
            self._revisions = []
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._nodes = []
            self._revisions = []
            return
        self._nodes = list(data.get("nodes") or [])
        self._revisions = list(data.get("revisions") or [])

    def save(self) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        payload = {"nodes": self._nodes, "revisions": self._revisions}
        self.store_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def active_nodes(self, column_id: str) -> list[dict[str, Any]]:
        return [
            n
            for n in self._nodes
            if n.get("column") == column_id and not n.get("deletedAt")
        ]

    def column_snapshot(self, column_id: str) -> list[dict[str, Any]]:
        """Prompt-facing snapshot: id, updatedAt, title, body, evidence, etc."""
        out: list[dict[str, Any]] = []
        for n in self.active_nodes(column_id):
            out.append(
                {
                    "id": n["id"],
                    "updatedAt": n["updatedAt"],
                    "title": n.get("title") or "",
                    "body": n.get("body") or "",
                    "evidence": list(n.get("evidence") or []),
                    "confidence": n.get("confidence") or "medium",
                    "cardState": n.get("cardState") or "emerging",
                    "createdBy": n.get("createdBy") or "agent",
                }
            )
        return out

    def _known_ids(self, column_id: str) -> set[str]:
        return {n["id"] for n in self.active_nodes(column_id)}

    def _find(self, node_id: str) -> dict[str, Any] | None:
        for n in self._nodes:
            if n.get("id") == node_id and not n.get("deletedAt"):
                return n
        return None

    def _record_revision(self, node: dict[str, Any], *, reason: str, run_id: str) -> None:
        self._revisions.append(
            {
                "nodeId": node["id"],
                "reason": reason,
                "run_id": run_id,
                "at": _now_iso(),
                "snapshot": dict(node),
            }
        )

    def _card_to_node(
        self,
        *,
        column: SignalColumn,
        card: dict[str, Any],
        run_id: str,
    ) -> dict[str, Any]:
        confidence = str(card.get("confidence") or "medium").lower()
        body_text = str(card.get("body") or "").strip()
        if body_text:
            card_state = "review" if confidence == "inferred" else "emerging"
        else:
            card_state = "draft"
        evidence = card.get("evidence")
        if isinstance(evidence, str):
            evidence = [evidence]
        structured: dict[str, Any] = {
            "title": str(card.get("title") or "").strip(),
            "description": str(card.get("body") or "").strip(),
        }
        if evidence:
            structured["evidence"] = [
                {"quote_or_paraphrase": str(e).strip(), "inferred_vs_explicit": "explicit"}
                for e in evidence
                if str(e).strip()
            ]
        rationale = card.get("rationale")
        if isinstance(rationale, dict):
            structured["rationale"] = rationale
        title = structured["title"]
        body = structured["description"]
        content = f"{title}\n\n{body}".strip() if title else body
        now = _now_iso()
        return {
            "id": _new_id(),
            "column": column.id,
            "type": column.node_type,
            "title": title,
            "body": body,
            "content": content,
            "evidence": list(evidence or []) if isinstance(evidence, list) else [],
            "confidence": confidence,
            "rationale": rationale,
            "cardState": card_state,
            "createdBy": "agent",
            "updatedAt": now,
            "deletedAt": None,
            "archived": False,
            "structured": structured,
            "run_id": run_id,
        }

    def list_active_nodes(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(n) for n in self._nodes if not n.get("deletedAt")]

    def mutate(self, action: dict[str, Any], *, run_id: str) -> MutationResult:
        with self._lock:
            return self._mutate_unlocked(action, run_id=run_id)

    def _mutate_unlocked(self, action: dict[str, Any], *, run_id: str) -> MutationResult:
        verb = str(action.get("action") or "").lower()
        column_id = str(action.get("column") or "")
        column = COLUMN_BY_ID.get(column_id)
        if not column:
            return MutationResult(ok=False, action=verb, error=f"unknown column {column_id}")

        if verb == "add":
            err = validate_add(action, expected_column=column_id)
            if err:
                return MutationResult(ok=False, action=verb, error=err)
            card = action.get("card")
            assert isinstance(card, dict)
            node = self._card_to_node(column=column, card=card, run_id=run_id)
            self._nodes.append(node)
            self._record_revision(node, reason="agent-add", run_id=run_id)
            self.save()
            return MutationResult(ok=True, action=verb, node=node)

        if verb == "add_draft":
            err = validate_add_draft(action, expected_column=column_id)
            if err:
                return MutationResult(ok=False, action=verb, error=err)
            card = action.get("card")
            assert isinstance(card, dict)
            draft_card = {**card, "body": "", "confidence": card.get("confidence") or "medium"}
            node = self._card_to_node(column=column, card=draft_card, run_id=run_id)
            node["cardState"] = "draft"
            self._nodes.append(node)
            self._record_revision(node, reason="agent-add-draft", run_id=run_id)
            self.save()
            return MutationResult(ok=True, action=verb, node=node)

        known = self._known_ids(column_id)

        if verb == "edit":
            err = validate_edit(action, expected_column=column_id, known_ids=known)
            if err:
                not_found = err.startswith("unknown id")
                return MutationResult(ok=False, action=verb, error=err, not_found=not_found)
            node = self._find(str(action["id"]))
            if not node:
                return MutationResult(ok=False, action=verb, error="node not found", not_found=True)
            if str(action.get("updatedAt") or "") != str(node.get("updatedAt") or ""):
                return MutationResult(ok=False, action=verb, error="updatedAt conflict", conflict=True)
            patch = action.get("patch")
            assert isinstance(patch, dict)
            for key in ("title", "body", "confidence", "rationale"):
                if key in patch:
                    node[key] = patch[key]
            if "evidence" in patch:
                ev = patch["evidence"]
                node["evidence"] = ev if isinstance(ev, list) else [ev]
            if node.get("title") and node.get("body"):
                node["content"] = f"{node['title']}\n\n{node['body']}".strip()
            conf = str(node.get("confidence") or "").lower()
            if conf == "inferred":
                node["cardState"] = "review"
            elif conf in ("high", "medium"):
                node["cardState"] = "emerging"
            structured = dict(node.get("structured") or {})
            structured["title"] = node.get("title")
            structured["description"] = node.get("body")
            if node.get("evidence"):
                structured["evidence"] = [
                    {"quote_or_paraphrase": str(e), "inferred_vs_explicit": "explicit"}
                    for e in node["evidence"]
                    if str(e).strip()
                ]
            node["structured"] = structured
            node["updatedAt"] = _now_iso()
            self._record_revision(node, reason="agent-edit", run_id=run_id)
            self.save()
            return MutationResult(ok=True, action=verb, node=node)

        if verb == "remove":
            err = validate_remove(action, expected_column=column_id, known_ids=known)
            if err:
                not_found = err.startswith("unknown id")
                return MutationResult(ok=False, action=verb, error=err, not_found=not_found)
            node = self._find(str(action["id"]))
            if not node:
                return MutationResult(ok=False, action=verb, error="node not found", not_found=True)
            if str(action.get("updatedAt") or "") != str(node.get("updatedAt") or ""):
                return MutationResult(ok=False, action=verb, error="updatedAt conflict", conflict=True)
            node["deletedAt"] = _now_iso()
            node["archived"] = True
            node["updatedAt"] = node["deletedAt"]
            node["removeReason"] = str(action.get("reason") or "")
            self._record_revision(node, reason="agent-remove", run_id=run_id)
            self.save()
            return MutationResult(ok=True, action=verb, node=node)

        if verb == "complete":
            return MutationResult(ok=True, action=verb)

        return MutationResult(ok=False, action=verb, error=f"unknown action {verb}")
