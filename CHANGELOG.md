<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Validator Changelog

## 1.0.0 — 2026-10-01

- Implements archive validation for OAA manifest version `"1.0"` using the matching local schema, semantic rules, and requirement catalogs.
- Distinguishes invalid archives from unsupported versions, capacity limits, and input/output failures. Version `"0.1"` returns unsupported; use the historical validator release for that version.
- Checks manifest references, primitive values, embedded sizes, safe paths and entry types, Store/Deflate compression, and bounded ZIP64 processing.
- Fixes termination for Deflate streams with trailing garbage at output-chunk boundaries.
- Detects the root manifest version before applying 1.0 container restrictions while retaining bounded safety preflight.
- Adds boundary, privacy, source-preservation, malformed-input, and standalone-package regression tests.
- Requires Python 3.12 or later. Packages the schema for offline installed use, uses package-relative imports, and makes source-distribution tests independent of Git.
- Retains the historical 0.1 schema and catalog without changing their contents.

## Earlier releases

See the [validator release history](https://github.com/Original-Art-Archive/oaa-validator/releases), including [v0.1.2](https://github.com/Original-Art-Archive/oaa-validator/releases/tag/v0.1.2).

Format decisions, compatibility guidance, and specification changes are maintained in the separate [specification repository](https://github.com/Original-Art-Archive/oaa-spec).
