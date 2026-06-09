<!-- SPDX-License-Identifier: CC0-1.0 -->

# Examples

This directory contains draft OAA folder-layout examples.

The current examples are draft fixtures for the 0.1 Draft. They are intended to demonstrate readable archive layouts and manifest patterns while the format remains under review.

Each example includes a root `mimetype` file containing `application/vnd.original-art-archive+zip`.

Example manifests use only valid OAA closed base values for `public_metadata.publication_status`, `files[].file_kind`, and `files[].image_role`. Provider-specific or application-specific values belong in extension blocks.

Do not commit real collector data. Real institutional fixture files may be used only when they have a clear public source, rights statement, and attribution.

CC0 applies to example manifests, fixture packaging, and sample media created by Remgrandt Games LLC for this repository. Third-party or public-source media included or referenced by an example is not relicensed by Remgrandt Games LLC unless explicitly stated. For examples that include or derive from public-source media, check the example's `SOURCE.md` file for source and rights notes before reusing embedded media.

- `minimal/` shows the smallest useful manifest set.
- `full/` shows richer provider metadata and extension block examples with synthetic image fixtures.
- `loc-multi-image/` shows a real multi-image public-source example with Library of Congress attribution.
- `public-domain-synthetic/` shows a practical archive with embedded synthetic PNG fixtures derived from public-domain published comic material.
