<!-- SPDX-License-Identifier: MIT -->

# Validator

This directory contains the reference validator for the Original Art Archive (OAA) Format.

The validator checks whether an OAA archive is valid according to OAA 0.1 Draft archive/content requirements: package structure, required manifest fields, manifest shape, archive path safety, manifest-local-path rejection, reference integrity, extension block shape, external link shape, and resource limits.

The validator uses [../schema/oaa-manifest.schema.json](../schema/oaa-manifest.schema.json) through `jsonschema` for manifest-local JSON Schema validation, then applies custom checks for package structure, archive paths, cross-manifest references, embedded file resolution, resource limits, and other rules that cannot be validated from one manifest document alone.

It does not certify reader or writer implementation behavior. A writer can run its emitted archive through this validator to check whether the archive is valid, and a reader can use the validator as a preflight check before reading an archive. The validator does not extract archive contents to disk and does not open or render embedded media files.

## Closed Base Value Checks

The validator rejects unknown values in OAA closed base value sets:

- Reject `files[].file_kind` values other than `raw`, `derivative`, and `supporting`.
- Reject `files[].image_role` values other than `raw_scan`, `raw_photo`, `corrected_scan`, `detail`, `verso`, and `reference` when the field is present and not null.
- Reject base `public_metadata.publication_status` values other than `published_art` and `unpublished_art` when the field is present and not null.

Display-oriented strings such as `public_metadata.media`, `public_metadata.artwork_type`, `artist_credits[].role`, `public_metadata.for_sale_status`, and `files[].format` are not treated as controlled OAA values.

## Severity Guide

| Condition | Severity | Reader behavior |
| --- | --- | --- |
| Unknown or invalid `public_metadata.publication_status` | Fatal | Reject archive or affected artwork record. |
| Unknown or invalid `files[].file_kind` | Fatal | Reject archive or affected artwork record. |
| Unknown or invalid `files[].image_role` | Fatal | Reject archive or affected artwork record. |
| Manifest does not match the OAA JSON Schema | Fatal | Reject archive or affected manifest record. |
| Unknown extension block | Info | Ignore for interpretation and preserve when practical. |
| Unknown external link provider | Info | Preserve and display generically when practical. |

## Usage

Validate an `.oaa` archive:

```powershell
python validator/oaa_validate.py validate path\to\archive.oaa
```

Validate a lab directory layout before packaging:

```powershell
python validator/oaa_validate.py validate-dir examples\minimal
```

Emit machine-readable output:

```powershell
python validator/oaa_validate.py validate-dir examples\minimal --json --show-info
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | No fatal or error findings. |
| `1` | Fatal or error findings were reported, or warnings were promoted with `--warnings-as-errors`. |
| `2` | CLI usage error. |

## Traceability

Validator findings include both `rule_id` and `requirement_ids`.

Requirement IDs are not embedded in [../SPEC.md](../SPEC.md). They live in [../requirements/oaa-0.1.yaml](../requirements/oaa-0.1.yaml), and [../requirements/traceability.md](../requirements/traceability.md) is generated from the catalog, rule metadata, and fixture metadata.

Only archive-validity requirements may have automated validator rules. Reader, writer, round-trip, public-display, and implementation-behavior statements are excluded from automated validator scope unless they define a concrete archive/content condition.

Refresh the traceability matrix:

```powershell
python requirements/generate_traceability.py
```

Check that it is current:

```powershell
python requirements/generate_traceability.py --check
```
