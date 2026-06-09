from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("extensions.container_object", "Extension container is an object", ("OAA-EXT-001",), Severity.FATAL),
    RuleMetadata("extensions.block_object", "Extension block values are objects", ("OAA-EXT-002",), Severity.FATAL),
    RuleMetadata("extensions.no_nested_extensions", "Extension blocks do not contain nested extension containers", ("OAA-EXT-003",), Severity.FATAL),
    RuleMetadata("extensions.unknown_block", "Unknown extension blocks are ignored", ("OAA-EXT-004",), Severity.INFO),
    RuleMetadata("extensions.no_base_field_shadow", "Extension block fields do not shadow present base fields", ("OAA-EXT-006",), Severity.FATAL),
]
