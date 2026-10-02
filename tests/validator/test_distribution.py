# SPDX-License-Identifier: CC0-1.0
"""The installed package must not depend on a neighboring source checkout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DistributionTests(unittest.TestCase):
    def test_package_local_schema_without_repository_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "oaa_validator"
            shutil.copytree(ROOT / "validator" / "oaa_validator", target,
                            ignore=shutil.ignore_patterns("__pycache__"))
            (target / "schema").mkdir(exist_ok=True)
            shutil.copyfile(ROOT / "schema" / "1.0" / "oaa-manifest.schema.json",
                            target / "schema" / "oaa-manifest.schema.json")
            code = (
                "import json, sys; sys.path.insert(0, sys.argv[1]); "
                "from oaa_validator import validate_directory; "
                "print(json.dumps(validate_directory(sys.argv[2]).to_dict()))"
            )
            result = subprocess.run(
                [sys.executable, "-E", "-P", "-c", code, temporary, str(ROOT / "examples" / "minimal")],
                cwd=temporary, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "valid")


if __name__ == "__main__":
    unittest.main()
