from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("collection.manifest_present", "Collection manifest is present", ("OAA-COL-001",), Severity.FATAL),
    RuleMetadata("collection.required_fields", "Collection required fields are present", ("OAA-COL-010",), Severity.FATAL),
    RuleMetadata("collection.gallery_refs_objects", "Collection gallery references are objects", ("OAA-COL-012",), Severity.FATAL),
    RuleMetadata("collection.artwork_refs_objects", "Collection artwork references are objects", ("OAA-COL-013",), Severity.FATAL),
    RuleMetadata("collection.unique_gallery_ids", "Collection gallery IDs are unique", ("OAA-COL-014",), Severity.FATAL),
    RuleMetadata("collection.unique_gallery_paths", "Collection gallery paths are unique", ("OAA-COL-015",), Severity.FATAL),
    RuleMetadata("collection.unique_artwork_ids", "Collection artwork IDs are unique", ("OAA-COL-018",), Severity.FATAL),
    RuleMetadata("collection.unique_artwork_paths", "Collection artwork paths are unique", ("OAA-COL-019",), Severity.FATAL),
    RuleMetadata("collection.gallery_manifest_present", "Referenced gallery manifests are present", ("OAA-GAL-001",), Severity.FATAL),
    RuleMetadata("collection.artwork_manifest_present", "Referenced artwork manifests are present", ("OAA-ART-001",), Severity.FATAL),
    RuleMetadata("collection.gallery_manifest_id_match", "Gallery manifest ID matches collection reference", ("OAA-COL-017",), Severity.FATAL),
    RuleMetadata("collection.artwork_manifest_id_match", "Artwork manifest ID matches collection reference", ("OAA-COL-021",), Severity.FATAL),
]
