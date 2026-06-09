<!-- SPDX-License-Identifier: CC0-1.0 -->

# LOC Multi-Image Example

This example demonstrates one OAA artwork record with multiple embedded image files.

## Source and Attribution

- Source: [Library of Congress Prints & Photographs Online Catalog, item 2004672673](https://www.loc.gov/pictures/item/2004672673/)
- Title: Little Nemo in Slumberland
- Creator: Winsor McCay
- Repository: Library of Congress Prints and Photographs Division
- Rights advisory: No known restrictions on publication.

The embedded JPEG files are downloaded from the Library of Congress public image service. The manifest keeps each file's Library of Congress reproduction number, handle, service image URL, and master TIFF URL in `files[].external_links[].extensions.gov.loc`.

See [SOURCE.md](SOURCE.md) for the license boundary. Remgrandt Games LLC does not grant rights in the embedded Library of Congress media; consult the Library of Congress source page for current source and rights information.

## Demonstrated Structure

```text
mimetype
.oacollection
galleries/
  Library of Congress/
    .oagallery
artworks/
  OAA-00002/
    .oaartwork
    ppmsca-05788-panel-1.jpg
    ppmsca-05789-panel-2.jpg
    ppmsca-05790-panels-8-9.jpg
```

This example intentionally embeds reduced JPEG service files instead of the much larger master TIFF files so the repository remains lightweight while still demonstrating real multi-image source attribution.
