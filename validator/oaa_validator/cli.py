from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from .model import Limits, Severity, ValidationResult
from .validator import validate_archive, validate_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oaa-validator", description="Validate Original Art Archive (OAA) packages.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_validate_command(subparsers, "validate", validate_archive)
    add_validate_command(subparsers, "validate-dir", validate_directory)
    return parser


def add_validate_command(subparsers: argparse._SubParsersAction, name: str, func: Callable) -> None:
    parser = subparsers.add_parser(name)
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--show-info", action="store_true")
    parser.add_argument("--warnings-as-errors", action="store_true")
    parser.add_argument("--max-archive-size", type=int, default=Limits.max_archive_size)
    parser.add_argument("--max-uncompressed-size", type=int, default=Limits.max_uncompressed_size)
    parser.add_argument("--max-entries", type=int, default=Limits.max_entries)
    parser.add_argument("--max-entry-size", type=int, default=Limits.max_entry_size)
    parser.add_argument("--max-manifest-size", type=int, default=Limits.max_manifest_size)
    parser.add_argument("--max-json-depth", type=int, default=Limits.max_json_depth)
    parser.set_defaults(func=func)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    limits = Limits(
        max_archive_size=args.max_archive_size,
        max_uncompressed_size=args.max_uncompressed_size,
        max_entries=args.max_entries,
        max_entry_size=args.max_entry_size,
        max_manifest_size=args.max_manifest_size,
        max_json_depth=args.max_json_depth,
    )
    path = Path(args.path)
    if not path.exists():
        parser.error(f"input path does not exist: {path}")
    result: ValidationResult = args.func(path, limits=limits)
    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_text_result(result, show_info=args.show_info)
    return exit_code(result, warnings_as_errors=args.warnings_as_errors)


def print_text_result(result: ValidationResult, *, show_info: bool) -> None:
    print(f"Input: {result.input}")
    print(f"Mode: {result.mode}")
    print(f"Valid: {str(result.valid).lower()}")
    summary = result.summary()
    print(
        "Summary: "
        + ", ".join(f"{key}={value}" for key, value in summary.items())
    )
    for item in result.issues:
        if item.severity == Severity.INFO and not show_info:
            continue
        reqs = ",".join(item.requirement_ids)
        location = item.json_pointer or item.path
        print(f"[{item.severity.value}] {item.rule_id} ({reqs}) {location}: {item.message}")


def exit_code(result: ValidationResult, *, warnings_as_errors: bool) -> int:
    if any(issue.severity in {Severity.FATAL, Severity.ERROR} for issue in result.issues):
        return 1
    if warnings_as_errors and any(issue.severity == Severity.WARNING for issue in result.issues):
        return 1
    return 0
