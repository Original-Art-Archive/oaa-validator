<!-- SPDX-License-Identifier: CC0-1.0 -->

# Synthetic Public Domain Fixture Example

This example is a practical OAA archive folder containing embedded PNG images that an OAA reader can load directly.

The image files are user-approved synthetic demonstration images derived from public-domain published comic material:

- `artworks/OAA-00003/hit-comics-5-cover.png` is derived from the public-domain published cover for *Hit Comics #5*: <https://comicbookplus.com/?dlid=28295>
- `artworks/OAA-00004/irwl-007-cleaned-white.png` and `artworks/OAA-00005/irwl-012-cleaned-white.png` are derived from the public-domain comic source at <https://comicbookplus.com/?dlid=62011>

See [SOURCE.md](SOURCE.md) for source and rights notes, including what Remgrandt Works dedicates to CC0 and what remains governed by the linked source pages.

The artwork manifests credit Lou Fine for pencils and inks on the *Hit Comics #5* cover, and credit Matt Baker for pencils and Ray Osrin for inks on the IRWL interior pages.

This fixture demonstrates:

- A collection with multiple galleries.
- Multiple artwork records with embedded PNG files.
- Public-source attribution through `external_links`.
- Fixture-specific source notes isolated in extension blocks.

Package this folder as an `.oaa` archive by ZIP-compatible packaging rules, keeping `mimetype` as the first uncompressed entry.
