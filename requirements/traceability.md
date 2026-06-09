<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# OAA 0.1 Traceability Matrix

Generated from `requirements/oaa-0.1.yaml`, validator rule metadata, and fixture metadata.

| Requirement | Level | Coverage | Spec Section | Validator Rule | Severity | Fixtures |
| --- | --- | --- | --- | --- | --- | --- |
| OAA-PKG-001 | MUST | automated | Archive Container | package.archive_readable | fatal | non-zip-input<br>valid-minimal-archive |
| OAA-PKG-002 | SHOULD | automated | Archive Container | package.extension_oaa | warning | wrong-extension |
| OAA-PKG-003 | SHOULD_NOT | not_validator_scope | Archive Container |  |  |  |
| OAA-ZIP-001 | MUST | automated | Archive Container | package.encrypted_entries | fatal | encrypted-entry |
| OAA-ZIP-002 | SHOULD | automated | Archive Container | package.compression_method | warning | unsupported-compression |
| OAA-ZIP-003 | MUST | not_validator_scope | Archive Container |  |  |  |
| OAA-PATH-001 | MUST | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-002 | MUST | automated | Archive Container | paths.utf8_names | fatal | non-utf8-archive-name<br>valid-minimal-archive |
| OAA-PATH-003 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-004 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-005 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-006 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-007 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-008 | MUST | not_validator_scope | Archive Container |  |  | valid-minimal-archive |
| OAA-PATH-009 | MUST | not_validator_scope | Archive Container |  |  | valid-minimal-archive |
| OAA-PATH-010 | SHOULD | automated | Archive Container | paths.nfc | warning | non-nfc-path |
| OAA-PATH-011 | MUST_NOT | automated | Archive Container | paths.safe_archive_path | fatal | unsafe-archive-path<br>valid-minimal-archive |
| OAA-PATH-012 | MUST | automated | Archive Container | package.duplicate_entries | fatal | duplicate-archive-entry<br>valid-minimal-archive |
| OAA-PKG-010 | MUST | automated | Required Files | package.mimetype_present | fatal | missing-mimetype<br>valid-minimal-directory |
| OAA-PKG-011 | MUST | automated | Required Files | package.mimetype_value | fatal | bad-mimetype<br>valid-minimal-directory |
| OAA-PKG-012 | SHOULD | automated | Required Files | package.mimetype_first | warning | mimetype-not-first<br>valid-minimal-archive |
| OAA-PKG-013 | SHOULD | automated | Required Files | package.mimetype_stored | warning | compressed-mimetype<br>valid-minimal-archive |
| OAA-COL-001 | MUST | automated | Required Files | collection.manifest_present | fatal | missing-collection<br>valid-minimal-directory |
| OAA-GAL-001 | MUST | automated | Required Files | collection.gallery_manifest_present | fatal | missing-gallery-manifest<br>valid-minimal-directory |
| OAA-ART-001 | MUST | automated | Required Files | collection.artwork_manifest_present | fatal | missing-artwork-manifest<br>valid-minimal-directory |
| OAA-GAL-002 | MUST | automated | Directory Layout | gallery.artwork_refs_resolve | fatal | gallery-unknown-artwork |
| OAA-GAL-003 | MUST_NOT | automated | Directory Layout | gallery.no_mutable_artwork_metadata | fatal | gallery-duplicates-mutable-artwork-metadata |
| OAA-FILE-001 | MUST | automated | Directory Layout | files.relative_path_exists | error | missing-embedded-file<br>valid-full-directory |
| OAA-FILE-002 | MUST_NOT | not_validator_scope | Directory Layout |  |  |  |
| OAA-MAN-001 | MUST | automated | Manifest Files | manifests.json_object | fatal | bad-json-top-level<br>valid-minimal-directory |
| OAA-MAN-002 | MUST | automated | Manifest Files | manifests.json_object | fatal | bad-json-top-level<br>valid-minimal-directory |
| OAA-MAN-003 | MUST_NOT | automated | Manifest Files | manifests.duplicate_json_members | fatal | duplicate-json-member |
| OAA-MAN-004 | MUST_NOT | not_validator_scope | Manifest Files |  |  |  |
| OAA-MAN-005 | SHOULD_NOT | automated | Manifest Files | manifests.byte_order_mark | warning | manifest-with-bom |
| OAA-MAN-006 | MUST | automated | Manifest Files | manifests.schema_version_required | fatal | missing-schema-version<br>valid-minimal-directory |
| OAA-MAN-007 | MUST | automated | Manifest Files | manifests.schema_version_supported | fatal | schema-version-mismatch<br>unsupported-schema-version<br>valid-minimal-directory |
| OAA-MAN-008 | SHOULD | automated | Manifest Files | manifests.same_schema_versions | warning | schema-version-mismatch |
| OAA-MAN-009 | MUST | automated | Manifest Files | manifests.schema_version_supported | fatal | schema-version-mismatch<br>unsupported-schema-version |
| OAA-MAN-010 | MUST | automated | Manifest Files | manifests.unknown_optional_fields | info | unknown-optional-field |
| OAA-MAN-011 | SHOULD | not_validator_scope | Manifest Files |  |  |  |
| OAA-MAN-012 | MUST_NOT | automated | Manifest Files | manifests.required_string_not_empty | fatal | empty-required-string |
| OAA-MAN-013 | MUST_NOT | automated | Manifest Files | manifests.required_identifier_not_whitespace | fatal | whitespace-required-id |
| OAA-MAN-014 | SHOULD | not_validator_scope | Manifest Files |  |  |  |
| OAA-MAN-015 | MUST_NOT | automated | Manifest Files | paths.manifest_path_safe | fatal | untrimmed-artwork-manifest-path<br>untrimmed-manifest-path |
| OAA-MAN-016 | MUST | automated | Manifest Files | manifests.field_type | fatal | schema-field-type-error |
| OAA-COL-010 | MUST | automated | Collection Manifest | collection.required_fields | fatal | collection-missing-required<br>valid-minimal-directory |
| OAA-COL-011 | MUST | automated | Collection Manifest | external_links.object | fatal | external-link-not-object |
| OAA-COL-012 | MUST | automated | Collection Manifest | collection.gallery_refs_objects | fatal | collection-gallery-ref-not-object<br>valid-minimal-directory |
| OAA-COL-013 | MUST | automated | Collection Manifest | collection.artwork_refs_objects | fatal | collection-artwork-ref-not-object<br>valid-minimal-directory |
| OAA-COL-014 | MUST | automated | Collection Manifest | collection.unique_gallery_ids | fatal | duplicate-gallery-id<br>valid-loc-multi-image-directory |
| OAA-COL-015 | MUST | automated | Collection Manifest | collection.unique_gallery_paths | fatal | duplicate-gallery-path<br>valid-loc-multi-image-directory |
| OAA-COL-016 | MUST | automated | Collection Manifest | paths.manifest_path_safe | fatal | untrimmed-manifest-path<br>valid-loc-multi-image-directory |
| OAA-COL-017 | MUST | automated | Collection Manifest | collection.gallery_manifest_id_match | fatal | gallery-id-mismatch<br>valid-loc-multi-image-directory |
| OAA-COL-018 | MUST | automated | Collection Manifest | collection.unique_artwork_ids | fatal | duplicate-artwork-id<br>valid-loc-multi-image-directory |
| OAA-COL-019 | MUST | automated | Collection Manifest | collection.unique_artwork_paths | fatal | duplicate-artwork-path<br>valid-loc-multi-image-directory |
| OAA-COL-020 | MUST | automated | Collection Manifest | paths.manifest_path_safe | fatal | untrimmed-artwork-manifest-path<br>valid-loc-multi-image-directory |
| OAA-COL-021 | MUST | automated | Collection Manifest | collection.artwork_manifest_id_match | fatal | artwork-id-mismatch<br>valid-loc-multi-image-directory |
| OAA-GAL-010 | MUST | automated | Gallery Manifest | gallery.required_fields | fatal | gallery-missing-required<br>valid-minimal-directory |
| OAA-GAL-011 | MUST | automated | Gallery Manifest | gallery.artwork_refs_objects | fatal | gallery-artwork-ref-not-object<br>valid-minimal-directory |
| OAA-GAL-012 | MUST | automated | Gallery Manifest | gallery.artwork_refs_resolve | fatal | gallery-unknown-artwork<br>valid-minimal-directory |
| OAA-GAL-013 | MUST | automated | Gallery Manifest | gallery.unique_artwork_ids | fatal | duplicate-gallery-membership<br>valid-loc-multi-image-directory |
| OAA-ART-010 | MUST | automated | Artwork Manifest | artwork.required_fields | fatal | artwork-missing-required<br>valid-minimal-directory |
| OAA-ART-011 | MUST | automated | Artwork Manifest | artwork.public_metadata_object | fatal | public-metadata-not-object<br>valid-minimal-directory |
| OAA-ART-012 | MUST | automated | Artwork Manifest | artwork.private_metadata_object | fatal | private-metadata-not-object<br>valid-public-domain-synthetic-directory |
| OAA-ART-013 | MUST | automated | Artwork Manifest | files.entries_objects | fatal | files-entry-not-object<br>valid-public-domain-synthetic-directory |
| OAA-LINK-001 | MUST | automated | External Link Object | external_links.object | fatal | external-link-not-object<br>valid-full-directory |
| OAA-LINK-002 | MUST | automated | External Link Object | external_links.provider | fatal | external-link-bad-provider<br>valid-full-directory |
| OAA-LINK-003 | MUST_NOT | automated | External Link Object | external_links.provider | fatal | external-link-bad-provider<br>valid-full-directory |
| OAA-LINK-004 | MUST_NOT | automated | External Link Object | external_links.provider | fatal | external-link-bad-provider<br>valid-full-directory |
| OAA-LINK-005 | MUST_NOT | automated | External Link Object | external_links.id | fatal | external-link-empty-id<br>valid-full-directory |
| OAA-LINK-006 | MAY | not_validator_scope | External Link Object |  |  |  |
| OAA-LINK-010 | MUST | automated | External Link Object | external_links.url | fatal | external-link-url-not-string |
| OAA-LINK-007 | SHOULD | automated | External Link Object | external_links.url | warning | external-link-relative-url<br>valid-full-directory |
| OAA-LINK-008 | MUST_NOT | automated | External Link Object | external_links.unknown_provider | info | external-link-unknown-provider |
| OAA-LINK-009 | SHOULD | not_validator_scope | External Link Object |  |  |  |
| OAA-PUB-001 | MUST | automated | Public Artwork Metadata Object | artwork.artist_credit_objects | fatal | artist-credit-empty<br>artist-credit-not-object<br>valid-full-directory |
| OAA-PUB-002 | MUST | automated | Public Artwork Metadata Object | artwork.publication_status | fatal | bad-publication-status<br>valid-full-directory |
| OAA-PRIV-001 | MUST_NOT | not_validator_scope | Private Artwork Metadata Object |  |  |  |
| OAA-FILE-010 | MUST | automated | Artwork File Object | artwork.required_fields | fatal | artwork-missing-required<br>valid-minimal-directory |
| OAA-FILE-011 | MUST | automated | Artwork File Object | files.entries_objects | fatal | files-entry-not-object<br>valid-full-directory |
| OAA-FILE-012 | MUST | automated | Artwork File Object | files.relative_path_exists | error | missing-embedded-file<br>valid-full-directory |
| OAA-FILE-013 | MUST | automated | Artwork File Object | files.relative_path_safe | fatal | unsafe-file-relative-path<br>valid-full-directory |
| OAA-FILE-014 | MUST_NOT | automated | Artwork File Object | files.relative_path_safe | fatal | unsafe-file-relative-path<br>valid-full-directory |
| OAA-FILE-015 | MUST_NOT | automated | Artwork File Object | files.relative_path_safe | fatal | unsafe-file-relative-path<br>valid-full-directory |
| OAA-FILE-016 | MUST | automated | Identifiers | files.unique_file_ids | fatal | duplicate-file-id<br>valid-full-directory |
| OAA-FILE-017 | SHOULD | automated | Artwork File Object | files.multiple_primary | warning | multiple-primary-files<br>valid-full-directory |
| OAA-FILE-018 | MUST | automated | Artwork File Object | files.file_kind | fatal | bad-file-kind<br>valid-full-directory |
| OAA-FILE-019 | MUST | automated | Artwork File Object | files.image_role | fatal | bad-image-role<br>valid-full-directory |
| OAA-EXT-001 | MUST | automated | Extension Blocks | extensions.container_object | fatal | extensions-not-object<br>valid-full-directory |
| OAA-EXT-002 | MUST | automated | Extension Blocks | extensions.block_object | fatal | extension-block-not-object<br>valid-full-directory |
| OAA-EXT-003 | MUST_NOT | automated | Extension Blocks | extensions.no_nested_extensions | fatal | nested-extension-container |
| OAA-EXT-004 | MUST | automated | Extension Blocks | extensions.unknown_block | info | unknown-extension-block |
| OAA-EXT-005 | MUST_NOT | not_validator_scope | Extension Blocks |  |  |  |
| OAA-EXT-006 | MUST_NOT | automated | Extension Blocks | extensions.no_base_field_shadow | fatal | extension-shadows-base-publication-status |
| OAA-SEC-001 | MUST | not_validator_scope | Security and Privacy Considerations |  |  |  |
| OAA-SEC-002 | MUST | automated | Security and Privacy Considerations | security.high_risk_media | warning | high-risk-media |
| OAA-SEC-003 | MUST_NOT | not_validator_scope | Security and Privacy Considerations |  |  |  |
| OAA-SEC-004 | MUST_NOT | automated | Security and Privacy Considerations | security.local_path_in_manifest | fatal | local-path-in-extension<br>local-posix-path-in-manifest |
| OAA-SEC-006 | SHOULD | not_validator_scope | Security and Privacy Considerations |  |  |  |
| OAA-SEC-007 | SHOULD | automated | Security and Privacy Considerations | security.resource_limits | fatal | resource-limit-entry-count |
| OAA-CONF-001 | MUST | not_validator_scope | Reader Requirements |  |  |  |
| OAA-CONF-002 | MUST | not_validator_scope | Reader Requirements |  |  |  |
| OAA-CONF-003 | MUST | not_validator_scope | Reader Requirements |  |  |  |
| OAA-CONF-004 | MUST | not_validator_scope | Reader Requirements |  |  |  |
| OAA-CONF-005 | MUST | not_validator_scope | Reader Requirements |  |  |  |
| OAA-CONF-006 | MUST | not_validator_scope | Reader Requirements |  |  |  |
