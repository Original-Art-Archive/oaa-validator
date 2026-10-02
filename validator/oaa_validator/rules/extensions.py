from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("extensions.container_object", "Extension container is an object", ("OAA-EXT-001",), Severity.FATAL),
    RuleMetadata("extensions.block_object", "Extension block values are objects", ("OAA-EXT-002",), Severity.FATAL),
    RuleMetadata("extensions.unknown_block", "Unknown extension blocks are ignored", ("OAA-EXT-004",), Severity.INFO),
]
