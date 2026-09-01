#!/usr/bin/env python3
"""Run dependency-free structural and public-release checks."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "OWNERSHIP.md",
    "PROVENANCE.md",
    "ORIGIN.json",
    "THIRD_PARTY_NOTICES.md",
    "TRADEMARKS.md",
    "VERSION",
    "agents/openai.yaml",
    "references/evidence-contract.md",
    "references/action-model.md",
    "references/data-interoperability.md",
    "references/methodology-and-ip.md",
    "references/multilingual-diagnostics.md",
    "schemas/evidence-bundle.schema.json",
    "schemas/action-bundle.schema.json",
    "schemas/outcome-claim.schema.json",
    "scripts/geo_outcome_scorecard.py",
    "scripts/geo_delta_compare.py",
    "scripts/geo_action_prioritizer.py",
    "scripts/geo_csv_import.py",
    "scripts/geo_privacy_export.py",
    "scripts/geo_claim_gate.py",
    "examples/outcome-claims-sample.json",
    "evals/trigger-cases.json",
    "evals/outcome-cases.json",
]
FORBIDDEN_SUFFIXES = {".env", ".pem", ".key", ".p12", ".pfx"}
FORBIDDEN_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aliyun_key": re.compile(r"\bLTAI[0-9A-Za-z]{12,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "private_path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "internal_domain": re.compile(r"\b(?:[a-z0-9-]+\.)*bcmsj\.com\b", re.I),
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}", failures)

    origin_path = ROOT / "ORIGIN.json"
    if origin_path.exists():
        try:
            origin = json.loads(origin_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid ORIGIN.json: {exc}", failures)
        else:
            if origin.get("project") != "bcm-geo-optimizer":
                fail("ORIGIN.json project mismatch", failures)
            if origin.get("steward") != "南昌包参谋品牌策划有限公司":
                fail("ORIGIN.json steward mismatch", failures)
            if origin.get("first_party_license") != "MIT":
                fail("ORIGIN.json license mismatch", failures)
            if origin.get("external_code_imports") != []:
                fail("ORIGIN.json external_code_imports must be an explicit empty array", failures)
            for reference in origin.get("conceptual_references", []):
                if reference.get("code_imported") is not False:
                    fail("conceptual reference must state code_imported=false", failures)
                if not re.fullmatch(r"[a-f0-9]{40}", str(reference.get("commit", ""))):
                    fail("conceptual reference must use a fixed 40-character commit", failures)

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else ""
    skill_path = ROOT / "SKILL.md"
    if skill_path.exists():
        frontmatter = parse_frontmatter(skill_path.read_text(encoding="utf-8"))
        if frontmatter.get("name") != "bcm-geo-optimizer":
            fail("SKILL.md name must be bcm-geo-optimizer", failures)
        if not frontmatter.get("description"):
            fail("SKILL.md description is required", failures)
        if "南昌包参谋品牌策划有限公司" not in skill_path.read_text(encoding="utf-8"):
            fail("SKILL.md must identify the BCM legal steward", failures)
        metadata_version = re.search(
            r"^\s{2}version:\s*([^\s]+)\s*$",
            skill_path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if not metadata_version or metadata_version.group(1) != version:
            fail("SKILL.md metadata version must match VERSION", failures)

    for relative in ("evals/trigger-cases.json", "evals/outcome-cases.json"):
        path = ROOT / relative
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                fail(f"invalid JSON {relative}: {exc}", failures)
                continue
            if payload.get("version") != version:
                fail(f"{relative} version must match VERSION", failures)

    for relative in (
        "schemas/evidence-bundle.schema.json",
        "schemas/action-bundle.schema.json",
        "schemas/outcome-claim.schema.json",
    ):
        path = ROOT / relative
        if not path.exists():
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON Schema {relative}: {exc}", failures)
            continue
        schema_version = (
            schema.get("properties", {}).get("schema_version", {}).get("const")
        )
        if schema_version != version:
            fail(f"{relative} schema_version const must match VERSION", failures)

    try:
        from geo_action_prioritizer import load_actions
        from geo_outcome_scorecard import load_bundle
        from geo_claim_gate import load_claims

        for relative in (
            "examples/evidence-baseline.json",
            "examples/evidence-retest.json",
            "examples/evidence-sample.json",
        ):
            load_bundle(ROOT / relative)
        load_actions(ROOT / "examples/actions-sample.json")
        load_claims(ROOT / "examples/outcome-claims-sample.json")
    except (ImportError, ValueError, OSError) as exc:
        fail(f"example validation failed: {exc}", failures)

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.is_symlink():
            try:
                path.resolve(strict=True).relative_to(ROOT.resolve())
            except (OSError, ValueError):
                fail(f"symlink escapes package root: {path.relative_to(ROOT)}", failures)
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            fail(f"forbidden sensitive file type: {path.relative_to(ROOT)}", failures)
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "VERSION"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                fail(f"{label} pattern in {path.relative_to(ROOT)}", failures)

    local_modules = {path.stem for path in (ROOT / "scripts").glob("*.py")}
    allowed_runtime = set(sys.stdlib_module_names) | local_modules
    for path in (ROOT / "scripts").glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            fail(f"invalid Python syntax in {path.relative_to(ROOT)}: {exc}", failures)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".", 1)[0]]
            else:
                continue
            for name in names:
                if name not in allowed_runtime:
                    fail(f"undeclared non-stdlib import {name} in {path.relative_to(ROOT)}", failures)

    if failures:
        for message in failures:
            print(f"FAIL: {message}", file=sys.stderr)
        return 1

    print(f"PASS: {len(REQUIRED)} required files, version {version}, public-release scan clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
