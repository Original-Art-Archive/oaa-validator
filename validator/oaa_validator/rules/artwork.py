from ..model import RuleMetadata, Severity

RULES = [
    RuleMetadata("artwork.required_fields", "Artwork required fields are present", ("OAA-ART-010", "OAA-FILE-010"), Severity.FATAL),
    RuleMetadata("artwork.public_metadata_object", "Public metadata is an object", ("OAA-ART-011",), Severity.FATAL),
    RuleMetadata("artwork.private_metadata_object", "Private metadata is an object", ("OAA-ART-012",), Severity.FATAL),
    RuleMetadata("artwork.artist_credit_objects", "Artist credit entries are objects", ("OAA-PUB-001",), Severity.FATAL),
    RuleMetadata("artwork.publication_status", "Publication status uses closed base value set", ("OAA-PUB-002",), Severity.FATAL),
]
