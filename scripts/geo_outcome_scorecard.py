#!/usr/bin/env python3
"""Validate and aggregate observed AI recommendation evidence.

This tool is intentionally offline and deterministic. It never browses, creates
evidence, or infers provider behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


SCHEMA_VERSION = "1.1.0"
SUPPORTED_INPUT_SCHEMA_VERSIONS = {"1.0", "1.0.0", "1.1.0"}
ALLOWED_STATUSES = {
    "unavailable",
    "not_mentioned",
    "mentioned",
    "cited",
    "recommended",
    "negative",
}
REQUIRED_FIELDS = {
    "observation_id",
    "panel_version",
    "prompt_id",
    "prompt_hash",
    "provider",
    "model",
    "locale",
    "region",
    "observed_at",
    "status",
    "brand",
    "source_urls",
    "evidence_excerpt",
    "limitations",
}
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
ISO_8601 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class EvidenceError(ValueError):
    """Raised when the evidence bundle violates the contract."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_bundle(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read valid JSON from {path}: {exc}") from exc

    if isinstance(raw, list):
        observations = raw
        metadata: dict[str, Any] = {}
    elif isinstance(raw, dict) and isinstance(raw.get("observations"), list):
        observations = raw["observations"]
        metadata = {key: value for key, value in raw.items() if key != "observations"}
    else:
        raise EvidenceError("input must be a JSON list or an object with observations[]")

    declared_version = metadata.get("schema_version")
    if declared_version is not None and declared_version not in SUPPORTED_INPUT_SCHEMA_VERSIONS:
        raise EvidenceError(
            f"unsupported schema_version {declared_version!r}; supported: "
            + ", ".join(sorted(SUPPORTED_INPUT_SCHEMA_VERSIONS))
        )
    validate_observations(observations)
    return observations, metadata


def _require_text(item: dict[str, Any], field: str, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"observations[{index}].{field} must be non-empty text")
    return value.strip()


def _valid_public_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_observations(observations: Any) -> None:
    if not isinstance(observations, list) or not observations:
        raise EvidenceError("observations must be a non-empty list")

    seen_ids: set[str] = set()
    for index, item in enumerate(observations):
        if not isinstance(item, dict):
            raise EvidenceError(f"observations[{index}] must be an object")
        missing = sorted(REQUIRED_FIELDS - item.keys())
        if missing:
            raise EvidenceError(
                f"observations[{index}] missing fields: {', '.join(missing)}"
            )

        for field in REQUIRED_FIELDS - {"source_urls"}:
            _require_text(item, field, index)

        observation_id = item["observation_id"].strip()
        if observation_id in seen_ids:
            raise EvidenceError(f"duplicate observation_id: {observation_id}")
        seen_ids.add(observation_id)

        status = item["status"].strip()
        if status not in ALLOWED_STATUSES:
            raise EvidenceError(
                f"observations[{index}].status must be one of {sorted(ALLOWED_STATUSES)}"
            )

        prompt_hash = item["prompt_hash"].strip().lower()
        if not HEX_64.fullmatch(prompt_hash):
            raise EvidenceError(
                f"observations[{index}].prompt_hash must be lowercase SHA-256"
            )

        if not ISO_8601.fullmatch(item["observed_at"].strip()):
            raise EvidenceError(
                f"observations[{index}].observed_at must include ISO 8601 timezone"
            )

        urls = item["source_urls"]
        if not isinstance(urls, list) or not all(isinstance(url, str) for url in urls):
            raise EvidenceError(f"observations[{index}].source_urls must be a string list")
        invalid_urls = [url for url in urls if not _valid_public_url(url)]
        if invalid_urls:
            raise EvidenceError(
                f"observations[{index}] contains invalid public URL: {invalid_urls[0]}"
            )
        if status == "cited" and not urls:
            raise EvidenceError(f"observations[{index}] is cited but source_urls is empty")


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float | None]:
    if total == 0:
        return [None, None]
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return [round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)]


def _rate(successes: int, total: int) -> dict[str, Any]:
    return {
        "count": successes,
        "n": total,
        "rate": round(successes / total, 4) if total else None,
        "wilson_95": wilson_interval(successes, total),
    }


def aggregate(observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(observations)
    counts = Counter(row["status"] for row in rows)
    valid = [row for row in rows if row["status"] != "unavailable"]
    cited_count = sum(bool(row["source_urls"]) for row in valid)
    mentioned_count = sum(
        row["status"] in {"mentioned", "cited", "recommended", "negative"}
        for row in valid
    )
    recommended_count = sum(row["status"] == "recommended" for row in valid)
    negative_count = sum(row["status"] == "negative" for row in valid)

    if recommended_count:
        highest_observed_state = "recommended"
    elif cited_count:
        highest_observed_state = "cited"
    elif mentioned_count:
        highest_observed_state = "mentioned"
    elif valid:
        highest_observed_state = "observed_not_mentioned"
    else:
        highest_observed_state = "unavailable"

    return {
        "total_observations": len(rows),
        "valid_observations": len(valid),
        "unavailable_observations": counts["unavailable"],
        "coverage_rate": round(len(valid) / len(rows), 4) if rows else None,
        "status_counts": {key: counts[key] for key in sorted(ALLOWED_STATUSES)},
        "mention": _rate(mentioned_count, len(valid)),
        "citation": _rate(cited_count, len(valid)),
        "recommendation": _rate(recommended_count, len(valid)),
        "negative": _rate(negative_count, len(valid)),
        "highest_observed_state": highest_observed_state,
    }


def build_scorecard(
    observations: list[dict[str, Any]], metadata: dict[str, Any]
) -> dict[str, Any]:
    groups: dict[str, dict[str, list[dict[str, Any]]]] = {
        "provider": defaultdict(list),
        "locale": defaultdict(list),
        "region": defaultdict(list),
    }
    for row in observations:
        for dimension in groups:
            groups[dimension][row[dimension]].append(row)

    panel_versions = sorted({row["panel_version"] for row in observations})
    warnings: list[str] = []
    if len(panel_versions) > 1:
        warnings.append("multiple_panel_versions_present")
    if len(observations) < 20:
        warnings.append("small_sample_directional_only")
    if any(row["status"] == "unavailable" for row in observations):
        warnings.append("unavailable_observations_preserved")

    return {
        "schema_version": SCHEMA_VERSION,
        "claim_boundary": "Observed aggregation only; no causal or platform-wide claim.",
        "input_sha256": sha256_json(observations),
        "bundle_metadata": metadata,
        "panel_versions": panel_versions,
        "warnings": warnings,
        "overall": aggregate(observations),
        "groups": {
            dimension: {
                key: aggregate(rows) for key, rows in sorted(group_values.items())
            }
            for dimension, group_values in groups.items()
        },
    }


def write_json(value: Any, output: Path | None) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and aggregate observed GEO outcome evidence."
    )
    parser.add_argument("--input", required=True, type=Path, help="Evidence JSON")
    parser.add_argument("--output", type=Path, help="Output JSON; stdout if omitted")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        observations, metadata = load_bundle(args.input)
        write_json(build_scorecard(observations, metadata), args.output)
    except EvidenceError as exc:
        print(f"evidence error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
