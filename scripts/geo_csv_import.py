#!/usr/bin/env python3
"""Convert a strict CSV observation export into a validated evidence bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from geo_outcome_scorecard import EvidenceError, validate_observations


SCHEMA_VERSION = "1.1.0"
REQUIRED_COLUMNS = [
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
]
OPTIONAL_COLUMNS = ["capture_ref"]
ALLOWED_COLUMNS = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)


class CsvImportError(ValueError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_source_urls(raw: str) -> list[str]:
    if not raw.strip():
        return []
    urls = [value.strip() for value in raw.split("|") if value.strip()]
    if len(urls) != len(set(urls)):
        raise CsvImportError("source_urls contains duplicate values")
    return urls


def load_csv(path: Path) -> list[dict[str, Any]]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise CsvImportError(f"cannot open {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CsvImportError("CSV header is missing")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise CsvImportError("CSV header contains duplicate columns")
        missing = [field for field in REQUIRED_COLUMNS if field not in reader.fieldnames]
        extras = [field for field in reader.fieldnames if field not in ALLOWED_COLUMNS]
        if missing:
            raise CsvImportError(f"missing required columns: {', '.join(missing)}")
        if extras:
            raise CsvImportError(
                "unrecognized columns are rejected to prevent accidental disclosure: "
                + ", ".join(extras)
            )

        observations: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise CsvImportError(f"line {line_number} has more values than headers")
            if not any((value or "").strip() for value in row.values()):
                continue
            item: dict[str, Any] = {
                field: (row.get(field) or "").strip() for field in REQUIRED_COLUMNS
            }
            item["source_urls"] = parse_source_urls(item["source_urls"])
            capture_ref = (row.get("capture_ref") or "").strip()
            if capture_ref:
                item["capture_ref"] = capture_ref
            observations.append(item)

    try:
        validate_observations(observations)
    except EvidenceError as exc:
        raise CsvImportError(str(exc)) from exc
    return observations


def build_bundle(
    path: Path, observations: list[dict[str, Any]], study_id: str, purpose: str
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "purpose": purpose,
        "source_format": "csv",
        "input_sha256": file_sha256(path),
        "observations": observations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert strict UTF-8 CSV observations to a validated GEO evidence bundle."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--purpose", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.study_id.strip() or not args.purpose.strip():
            raise CsvImportError("--study-id and --purpose must be non-empty")
        observations = load_csv(args.input)
        result = build_bundle(
            args.input, observations, args.study_id.strip(), args.purpose.strip()
        )
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except CsvImportError as exc:
        print(f"CSV import error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
