<!-- SPDX-License-Identifier: CC0-1.0 -->

# Examples

This directory contains OAA 1.0 folder-layout fixtures used by the validator tests.

The current directory fixtures use manifest version `"1.0"` and match the specification's examples. Historical generated archives remain unchanged. Download packaged examples from the [specification release](https://github.com/Original-Art-Archive/oaa-spec/releases/tag/v1.0.0).

Each example includes a root `mimetype` file containing `application/vnd.original-art-archive+zip`.

Example manifests use only valid OAA closed base values for `public_metadata.publication_status`, `files[].file_kind`, and `files[].image_role`. Provider-specific or application-specific values belong in extension blocks.

Do not commit real collector data. Real institutional fixture files may be used only when they have a clear public source, rights statement, and attribution.

CC0 applies to example manifests, fixture packaging, and sample media created by Remgrandt Works for this repository. Third-party or public-source media included or referenced by an example is not relicensed by Remgrandt Works unless explicitly stated. For examples that include or derive from public-source media, check the example's `SOURCE.md` file for source and rights notes before reusing embedded media.

- [minimal/](minimal/README.md) shows the smallest useful manifest set.
- [full/](full/README.md) shows richer provider metadata and extension block examples with synthetic image fixtures.
- [loc-multi-image/](loc-multi-image/README.md) shows a real multi-image public-source example with Library of Congress attribution.
- [public-domain-synthetic/](public-domain-synthetic/README.md) shows a practical archive with embedded synthetic PNG fixtures derived from public-domain published comic material.
