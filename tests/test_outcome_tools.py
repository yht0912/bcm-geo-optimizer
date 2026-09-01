from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from geo_delta_compare import compare  # noqa: E402
from geo_action_prioritizer import ActionError, build_queue, load_actions  # noqa: E402
from geo_csv_import import CsvImportError, build_bundle as build_csv_bundle, load_csv  # noqa: E402
from geo_privacy_export import (  # noqa: E402
    PrivacyExportError,
    build_privacy_bundle,
    read_salt,
)
from geo_outcome_scorecard import (  # noqa: E402
    EvidenceError,
    build_scorecard,
    load_bundle,
    validate_observations,
)


class OutcomeScorecardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline, _ = load_bundle(ROOT / "examples" / "evidence-baseline.json")
        cls.retest, _ = load_bundle(ROOT / "examples" / "evidence-retest.json")

    def test_scorecard_preserves_unavailable_and_uses_valid_denominator(self) -> None:
        result = build_scorecard(self.baseline, {"study_id": "test"})
        self.assertEqual(result["overall"]["total_observations"], 6)
        self.assertEqual(result["overall"]["valid_observations"], 5)
        self.assertEqual(result["overall"]["unavailable_observations"], 1)
        self.assertEqual(result["overall"]["citation"]["count"], 1)
        self.assertEqual(result["overall"]["highest_observed_state"], "cited")

    def test_cited_observation_requires_source_url(self) -> None:
        rows = copy.deepcopy(self.baseline)
        rows[3]["source_urls"] = []
        with self.assertRaisesRegex(EvidenceError, "source_urls is empty"):
            validate_observations(rows)

    def test_duplicate_observation_id_is_rejected(self) -> None:
        rows = copy.deepcopy(self.baseline)
        rows[1]["observation_id"] = rows[0]["observation_id"]
        with self.assertRaisesRegex(EvidenceError, "duplicate observation_id"):
            validate_observations(rows)

    def test_invalid_bundle_shape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps({"items": []}), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "observations"):
                load_bundle(path)

    def test_matched_delta_is_directional_and_valid(self) -> None:
        result = compare(self.baseline, self.retest, 0.8)
        self.assertEqual(result["comparison_status"], "valid_directional_comparison")
        self.assertEqual(result["coverage"]["both_valid_pairs"], 5)
        self.assertEqual(
            result["metrics"]["recommendation"]["delta_percentage_points"], 40.0
        )
        self.assertIn("no causal attribution", result["claim_boundary"])

    def test_prompt_hash_mismatch_is_excluded(self) -> None:
        retest = copy.deepcopy(self.retest)
        retest[0]["prompt_hash"] = "f" * 64
        result = compare(self.baseline, retest, 0.8)
        self.assertEqual(result["coverage"]["prompt_hash_mismatches"], 1)
        self.assertIn("prompt_hash_mismatch_excluded", result["warnings"])
        self.assertEqual(result["comparison_status"], "insufficient_matched_coverage")

    def test_constraint_first_queue_puts_p0_before_p1_and_p3(self) -> None:
        actions, metadata = load_actions(ROOT / "examples" / "actions-sample.json")
        result = build_queue(actions, metadata)
        self.assertEqual(
            [item["action_id"] for item in result["queue"]],
            ["repair-canonical", "add-proof-unit", "test-machine-helper"],
        )
        self.assertIn("not evidence", result["claim_boundary"])

    def test_action_dimensions_are_bounded(self) -> None:
        actions, _ = load_actions(ROOT / "examples" / "actions-sample.json")
        actions[0]["impact"] = 6
        from geo_action_prioritizer import validate_actions

        with self.assertRaisesRegex(ActionError, "impact must be 1..5"):
            validate_actions(actions)

    def test_csv_import_matches_json_sample(self) -> None:
        imported = load_csv(ROOT / "examples" / "evidence-sample.csv")
        expected, _ = load_bundle(ROOT / "examples" / "evidence-sample.json")
        self.assertEqual(imported, expected)
        bundle = build_csv_bundle(
            ROOT / "examples" / "evidence-sample.csv",
            imported,
            "example-study",
            "Synthetic import check",
        )
        self.assertEqual(bundle["schema_version"], "1.1.0")
        self.assertEqual(len(bundle["input_sha256"]), 64)

    def test_csv_import_rejects_unknown_columns(self) -> None:
        source = (ROOT / "examples" / "evidence-sample.csv").read_text(
            encoding="utf-8"
        )
        lines = source.splitlines()
        lines[0] += ",private_note"
        lines[1] += ",must-not-leak"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.csv"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CsvImportError, "accidental disclosure"):
                load_csv(path)

    def test_privacy_export_is_deterministic_and_removes_identifiers(self) -> None:
        salt = b"0123456789abcdef-test-salt"
        first = build_privacy_bundle(
            self.retest, salt, "day", "private-study-name"
        )
        second = build_privacy_bundle(
            self.retest, salt, "day", "private-study-name"
        )
        self.assertEqual(first, second)
        rendered = json.dumps(first, ensure_ascii=False)
        self.assertNotIn("Example Brand", rendered)
        self.assertNotIn("example.com", rendered)
        self.assertNotIn("private-study-name", rendered)
        self.assertTrue(first["observations"][0]["source_urls"][0].endswith(".invalid/"))
        self.assertEqual(
            first["observations"][0]["observed_at"], "2026-09-01T00:00:00Z"
        )
        validate_observations(first["observations"])

    def test_privacy_export_requires_a_long_salt(self) -> None:
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"TEST_GEO_SALT": "short"}, clear=False):
            with self.assertRaisesRegex(PrivacyExportError, "at least 16"):
                read_salt("TEST_GEO_SALT")

    def test_json_schema_versions_match_package(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        for name in ("evidence-bundle.schema.json", "action-bundle.schema.json"):
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(schema["properties"]["schema_version"]["const"], version)

    def test_unsupported_evidence_schema_is_rejected(self) -> None:
        payload = json.loads(
            (ROOT / "examples" / "evidence-sample.json").read_text(encoding="utf-8")
        )
        payload["schema_version"] = "9.9.9"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "future.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(EvidenceError, "unsupported schema_version"):
                load_bundle(path)


if __name__ == "__main__":
    unittest.main()
