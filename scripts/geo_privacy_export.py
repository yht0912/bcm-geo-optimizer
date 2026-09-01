#!/usr/bin/env python3
"""Create a deterministic, de-identified GEO evidence export.

This is risk reduction, not a guarantee of anonymity. The HMAC salt must be
kept outside source control and reused only when stable cross-run matching is
needed.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

from geo_outcome_scorecard import EvidenceError, load_bundle, validate_observations


SCHEMA_VERSION = "1.1.0"
DEFAULT_SALT_ENV = "GEO_ANONYMIZATION_SALT"


class PrivacyExportError(ValueError):
    pass


def read_salt(env_name: str) -> bytes:
    value = os.environ.get(env_name, "")
    if len(value.encode("utf-8")) < 16:
        raise PrivacyExportError(
            f"environment variable {env_name} must contain at least 16 UTF-8 bytes"
        )
    return value.encode("utf-8")


def token(salt: bytes, namespace: str, value: str, length: int = 16) -> str:
    message = f"{namespace}\x00{value}".encode("utf-8")
    return hmac.new(salt, message, hashlib.sha256).hexdigest()[:length]


def generalized_time(value: str, granularity: str) -> str:
    if granularity == "exact":
        return value
    if granularity == "day":
        return f"{value[:10]}T00:00:00Z"
    if granularity == "month":
        return f"{value[:7]}-01T00:00:00Z"
    return "1970-01-01T00:00:00Z"


def privacy_observation(
    row: dict[str, Any], salt: bytes, time_granularity: str
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "observation_id": f"observation-{token(salt, 'observation', row['observation_id'])}",
        "panel_version": f"panel-{token(salt, 'panel', row['panel_version'])}",
        "prompt_id": f"prompt-{token(salt, 'prompt', row['prompt_id'])}",
        "prompt_hash": row["prompt_hash"],
        "provider": row["provider"],
        "model": row["model"],
        "locale": row["locale"],
        "region": row["region"],
        "observed_at": generalized_time(row["observed_at"], time_granularity),
        "status": row["status"],
        "brand": f"brand-{token(salt, 'brand', row['brand'])}",
        "source_urls": [
            f"https://source-{token(salt, 'source-url', url)}.invalid/"
            for url in row["source_urls"]
        ],
        "evidence_excerpt": (
            f"[redacted:{token(salt, 'evidence-excerpt', row['evidence_excerpt'])}]"
        ),
        "limitations": "Content removed by privacy export; review residual re-identification risk before sharing.",
    }
    if row.get("capture_ref"):
        output["capture_ref"] = (
            f"capture-{token(salt, 'capture-ref', row['capture_ref'])}"
        )
    return output


def build_privacy_bundle(
    observations: list[dict[str, Any]],
    salt: bytes,
    time_granularity: str,
    study_id: str,
) -> dict[str, Any]:
    transformed = [
        privacy_observation(row, salt, time_granularity) for row in observations
    ]
    validate_observations(transformed)
    return {
        "schema_version": SCHEMA_VERSION,
        "study_id": f"study-{token(salt, 'study', study_id)}",
        "purpose": "De-identified evidence export for review or reproducible analysis.",
        "source_format": "privacy-export",
        "anonymization": {
            "method": "hmac-sha256-v1",
            "salt_fingerprint": hashlib.sha256(salt).hexdigest()[:12],
            "time_granularity": time_granularity,
            "warning": "Risk-reduction export only; not a guarantee of anonymity.",
        },
        "observations": transformed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a deterministic, de-identified GEO evidence export."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--salt-env", default=DEFAULT_SALT_ENV)
    parser.add_argument(
        "--time-granularity",
        choices=("exact", "day", "month", "none"),
        default="day",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        salt = read_salt(args.salt_env)
        observations, metadata = load_bundle(args.input)
        study_id = str(metadata.get("study_id") or "unspecified-study")
        result = build_privacy_bundle(
            observations, salt, args.time_granularity, study_id
        )
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (EvidenceError, PrivacyExportError) as exc:
        print(f"privacy export error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
