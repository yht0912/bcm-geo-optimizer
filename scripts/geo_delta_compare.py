#!/usr/bin/env python3
"""Compare matched baseline and retest GEO observations without claiming causality."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from geo_outcome_scorecard import EvidenceError, aggregate, load_bundle, sha256_json


MATCH_FIELDS = ("prompt_id", "provider", "locale", "region")


def observation_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(row[field] for field in MATCH_FIELDS)


def index_unique(
    rows: list[dict[str, Any]], label: str
) -> dict[tuple[str, ...], dict[str, Any]]:
    indexed: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = observation_key(row)
        if key in indexed:
            printable = " | ".join(key)
            raise EvidenceError(f"duplicate {label} comparison key: {printable}")
        indexed[key] = row
    return indexed


def _metric_delta(
    baseline: dict[str, Any], retest: dict[str, Any], metric: str
) -> dict[str, Any]:
    before = baseline[metric]["rate"]
    after = retest[metric]["rate"]
    delta = round((after - before) * 100, 2) if before is not None and after is not None else None
    return {
        "baseline": baseline[metric],
        "retest": retest[metric],
        "delta_percentage_points": delta,
    }


def compare(
    baseline_rows: list[dict[str, Any]],
    retest_rows: list[dict[str, Any]],
    min_coverage: float,
) -> dict[str, Any]:
    baseline_index = index_unique(baseline_rows, "baseline")
    retest_index = index_unique(retest_rows, "retest")
    union_keys = set(baseline_index) | set(retest_index)
    shared_keys = set(baseline_index) & set(retest_index)

    incompatible_prompt_keys: list[tuple[str, ...]] = []
    model_drift_keys: list[tuple[str, ...]] = []
    compatible_pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for key in sorted(shared_keys):
        before = baseline_index[key]
        after = retest_index[key]
        if before["prompt_hash"] != after["prompt_hash"]:
            incompatible_prompt_keys.append(key)
            continue
        if before["model"] != after["model"]:
            model_drift_keys.append(key)
        compatible_pairs.append((before, after))

    both_valid_pairs = [
        pair
        for pair in compatible_pairs
        if pair[0]["status"] != "unavailable" and pair[1]["status"] != "unavailable"
    ]
    matched_baseline = [pair[0] for pair in both_valid_pairs]
    matched_retest = [pair[1] for pair in both_valid_pairs]

    coverage = len(compatible_pairs) / len(union_keys) if union_keys else 0.0
    valid_coverage = len(both_valid_pairs) / len(union_keys) if union_keys else 0.0
    baseline_agg = aggregate(matched_baseline) if matched_baseline else aggregate([])
    retest_agg = aggregate(matched_retest) if matched_retest else aggregate([])
    transitions = Counter(
        f"{before['status']}->{after['status']}" for before, after in both_valid_pairs
    )

    if not compatible_pairs:
        comparison_status = "no_compatible_pairs"
    elif valid_coverage < min_coverage:
        comparison_status = "insufficient_matched_coverage"
    else:
        comparison_status = "valid_directional_comparison"

    warnings: list[str] = []
    if model_drift_keys:
        warnings.append("model_drift_present")
    if incompatible_prompt_keys:
        warnings.append("prompt_hash_mismatch_excluded")
    if len(both_valid_pairs) < 20:
        warnings.append("small_matched_sample_directional_only")

    return {
        "schema_version": "1.2.0",
        "comparison_status": comparison_status,
        "claim_boundary": "Matched observational delta only; no causal attribution.",
        "minimum_required_coverage": min_coverage,
        "baseline_input_sha256": sha256_json(baseline_rows),
        "retest_input_sha256": sha256_json(retest_rows),
        "coverage": {
            "baseline_keys": len(baseline_index),
            "retest_keys": len(retest_index),
            "union_keys": len(union_keys),
            "shared_keys": len(shared_keys),
            "compatible_prompt_pairs": len(compatible_pairs),
            "both_valid_pairs": len(both_valid_pairs),
            "matched_coverage_rate": round(coverage, 4),
            "valid_matched_coverage_rate": round(valid_coverage, 4),
            "prompt_hash_mismatches": len(incompatible_prompt_keys),
            "model_drift_pairs": len(model_drift_keys),
        },
        "warnings": warnings,
        "metrics": {
            metric: _metric_delta(baseline_agg, retest_agg, metric)
            for metric in ("mention", "citation", "recommendation", "negative")
        },
        "transitions": dict(sorted(transitions.items())),
        "unmatched_baseline_keys": [
            " | ".join(key) for key in sorted(set(baseline_index) - set(retest_index))
        ],
        "unmatched_retest_keys": [
            " | ".join(key) for key in sorted(set(retest_index) - set(baseline_index))
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare matched baseline and retest GEO evidence."
    )
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--retest", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-coverage", type=float, default=0.8)
    args = parser.parse_args()
    if not 0 <= args.min_coverage <= 1:
        parser.error("--min-coverage must be between 0 and 1")
    return args


def main() -> int:
    args = parse_args()
    try:
        baseline_rows, _ = load_bundle(args.baseline)
        retest_rows, _ = load_bundle(args.retest)
        result = compare(baseline_rows, retest_rows, args.min_coverage)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except EvidenceError as exc:
        print(f"evidence error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
