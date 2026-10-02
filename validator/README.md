<!-- SPDX-License-Identifier: MIT -->

# Reference Validator

This reference tool implements the **OAA 1.0**. It checks package structure, manifest JSON and field semantics, collection-authoritative references, embedded sizes, path safety, and bounded archive processing.

It uses the local [1.0 schema](../schema/1.0/oaa-manifest.schema.json) plus archive-wide rules. It does not extract files, fetch URLs, open media, render metadata, publish content, or certify another reader/writer. Its diagnostics are local processing output, not a sanitized public collection export.

## Run

Requires Python 3.12 or later (tested runtime is recorded in the [verification scope](../README.md#verification)) and the dependencies in [dev-requirements.txt](../requirements/dev-requirements.txt).

```powershell
python -m pip install -r requirements/dev-requirements.txt
python validator/oaa_validate.py validate path\to\archive.oaa
python validator/oaa_validate.py validate-dir examples\minimal --json --show-info
```

Directory mode is a convenience for already-unpacked layouts; it does not prove that a previous extractor was safe.

## Results

JSON output includes `valid` (true, false, or null), `status`, `complete`, issue severities, and requirement IDs.

| Status | Meaning |
| --- | --- |
| `valid` | Completed the supported archive/content checks without a validity violation. |
| `invalid` | A concrete validity violation was found; `complete` can still be false if checking stopped early. |
| `unsupported` | Manifest version is not supported; no validity conclusion without a separate proven violation. |
| `capacity_exceeded` | A configured processing limit was reached; not proof of invalidity. |
| `io_error` | Input could not be completely read; not proof of invalidity. |

A proven invalidity takes precedence in `status` if an incomplete-processing finding also exists. The issue list retains both. This tool does not offer salvage/recovery mode.

| Exit | Meaning |
| --- | --- |
| 0 | Completed successfully (advisory warnings may exist). |
| 1 | Invalid input, or warnings promoted by `--warnings-as-errors`. |
| 2 | CLI usage error, including a missing input path. |
| 3 | Unsupported or incomplete processing without a proven validity failure. |

Unknown providers and optional data are accepted. Closed base values remain enforced. Path-like prose is advisory, while unsafe actual references are invalid.

## Declared Capacities

Defaults: archive 2 GiB; total uncompressed content 4 GiB; 100,000 entries; individual file 1 GiB; manifest 10 MiB; JSON nesting 100 containers; central directory 16 MiB. CLI `--max-*` options override these with positive integers; `--help` lists them. JSON integers are limited to 4,300 digits by this implementation.

Directory metadata is bounded before constructing the ZIP entry table. Version dispatch reads only the fixed root `.oacollection`, under manifest, individual-file, total-size, and JSON limits, after refusing ambiguous, encrypted, or special root entries. This probe supports bounded Store, Deflate, and BZIP2 decoding; other root compression methods yield `unsupported` without attempting decompression. BZIP2 probe support does not make it valid in 1.0.

If the root declares an unsupported version, validation stops without reading other entries or imposing 1.0 container rules. This is not a safety or validity certification of the unread content. Once the root declares 1.0, paths, encryption, compression, special entries, and file/directory conflicts are checked before reading remaining payloads. Every file, including unreferenced extras, is then streamed with decompressed-size bounds and archive CRC verification. Trailing compressed-stream data is rejected at EOF, including at output-chunk boundaries.

The bounded ZIP64 end-record preflight uses a private Python standard-library helper; keep the ZIP64 and malformed-input regressions passing when upgrading Python.

## Scope and History

The current validator implements manifest version `"1.0"` only. Version `"0.1"` is an unsupported input, not intrinsically invalid. The `v0.1.2` snapshot preserves the historical implementation, and [fixtures/0.1/cases.json](fixtures/0.1/cases.json) preserves its old mutation catalog.

Rules and fixtures are mapped in [requirements/traceability.md](../requirements/traceability.md). Run the [test suite](../tests/README.md) before making a conformance claim.
