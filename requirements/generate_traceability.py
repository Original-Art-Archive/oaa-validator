from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "requirements" / "traceability.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validator.oaa_validator.rules import rule_map


def load_catalog() -> dict:
    with (ROOT / "requirements" / "oaa-0.1.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_fixtures() -> list[dict]:
    fixtures: list[dict] = []
    for path in [
        ROOT / "validator" / "fixtures" / "valid" / "examples.json",
        ROOT / "validator" / "fixtures" / "invalid" / "cases.json",
    ]:
        with path.open("r", encoding="utf-8") as handle:
            fixtures.extend(json.load(handle)["fixtures"])
    return fixtures


def fixture_index(fixtures: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for fixture in fixtures:
        for req_id in fixture.get("covers_requirements", []):
            index.setdefault(req_id, []).append(fixture["id"])
        for finding in fixture.get("expected_findings", []):
            for req_id in finding["requirement_ids"]:
                index.setdefault(req_id, []).append(fixture["id"])
    return index


def render() -> str:
    catalog = load_catalog()
    rules = rule_map()
    fixtures = fixture_index(load_fixtures())
    lines = [
        "<!-- SPDX-License-Identifier: CC-BY-4.0 -->",
        "",
        "# OAA 0.1 Traceability Matrix",
        "",
        "Generated from `requirements/oaa-0.1.yaml`, validator rule metadata, and fixture metadata.",
        "",
        "| Requirement | Level | Coverage | Spec Section | Validator Rule | Severity | Fixtures |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for req in catalog["requirements"]:
        validation = req["validation"]
        rule_ids = validation.get("rule_ids", [])
        rule_text = "<br>".join(rule_ids) if rule_ids else ""
        severity = validation.get("severity", "")
        fixture_text = "<br>".join(sorted(set(fixtures.get(req["id"], []))))
        missing_rules = [rule_id for rule_id in rule_ids if rule_id not in rules]
        if missing_rules:
            rule_text += "<br>UNKNOWN: " + ", ".join(missing_rules)
        lines.append(
            "| {id} | {level} | {coverage} | {section} | {rules} | {severity} | {fixtures} |".format(
                id=req["id"],
                level=req["level"],
                coverage=validation["coverage"],
                section=req["source"]["section"],
                rules=rule_text,
                severity=severity,
                fixtures=fixture_text,
            )
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    content = render()
    if args.check:
        if not OUTPUT.exists():
            print(f"{OUTPUT} does not exist")
            return 1
        current = OUTPUT.read_text(encoding="utf-8")
        if current != content:
            print(f"{OUTPUT} is not current")
            return 1
        return 0
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
