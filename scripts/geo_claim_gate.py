#!/usr/bin/env python3
"""Validate evidence-linked GEO claims without inventing causality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.2.0"
METHOD_ID = "bcm-geo-evidence-action-retest"
CLAIM_TYPES = {
    "implementation",
    "search_outcome",
    "ai_outcome",
    "observed_change",
    "causal_estimate",
}
OUTCOME_STATES = {
    "reachable",
    "discovered",
    "crawled",
    "indexed",
    "ranked",
    "mentioned",
    "cited",
    "recommended",
    "converted",
}
STATUSES = {"substantiated", "qualified", "insufficient"}
CAUSAL_DESIGNS = {
    "randomized_controlled",
    "quasi_experimental",
    "interrupted_time_series",
}


class ClaimError(ValueError):
    pass


def _text(value: Any, field: str, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClaimError(f"claims[{index}].{field} must be non-empty text")
    return value.strip()


def load_claims(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClaimError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("claims"), list):
        raise ClaimError("input must be an object with claims[]")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ClaimError(f"schema_version must be {SCHEMA_VERSION}")
    method = payload.get("methodology")
    if not isinstance(method, dict) or method.get("id") != METHOD_ID:
        raise ClaimError(f"methodology.id must be {METHOD_ID}")
    _text(method.get("version"), "methodology.version", -1)
    validate_claims(payload["claims"])
    return payload["claims"], {key: value for key, value in payload.items() if key != "claims"}


def validate_claims(claims: Any) -> None:
    if not isinstance(claims, list) or not claims:
        raise ClaimError("claims must be a non-empty list")
    seen: set[str] = set()
    required = {
        "claim_id",
        "claim_type",
        "statement",
        "highest_verified_state",
        "evidence_refs",
        "confidence",
        "status",
        "limitations",
    }
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise ClaimError(f"claims[{index}] must be an object")
        missing = sorted(required - claim.keys())
        if missing:
            raise ClaimError(f"claims[{index}] missing fields: {', '.join(missing)}")
        claim_id = _text(claim["claim_id"], "claim_id", index)
        if claim_id in seen:
            raise ClaimError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        _text(claim["statement"], "statement", index)
        if claim["claim_type"] not in CLAIM_TYPES:
            raise ClaimError(f"claims[{index}].claim_type is unsupported")
        if claim["highest_verified_state"] not in OUTCOME_STATES:
            raise ClaimError(f"claims[{index}].highest_verified_state is unsupported")
        if claim["status"] not in STATUSES:
            raise ClaimError(f"claims[{index}].status is unsupported")
        confidence = claim["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ClaimError(f"claims[{index}].confidence must be 0..1")
        for field in ("evidence_refs", "limitations"):
            values = claim[field]
            if not isinstance(values, list) or not values:
                raise ClaimError(f"claims[{index}].{field} must be a non-empty list")
            for value in values:
                _text(value, field, index)


def _comparison_reasons(claim: dict[str, Any]) -> list[str]:
    comparison = claim.get("comparison")
    if not isinstance(comparison, dict):
        return ["comparison_required"]
    reasons: list[str] = []
    for field in ("baseline_study_id", "retest_study_id"):
        if not isinstance(comparison.get(field), str) or not comparison[field].strip():
            reasons.append(f"{field}_required")
    matched_pairs = comparison.get("matched_pairs")
    coverage = comparison.get("matched_coverage")
    if not isinstance(matched_pairs, int) or isinstance(matched_pairs, bool) or matched_pairs < 1:
        reasons.append("matched_pairs_must_be_positive")
    if isinstance(coverage, bool) or not isinstance(coverage, (int, float)) or not 0 < coverage <= 1:
        reasons.append("matched_coverage_must_be_positive")
    return reasons


def gate_claim(claim: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    claim_type = claim["claim_type"]
    if claim_type == "implementation" and claim["highest_verified_state"] not in {"reachable", "discovered", "crawled"}:
        reasons.append("implementation_claim_exceeds_implementation_evidence")
    if claim_type in {"observed_change", "causal_estimate"}:
        reasons.extend(_comparison_reasons(claim))
    if claim_type == "causal_estimate":
        design = claim.get("causal_design")
        if not isinstance(design, dict):
            reasons.append("causal_design_required")
        else:
            if design.get("design_type") not in CAUSAL_DESIGNS:
                reasons.append("supported_causal_design_required")
            if not isinstance(design.get("control_reference"), str) or not design["control_reference"].strip():
                reasons.append("control_reference_required")
            assumptions = design.get("assumptions")
            if not isinstance(assumptions, list) or not assumptions:
                reasons.append("causal_assumptions_required")
    if claim["status"] == "substantiated" and claim["confidence"] < 0.8:
        reasons.append("substantiated_claim_confidence_below_0_8")

    if reasons:
        decision = "rejected"
    elif claim["status"] == "qualified" or claim["confidence"] < 0.8:
        decision = "qualified"
    else:
        decision = "pass"
    return {"claim_id": claim["claim_id"], "decision": decision, "reasons": reasons}


def build_result(claims: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    decisions = [gate_claim(claim) for claim in claims]
    counts = {state: sum(item["decision"] == state for item in decisions) for state in ("pass", "qualified", "rejected")}
    return {
        "schema_version": SCHEMA_VERSION,
        "methodology": metadata["methodology"],
        "gate_status": "rejected" if counts["rejected"] else ("qualified" if counts["qualified"] else "pass"),
        "counts": counts,
        "decisions": decisions,
        "claim_boundary": "A passed structural gate preserves evidence discipline; it does not independently prove the underlying claim.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate evidence-linked GEO claims.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Return exit code 2 when any claim is rejected.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        claims, metadata = load_claims(args.input)
        result = build_result(claims, metadata)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        if args.strict and result["gate_status"] == "rejected":
            return 2
    except ClaimError as exc:
        print(f"claim error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
