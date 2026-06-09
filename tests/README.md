<!-- SPDX-License-Identifier: CC0-1.0 -->

# Tests

This directory contains requirement-driven tests for the reference validator.

The validator fixture metadata lives under [../validator/fixtures](../validator/fixtures). Valid examples are copied from [../examples](../examples), and invalid inputs are produced by applying targeted mutations during the test run.

Run the test suite:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The traceability tests require every automated archive-validity requirement to have rule coverage and expected-finding fixture coverage.
