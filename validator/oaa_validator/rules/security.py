from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("security.high_risk_media", "High-risk embedded media is reported", ("OAA-SEC-002",), Severity.WARNING),
    RuleMetadata("security.local_path_in_manifest", "Path-like prose may disclose private information", ("OAA-SEC-004",), Severity.WARNING),
    RuleMetadata("security.resource_limits", "Reasonable resource limits are enforced", ("OAA-SEC-007",), Severity.INFO),
    RuleMetadata("security.input_unavailable", "Incomplete input read", ("OAA-SEC-008",), Severity.INFO),
]
