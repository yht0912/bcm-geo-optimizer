#!/usr/bin/env python3
"""Build a deterministic, constraint-first GEO action queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
LAYER_ORDER = {
    "access": 0,
    "discovery": 1,
    "retrieval": 2,
    "entity": 3,
    "answerability": 4,
    "corroboration": 5,
    "recommendation_fit": 6,
    "conversion": 7,
}
REQUIRED_FIELDS = {
    "action_id",
    "priority_class",
    "limiting_layer",
    "observed_gap",
    "evidence_ref",
    "evidence_strength",
    "impact",
    "reach",
    "effort",
    "risk",
    "reversibility",
    "expected_state",
    "acceptance_check",
}


class ActionError(ValueError):
    pass


def load_actions(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActionError(f"cannot read valid JSON from {path}: {exc}") from exc
    if isinstance(payload, list):
        actions = payload
        metadata: dict[str, Any] = {}
    elif isinstance(payload, dict) and isinstance(payload.get("actions"), list):
        actions = payload["actions"]
        metadata = {key: value for key, value in payload.items() if key != "actions"}
    else:
        raise ActionError("input must be a list or an object with actions[]")
    validate_actions(actions)
    return actions, metadata


def _number(item: dict[str, Any], field: str, index: int) -> float:
    value = item[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActionError(f"actions[{index}].{field} must be numeric")
    return float(value)


def validate_actions(actions: Any) -> None:
    if not isinstance(actions, list) or not actions:
        raise ActionError("actions must be a non-empty list")
    seen: set[str] = set()
    for index, item in enumerate(actions):
        if not isinstance(item, dict):
            raise ActionError(f"actions[{index}] must be an object")
        missing = sorted(REQUIRED_FIELDS - item.keys())
        if missing:
            raise ActionError(f"actions[{index}] missing fields: {', '.join(missing)}")
        for field in {
            "action_id",
            "observed_gap",
            "evidence_ref",
            "expected_state",
            "acceptance_check",
        }:
            if not isinstance(item[field], str) or not item[field].strip():
                raise ActionError(f"actions[{index}].{field} must be non-empty text")
        if item["action_id"] in seen:
            raise ActionError(f"duplicate action_id: {item['action_id']}")
        seen.add(item["action_id"])
        if item["priority_class"] not in PRIORITY_ORDER:
            raise ActionError(f"actions[{index}].priority_class must be P0, P1, P2, or P3")
        if item["limiting_layer"] not in LAYER_ORDER:
            raise ActionError(
                f"actions[{index}].limiting_layer must be one of {sorted(LAYER_ORDER)}"
            )
        evidence_strength = _number(item, "evidence_strength", index)
        if not 0 <= evidence_strength <= 1:
            raise ActionError(f"actions[{index}].evidence_strength must be 0..1")
        for field in ("impact", "reach", "effort", "risk", "reversibility"):
            value = _number(item, field, index)
            if not 1 <= value <= 5:
                raise ActionError(f"actions[{index}].{field} must be 1..5")


def sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        PRIORITY_ORDER[item["priority_class"]],
        LAYER_ORDER[item["limiting_layer"]],
        -float(item["evidence_strength"]),
        -(float(item["impact"]) * float(item["reach"])),
        float(item["effort"]) + float(item["risk"]),
        -float(item["reversibility"]),
        item["action_id"],
    )


def build_queue(actions: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted(actions, key=sort_key)
    queue = []
    for position, item in enumerate(ordered, start=1):
        row = dict(item)
        row["position"] = position
        row["ordering_basis"] = {
            "priority_class_rank": PRIORITY_ORDER[item["priority_class"]],
            "limiting_layer_rank": LAYER_ORDER[item["limiting_layer"]],
            "evidence_strength": item["evidence_strength"],
            "impact_x_reach": item["impact"] * item["reach"],
            "effort_plus_risk": item["effort"] + item["risk"],
            "reversibility": item["reversibility"],
        }
        queue.append(row)
    return {
        "schema_version": "1.1.0",
        "claim_boundary": "Planning order only; not evidence of ranking or recommendation impact.",
        "metadata": metadata,
        "action_count": len(queue),
        "queue": queue,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a constraint-first GEO action queue.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        actions, metadata = load_actions(args.input)
        result = build_queue(actions, metadata)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except ActionError as exc:
        print(f"action error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
