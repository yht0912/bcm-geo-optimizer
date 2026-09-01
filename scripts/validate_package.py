#!/usr/bin/env python3
"""Run dependency-free structural and public-release checks."""

from __future__ import annotations

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
    "SECURITY.md",
    "CONTRIBUTING.md",
    "VERSION",
    "agents/openai.yaml",
    "references/evidence-contract.md",
    "references/action-model.md",
    "scripts/geo_outcome_scorecard.py",
    "scripts/geo_delta_compare.py",
    "scripts/geo_action_prioritizer.py",
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

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else ""
    skill_path = ROOT / "SKILL.md"
    if skill_path.exists():
        frontmatter = parse_frontmatter(skill_path.read_text(encoding="utf-8"))
        if frontmatter.get("name") != "bcm-geo-optimizer":
            fail("SKILL.md name must be bcm-geo-optimizer", failures)
        if not frontmatter.get("description"):
            fail("SKILL.md description is required", failures)
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

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
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

    if failures:
        for message in failures:
            print(f"FAIL: {message}", file=sys.stderr)
        return 1

    print(f"PASS: {len(REQUIRED)} required files, version {version}, public-release scan clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
