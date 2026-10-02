<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Requirements Traceability

The normative rules are in the [upstream 1.0 specification](https://github.com/Original-Art-Archive/oaa-spec/blob/v1.0.0/SPEC.md). The supporting [oaa-1.0.yaml](oaa-1.0.yaml) catalog assigns stable requirement IDs; [traceability.md](traceability.md) maps them to validator rules and fixtures. The [0.1 catalog](oaa-0.1.yaml) remains unchanged for historical use, with its [historical specification](https://github.com/Original-Art-Archive/oaa-spec/blob/v0.1.2/SPEC.md).

These are unchanged copies of the specification's catalogs. Their `source_spec` and `source.file` paths describe provenance within the upstream specification repository at the matching version, not files in this repository. Tests use requirement IDs, sections, and classifications without opening a local `SPEC.md`; no specification checkout or network lookup is required.

Automated rules cover archive/content conditions and explicitly classified processing outcomes. Processing findings (unsupported version, configured capacity, unavailable input) are not archive-invalidity findings. Reader, writer, privacy, and other behavior that cannot be inferred from an archive is tracked separately; see the [verification scope](../README.md#verification).

The tests require every automated requirement to have rule and expected-finding fixture coverage, and every finding to reference known requirement IDs. Fixture coverage does not prove another application's implementation behavior.

Regenerate and check the matrix:

```powershell
python requirements/generate_traceability.py
python requirements/generate_traceability.py --check
```
