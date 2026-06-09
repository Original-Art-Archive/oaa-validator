from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("package.archive_readable", "Archive is ZIP-compatible", ("OAA-PKG-001",), Severity.FATAL),
    RuleMetadata("package.extension_oaa", "Filesystem archive uses .oaa extension", ("OAA-PKG-002",), Severity.WARNING),
    RuleMetadata("package.encrypted_entries", "Archive entries are not encrypted", ("OAA-ZIP-001",), Severity.FATAL),
    RuleMetadata("package.compression_method", "Archive entries use Store or Deflate", ("OAA-ZIP-002",), Severity.WARNING),
    RuleMetadata("package.duplicate_entries", "Archive entries are unique", ("OAA-PATH-012",), Severity.FATAL),
    RuleMetadata("package.mimetype_present", "Root mimetype file is present", ("OAA-PKG-010",), Severity.FATAL),
    RuleMetadata("package.mimetype_value", "Root mimetype value is exact", ("OAA-PKG-011",), Severity.FATAL),
    RuleMetadata("package.mimetype_first", "Root mimetype is first archive entry", ("OAA-PKG-012",), Severity.WARNING),
    RuleMetadata("package.mimetype_stored", "Root mimetype is stored without compression", ("OAA-PKG-013",), Severity.WARNING),
]
