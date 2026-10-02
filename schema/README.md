<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Schema

[1.0/oaa-manifest.schema.json](1.0/oaa-manifest.schema.json) is the validator's local copy of the normative OAA 1.0 manifest schema. The [upstream specification](https://github.com/Original-Art-Archive/oaa-spec/blob/v1.0.0/SPEC.md) remains authoritative for the archive as a whole, including semantics, security, privacy, and cross-file integrity. Schema changes originate in that repository; these copies stay aligned with it.

The schema's `$id` identifies its immutable release URL. Tools can load the local file without resolving that URL over the network.

The root schema accepts the union of manifest shapes. Select the appropriate `$defs/collectionManifest`, `$defs/galleryManifest`, or `$defs/artworkManifest` using the manifest's role and path. Do not infer its role from optional JSON members: unknown optional fields are permitted.

The reference validator combines this schema with semantic checks for real calendar dates, absolute non-local URLs, finite numeric values, actual embedded sizes, duplicate JSON members, path safety, references, and bounded archive processing. JSON Schema alone cannot establish archive validity; format annotations are not a substitute for these checks.

Provider blocks are opaque JSON objects, including nested provider JSON and same-named fields. They cannot override base-field meaning. Existing closed base value sets remain enforced; display-oriented strings remain text.

[oaa-manifest.schema.json](oaa-manifest.schema.json) is the unchanged historical **0.1** schema, not an alias for 1.0.
