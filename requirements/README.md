<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Requirements Traceability

The OAA specification is written for human readers and does not include visible requirement IDs inline.

Normative requirements used by the validator are tracked in [oaa-0.1.yaml](oaa-0.1.yaml).

The generated traceability matrix in [traceability.md](traceability.md) maps OAA requirement IDs to specification sections, validator rules, and conformance fixtures.

The validator catalog is scoped to archive validity. Reader, writer, round-trip, public-display, and implementation-behavior statements from the specification are tracked as excluded context unless they define a concrete archive/content condition that the validator can evaluate.

Validator tests are requirement-driven:

- Every automated requirement MUST be an archive/content validity requirement.
- Every automated requirement MUST map to at least one validator rule.
- Every validator rule MUST reference at least one cataloged requirement.
- Every validator rule MUST reference only automated archive-validity requirements.
- Every emitted validator issue MUST include requirement IDs.
- Every expected fixture finding MUST reference known rule and requirement IDs.
