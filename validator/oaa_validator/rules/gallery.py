from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("gallery.required_fields", "Gallery required fields are present", ("OAA-GAL-010",), Severity.FATAL),
    RuleMetadata("gallery.artwork_refs_objects", "Gallery artwork references are objects", ("OAA-GAL-011",), Severity.FATAL),
    RuleMetadata("gallery.artwork_refs_resolve", "Gallery artwork references resolve", ("OAA-GAL-002", "OAA-GAL-012"), Severity.FATAL),
    RuleMetadata("gallery.unique_artwork_ids", "Gallery artwork references are unique", ("OAA-GAL-013",), Severity.FATAL),
    RuleMetadata("gallery.no_mutable_artwork_metadata", "Gallery references do not duplicate artwork metadata", ("OAA-GAL-003",), Severity.FATAL),
]
