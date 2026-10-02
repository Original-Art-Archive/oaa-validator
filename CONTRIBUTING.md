<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing to the Validator

This repository maintains the reference validator, its packaging, tests, and supporting fixtures for OAA manifest version `"1.0"`.

## Contribution Licensing

By contributing, you agree to the license that applies to the file or directory you modify:

- Documentation is CC BY 4.0 unless otherwise stated.
- Repository-authored examples and tests are CC0 1.0.
- Machine-readable schemas are CC0 1.0, or alternatively MIT when incorporated into software.
- Validator code, tools, and other software are MIT.

Only contribute material you have the right to license. Preserve third-party fixture attribution and the [names-and-marks policy](LICENSE.md#names-and-marks).

## Validator Changes

For a bug report, include a minimal synthetic reproducer, the validator version, expected and actual results, and relevant capacity settings. Do not attach private collector data or unredacted diagnostics.

For a fix, add a focused regression and update affected rules, fixtures, result documentation, and packaging as needed. Keep the [test suite](tests/README.md) and [requirements traceability](requirements/README.md) passing:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python requirements/generate_traceability.py --check
```

Review bounded processing, version dispatch, deterministic findings, privacy, and offline installed-package behavior. Test results establish this tool's behavior, not another application's conformance or extraction safety.

## Format Changes

Propose changes to manifest fields, archive requirements, schemas, or conformance rules in the separate [specification repository](https://github.com/Original-Art-Archive/oaa-spec/blob/main/CONTRIBUTING.md). Do not introduce new format rules through validator behavior alone. Update local schema and requirement-catalog copies only in coordination with accepted upstream changes.
