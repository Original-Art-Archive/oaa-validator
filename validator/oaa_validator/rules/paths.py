from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("paths.safe_archive_path", "Archive entry path is safe", ("OAA-PATH-001", "OAA-PATH-003", "OAA-PATH-004", "OAA-PATH-005", "OAA-PATH-006", "OAA-PATH-007", "OAA-PATH-011"), Severity.FATAL),
    RuleMetadata("paths.utf8_names", "Archive entry names are UTF-8", ("OAA-PATH-002",), Severity.FATAL),
    RuleMetadata("paths.nfc", "Archive paths are NFC", ("OAA-PATH-010",), Severity.WARNING),
    RuleMetadata("paths.manifest_path_safe", "Manifest path is safe and archive-relative", ("OAA-MAN-015", "OAA-COL-016", "OAA-COL-020"), Severity.FATAL),
]
