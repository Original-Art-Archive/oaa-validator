from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("external_links.object", "External link entries are objects", ("OAA-COL-011", "OAA-LINK-001"), Severity.FATAL),
    RuleMetadata("external_links.provider", "External link provider identifier is valid", ("OAA-LINK-002", "OAA-LINK-003", "OAA-LINK-004"), Severity.FATAL),
    RuleMetadata("external_links.id", "External link ID is not empty", ("OAA-LINK-005",), Severity.FATAL),
    RuleMetadata("external_links.url", "External link URL is string and absolute when non-empty", ("OAA-LINK-010", "OAA-LINK-007"), Severity.WARNING),
    RuleMetadata("external_links.unknown_provider", "Unknown external link providers are accepted", ("OAA-LINK-008",), Severity.INFO),
]
