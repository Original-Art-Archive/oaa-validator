from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("manifests.json_object", "Manifest is UTF-8 JSON object", ("OAA-MAN-001", "OAA-MAN-002"), Severity.FATAL),
    RuleMetadata("manifests.duplicate_json_members", "Manifest objects do not duplicate member names", ("OAA-MAN-003",), Severity.FATAL),
    RuleMetadata("manifests.byte_order_mark", "Manifest does not emit byte order mark", ("OAA-MAN-005",), Severity.WARNING),
    RuleMetadata("manifests.schema_version_required", "Manifest schema_version is present", ("OAA-MAN-006",), Severity.FATAL),
    RuleMetadata("manifests.schema_version_supported", "Manifest schema_version is supported", ("OAA-MAN-007", "OAA-MAN-009"), Severity.FATAL),
    RuleMetadata("manifests.same_schema_versions", "Manifest schema versions match", ("OAA-MAN-008",), Severity.WARNING),
    RuleMetadata("manifests.unknown_optional_fields", "Unknown optional fields are ignored", ("OAA-MAN-010",), Severity.INFO),
    RuleMetadata("manifests.required_string_not_empty", "Required string fields are not empty", ("OAA-MAN-012",), Severity.FATAL),
    RuleMetadata("manifests.required_identifier_not_whitespace", "Required identifier fields are not whitespace-only", ("OAA-MAN-013",), Severity.FATAL),
    RuleMetadata("manifests.field_type", "Manifest matches JSON Schema", ("OAA-MAN-016",), Severity.FATAL),
]
