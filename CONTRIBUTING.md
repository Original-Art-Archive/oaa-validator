<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing

OAA is currently a 0.1 Draft format. Validator changes should be proposed and reviewed against the public specification, archive validity, reader safety, and backward compatibility.

## Contribution Licensing

By contributing to this repository, you agree that your contribution is licensed under the same license that applies to the file or directory you are modifying.

For example:

- Contributions to `README.md`, `requirements/`, or other documentation are licensed under CC BY 4.0.
- Contributions to `examples/` or `tests/` are dedicated under CC0 1.0.
- Contributions to validator code, tools, scripts, or other software are licensed under MIT.

Do not contribute material unless you have the right to license it under the applicable license.

## Validator Changes

Format changes belong in the [OAA specification repository](https://github.com/Original-Art-Archive/oaa-spec). This repository should track the current public draft and validate archive/content requirements from that specification.

Changes that affect validation behavior should update these files together:

- [examples/](examples/)
- [validator/](validator/)
- [requirements/](requirements/)
- [tests/](tests/)

## Review Criteria

Reviewers should evaluate:

- Whether the change preserves safe archive validation.
- Whether runtime dependencies remain minimal and justified.
- Whether every emitted finding includes requirement IDs.
- Whether examples, fixtures, and traceability remain aligned with the public spec.
- Whether private collector metadata remains private by default.

## Draft Compatibility

Versions before 1.0 may change incompatibly, but draft changes should still document their compatibility impact.
