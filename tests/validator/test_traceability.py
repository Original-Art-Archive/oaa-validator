import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "requirements" / "oaa-0.1.yaml"
SCHEMA = ROOT / "schema" / "oaa-manifest.schema.json"
FIXTURE_FILES = [
    ROOT / "validator" / "fixtures" / "valid" / "examples.json",
    ROOT / "validator" / "fixtures" / "invalid" / "cases.json",
]


def load_catalog():
    with CATALOG.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_schema():
    with SCHEMA.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_fixtures():
    fixtures = []
    for path in FIXTURE_FILES:
        with path.open("r", encoding="utf-8") as handle:
            fixtures.extend(json.load(handle)["fixtures"])
    return fixtures


def requirement_by_id(catalog, requirement_id):
    for requirement in catalog["requirements"]:
        if requirement["id"] == requirement_id:
            return requirement
    raise AssertionError(f"Missing requirement {requirement_id}")


class RequirementTraceabilityTests(unittest.TestCase):
    def test_requirement_catalog_schema_is_valid(self):
        catalog = load_catalog()
        self.assertEqual(catalog["format_version"], 1)
        self.assertEqual(catalog["spec_version"], "0.1")
        ids = set()
        for req in catalog["requirements"]:
            with self.subTest(req=req.get("id")):
                self.assertRegex(req["id"], r"^OAA-[A-Z]+-[0-9]{3}$")
                self.assertNotIn(req["id"], ids)
                ids.add(req["id"])
                self.assertIn(req["level"], {"MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY", "OPTIONAL"})
                self.assertIn(req["validation"]["coverage"], {"automated", "manual", "not_validator_scope"})
                if req["validation"]["coverage"] == "automated":
                    self.assertTrue(req["validation"].get("rule_ids"))
                    self.assertIn(req["validation"].get("severity"), {"fatal", "error", "warning", "info"})
                else:
                    self.assertTrue(req["validation"].get("reason"))

    def test_every_rule_references_known_requirements(self):
        catalog = load_catalog()
        known_requirement_ids = {req["id"] for req in catalog["requirements"]}
        rules = importlib.import_module("validator.oaa_validator.rules").all_rules()
        self.assertGreater(len(rules), 0)
        for rule in rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.requirement_ids)
                self.assertLessEqual(set(rule.requirement_ids), known_requirement_ids)

    def test_every_rule_references_only_automated_archive_validity_requirements(self):
        catalog = load_catalog()
        automated_ids = {
            req["id"]
            for req in catalog["requirements"]
            if req["validation"]["coverage"] == "automated"
        }
        rules = importlib.import_module("validator.oaa_validator.rules").all_rules()
        for rule in rules:
            with self.subTest(rule=rule.id):
                self.assertLessEqual(set(rule.requirement_ids), automated_ids)

    def test_every_automated_requirement_has_rule_coverage(self):
        catalog = load_catalog()
        rules = importlib.import_module("validator.oaa_validator.rules").all_rules()
        known_rule_ids = {rule.id for rule in rules}
        for req in catalog["requirements"]:
            if req["validation"]["coverage"] != "automated":
                continue
            with self.subTest(req=req["id"]):
                self.assertTrue(set(req["validation"]["rule_ids"]) & known_rule_ids)

    def test_automated_requirements_are_archive_validity_scope(self):
        catalog = load_catalog()
        excluded_types = {"reader", "writer", "round-trip", "privacy", "conformance"}
        for req in catalog["requirements"]:
            if req["validation"]["coverage"] != "automated":
                continue
            with self.subTest(req=req["id"]):
                self.assertNotIn(req["type"], excluded_types)

    def test_every_automated_requirement_has_fixture_coverage(self):
        catalog = load_catalog()
        automated_ids = {
            req["id"]
            for req in catalog["requirements"]
            if req["validation"]["coverage"] == "automated"
        }
        covered_ids = set()
        for fixture in load_fixtures():
            covered_ids.update(fixture.get("covers_requirements", []))
            for finding in fixture.get("expected_findings", []):
                covered_ids.update(finding["requirement_ids"])
        self.assertFalse(automated_ids - covered_ids)

    def test_every_automated_requirement_has_expected_finding_coverage(self):
        catalog = load_catalog()
        automated_ids = {
            req["id"]
            for req in catalog["requirements"]
            if req["validation"]["coverage"] == "automated"
        }
        covered_ids = set()
        for fixture in load_fixtures():
            for finding in fixture.get("expected_findings", []):
                covered_ids.update(finding["requirement_ids"])
        self.assertFalse(automated_ids - covered_ids)

    def test_fixture_expected_findings_reference_known_rules_and_requirements(self):
        catalog = load_catalog()
        known_requirement_ids = {req["id"] for req in catalog["requirements"]}
        rules = importlib.import_module("validator.oaa_validator.rules").all_rules()
        known_rule_ids = {rule.id for rule in rules}
        for fixture in load_fixtures():
            for finding in fixture.get("expected_findings", []):
                with self.subTest(fixture=fixture["id"], rule=finding["rule_id"]):
                    self.assertIn(finding["rule_id"], known_rule_ids)
                    self.assertTrue(set(finding["requirement_ids"]))
                    self.assertLessEqual(set(finding["requirement_ids"]), known_requirement_ids)

    def test_closed_base_value_requirements_are_fatal_and_fixture_backed(self):
        expected = {
            "OAA-PUB-002": {
                "section": "Public Artwork Metadata Object",
                "rule_id": "artwork.publication_status",
                "negative_fixture": "bad-publication-status",
                "positive_fixture": "valid-full-directory",
            },
            "OAA-FILE-018": {
                "section": "Artwork File Object",
                "rule_id": "files.file_kind",
                "negative_fixture": "bad-file-kind",
                "positive_fixture": "valid-full-directory",
            },
            "OAA-FILE-019": {
                "section": "Artwork File Object",
                "rule_id": "files.image_role",
                "negative_fixture": "bad-image-role",
                "positive_fixture": "valid-full-directory",
            },
        }
        catalog = load_catalog()
        fixtures = load_fixtures()
        fixtures_by_id = {fixture["id"]: fixture for fixture in fixtures}

        for requirement_id, expectation in expected.items():
            with self.subTest(req=requirement_id):
                requirement = requirement_by_id(catalog, requirement_id)
                self.assertEqual(requirement["source"]["section"], expectation["section"])
                self.assertEqual(requirement["validation"]["coverage"], "automated")
                self.assertEqual(requirement["validation"]["rule_ids"], [expectation["rule_id"]])
                self.assertEqual(requirement["validation"]["severity"], "fatal")

                negative_fixture = fixtures_by_id[expectation["negative_fixture"]]
                self.assertFalse(negative_fixture["expected_valid"])
                self.assertIn(
                    {
                        "rule_id": expectation["rule_id"],
                        "requirement_ids": [requirement_id],
                        "severity": "fatal",
                    },
                    negative_fixture["expected_findings"],
                )

                positive_fixture = fixtures_by_id[expectation["positive_fixture"]]
                self.assertTrue(positive_fixture["expected_valid"])
                self.assertIn(requirement_id, positive_fixture["covers_requirements"])

    def test_schema_closed_base_value_sets_match_validator_contract(self):
        schema = load_schema()
        public_metadata = schema["$defs"]["publicArtworkMetadata"]
        artwork_file = schema["$defs"]["artworkFile"]

        self.assertEqual(
            public_metadata["properties"]["publication_status"]["enum"],
            ["published_art", "unpublished_art", None],
        )
        self.assertEqual(
            artwork_file["properties"]["file_kind"]["enum"],
            ["raw", "derivative", "supporting"],
        )
        self.assertEqual(
            artwork_file["properties"]["image_role"]["enum"],
            ["raw_scan", "raw_photo", "corrected_scan", "detail", "verso", "reference", None],
        )
        self.assertIn("file_kind", artwork_file["required"])

    def test_generated_traceability_is_current(self):
        result = subprocess.run(
            [sys.executable, "requirements/generate_traceability.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
