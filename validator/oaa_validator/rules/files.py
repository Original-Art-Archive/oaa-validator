from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("files.entries_objects", "Artwork file entries are objects", ("OAA-ART-013", "OAA-FILE-011"), Severity.FATAL),
    RuleMetadata("files.relative_path_exists", "Artwork file relative_path resolves to embedded file", ("OAA-FILE-001", "OAA-FILE-012"), Severity.ERROR),
    RuleMetadata("files.relative_path_safe", "Artwork file relative_path is artwork-relative", ("OAA-FILE-013", "OAA-FILE-014", "OAA-FILE-015"), Severity.FATAL),
    RuleMetadata("files.unique_file_ids", "Artwork file IDs are unique", ("OAA-FILE-016",), Severity.FATAL),
    RuleMetadata("files.multiple_primary", "Artwork has at most one primary file", ("OAA-FILE-017",), Severity.WARNING),
    RuleMetadata("files.file_kind", "File kind uses closed base value set", ("OAA-FILE-018",), Severity.FATAL),
    RuleMetadata("files.image_role", "Image role uses closed base value set", ("OAA-FILE-019",), Severity.FATAL),
]
