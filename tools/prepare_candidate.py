# SPDX-License-Identifier: MIT
"""Fixture archive writer used by the reference tests."""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validator.oaa_validator import Limits, validate_archive, validate_directory

EXAMPLES = ("minimal", "full", "loc-multi-image", "public-domain-synthetic")


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_example(name, destination):
    if name not in EXAMPLES:
        raise ValueError("Not a reviewed fixture name")
    source = ROOT / "examples" / name
    preflight = validate_directory(source)
    if preflight.valid is not True or not preflight.completed:
        raise ValueError(f"Fixture preflight did not complete successfully: {name}")
    paths = [path for path in source.rglob("*") if path.is_file()]
    paths.sort(key=lambda path: (path != source / "mimetype", path.as_posix()))
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            method = zipfile.ZIP_STORED if path == source / "mimetype" else zipfile.ZIP_DEFLATED
            archive.write(path, path.relative_to(source).as_posix(), compress_type=method)
    result = validate_archive(destination)
    if result.valid is not True or not result.completed:
        raise ValueError(f"Emitted fixture did not validate: {name}")
    with zipfile.ZipFile(destination) as archive:
        for path in paths:
            with archive.open(path.relative_to(source).as_posix()) as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != digest(path):
                    raise ValueError(f"Embedded bytes changed: {name}")
    return {"status": result.status, "complete": result.completed,
            "entries": len(paths), "summary": result.summary(), "sha256": digest(destination)}

