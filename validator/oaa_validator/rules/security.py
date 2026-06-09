from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("security.high_risk_media", "High-risk embedded media is reported", ("OAA-SEC-002",), Severity.WARNING),
    RuleMetadata("security.local_path_in_manifest", "Manifest values must not contain local filesystem paths", ("OAA-SEC-004",), Severity.FATAL),
    RuleMetadata("security.resource_limits", "Reasonable resource limits are enforced", ("OAA-SEC-007",), Severity.FATAL),
]
