<!-- SPDX-License-Identifier: MIT -->

<p align="center">
  <img src="assets/oaa-logo.svg" alt="Original Art Archive logo" width="180">
</p>

# Original Art Archive Validator

This repository contains the reference validator for the Original Art Archive (OAA) Format.

The validator checks whether an OAA archive is valid according to OAA 0.1 Draft archive/content requirements: package structure, required manifest fields, manifest shape, archive path safety, manifest-local-path rejection, reference integrity, extension block shape, external link shape, and resource limits.

The validator uses [schema/oaa-manifest.schema.json](schema/oaa-manifest.schema.json) through `jsonschema` for manifest-local JSON Schema validation, then applies custom checks for package structure, archive paths, cross-manifest references, embedded file resolution, resource limits, and other rules that cannot be validated from one manifest document alone.

It does not certify reader or writer implementation behavior. A writer can run its emitted archive through this validator to check whether the archive is valid, and a reader can use the validator as a preflight check before reading an archive. The validator does not extract archive contents to disk and does not open or render embedded media files.

The normative format specification is maintained in [Original-Art-Archive/oaa-spec](https://github.com/Original-Art-Archive/oaa-spec).

## Installation

Install from PyPI:

```powershell
python -m pip install oaa-validator
```

Install development dependencies from a source checkout:

```powershell
python -m pip install -r requirements\dev-requirements.txt
python -m pip install -e .
```

## Usage

Validate an `.oaa` archive:

```powershell
oaa-validator validate path\to\archive.oaa
```

Validate an unpacked OAA directory layout before packaging:

```powershell
oaa-validator validate-dir examples\minimal
```

Emit machine-readable output:

```powershell
oaa-validator validate-dir examples\minimal --json --show-info
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | No fatal or error findings. |
| `1` | Fatal or error findings were reported, or warnings were promoted with `--warnings-as-errors`. |
| `2` | CLI usage error. |

## Closed Base Value Checks

The validator rejects unknown values in OAA closed base value sets:

- Reject `files[].file_kind` values other than `raw`, `derivative`, and `supporting`.
- Reject `files[].image_role` values other than `raw_scan`, `raw_photo`, `corrected_scan`, `detail`, `verso`, and `reference` when the field is present and not null.
- Reject base `public_metadata.publication_status` values other than `published_art` and `unpublished_art` when the field is present and not null.

Display-oriented strings such as `public_metadata.media`, `public_metadata.artwork_type`, `artist_credits[].role`, `public_metadata.for_sale_status`, and `files[].format` are not treated as controlled OAA values.

## Traceability

Validator findings include both `rule_id` and `requirement_ids`.

Requirement IDs are not embedded in the public specification. They live in [requirements/oaa-0.1.yaml](requirements/oaa-0.1.yaml), and [requirements/traceability.md](requirements/traceability.md) is generated from the catalog, rule metadata, and fixture metadata.

Only archive-validity requirements may have automated validator rules. Reader, writer, round-trip, public-display, and implementation-behavior statements are excluded from automated validator scope unless they define a concrete archive/content condition.

Refresh the traceability matrix:

```powershell
python requirements/generate_traceability.py
```

Check that it is current:

```powershell
python requirements/generate_traceability.py --check
```

## Publishing

This repository publishes the `oaa-validator` package to PyPI from `.github/workflows/publish.yml`.

Publishing uses PyPI Trusted Publishing through the `pypi` GitHub environment. No PyPI API token is stored in this repository.
