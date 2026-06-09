<!-- SPDX-License-Identifier: CC0-1.0 -->

# Full Example

This directory is a fuller `.oaa` folder-layout example demonstrating optional fields, external links, extension block fields, and compatibility behavior.

The example shows the base hierarchy:

```text
mimetype
.oacollection
galleries/
  AP/
    .oagallery
  For Sale/
    .oagallery
artworks/
  OAA-00044/
    .oaartwork
    hit-comics-5-cover.png
```

Both example galleries reference the same artwork ID. The artwork folder includes an approved synthetic PNG fixture derived from public-domain comic material so its `files[]` entry resolves to an embedded archive file.

See [SOURCE.md](SOURCE.md) for source and rights notes, including what Remgrandt Games LLC dedicates to CC0 and what remains governed by the linked source page.

The artwork manifest credits Lou Fine for pencils and inks on the *Hit Comics #5* cover fixture.
