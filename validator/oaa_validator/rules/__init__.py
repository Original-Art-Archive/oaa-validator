from __future__ import annotations

from ..model import RuleMetadata

from . import artwork, collection, external_links, extensions, files, gallery, manifests, package, paths, security

MODULES = [
    package,
    paths,
    manifests,
    collection,
    gallery,
    artwork,
    files,
    external_links,
    extensions,
    security,
]


def all_rules() -> list[RuleMetadata]:
    rules: list[RuleMetadata] = []
    for module in MODULES:
        rules.extend(module.RULES)
    return rules


def rule_map() -> dict[str, RuleMetadata]:
    return {rule.id: rule for rule in all_rules()}
