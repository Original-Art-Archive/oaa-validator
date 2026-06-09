#!/usr/bin/env python
"""Command-line entrypoint for the OAA validator."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validator.oaa_validator.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
