from __future__ import annotations

from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any
import json
import re
import unicodedata
import zipfile

from jsonschema import Draft202012Validator

from .model import Limits, Severity, ValidationIssue, ValidationResult
from .rules import rule_map
from .source import OaaSource, load_archive, load_directory

MIMETYPE = b"application/vnd.original-art-archive+zip"
SUPPORTED_SCHEMA = "0.1"
PACKAGE_SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "oaa-manifest.schema.json"
REPO_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "oaa-manifest.schema.json"
SUPPORTED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
KNOWN_PROVIDERS = {
    "app.oa-curator",
    "com.comicartfans",
    "com.comicbookplus",
    "com.raremarq",
    "com.snikt",
    "gov.loc",
    "org.originalartarchive.examples",
}
KNOWN_EXTENSION_BLOCKS = KNOWN_PROVIDERS | {"org.originalartarchive.examples"}
KNOWN_FILE_KINDS = {"raw", "derivative", "supporting"}
KNOWN_IMAGE_ROLES = {"raw_scan", "raw_photo", "corrected_scan", "detail", "verso", "reference"}
HIGH_RISK_EXTENSIONS = {".html", ".htm", ".svg", ".js", ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".scr", ".msi"}
HIGH_RISK_MEDIA_TYPES = {"text/html", "image/svg+xml", "application/javascript", "text/javascript"}
COLLECTION_BASE_FIELDS = {"schema_version", "id", "name", "external_links", "galleries", "artworks"}
COLLECTION_REF_BASE_FIELDS = {"id", "path"}
GALLERY_BASE_FIELDS = {"schema_version", "id", "name", "external_links", "artworks"}
GALLERY_ARTWORK_REF_BASE_FIELDS = {"id"}
ARTWORK_BASE_FIELDS = {"schema_version", "id", "title", "external_links", "public_metadata", "private_metadata", "files"}
PUBLIC_METADATA_BASE_FIELDS = {"description", "for_sale_status", "media", "artwork_type", "publication_status", "is_public", "artist_credits"}
ARTIST_CREDIT_BASE_FIELDS = {"display_name", "first_name", "last_name", "role"}
PRIVATE_METADATA_BASE_FIELDS = {"purchase_price", "estimated_value", "purchase_date", "provenance", "personal_notes"}
FILE_BASE_FIELDS = {"id", "file_name", "relative_path", "file_kind", "size_bytes", "width", "height", "format", "media_type", "is_primary", "image_role", "external_links"}
EXTERNAL_LINK_BASE_FIELDS = {"provider", "id", "url"}
MUTABLE_GALLERY_ARTWORK_FIELDS = {
    "title",
    "external_links",
    "artist_credits",
    "media",
    "private_metadata",
    "public_metadata",
    "files",
}
PROVIDER_RE = re.compile(r"^[a-z0-9._-]+$")
LOCAL_PATH_RE = re.compile(r"(^[A-Za-z]:[\\/])|(^\\\\)|(^file://)|(^/(Users|home|var|tmp|Volumes|mnt|opt|etc)(/|$))")
RULES = rule_map()


class DuplicateMemberError(ValueError):
    pass


def issue(
    rule_id: str,
    message: str,
    path: str,
    *,
    manifest: str | None = None,
    json_pointer: str | None = None,
    requirement_ids: tuple[str, ...] | None = None,
    severity: Severity | None = None,
) -> ValidationIssue:
    rule = RULES[rule_id]
    return ValidationIssue(
        rule_id=rule.id,
        requirement_ids=requirement_ids or rule.requirement_ids,
        severity=severity or rule.severity,
        message=message,
        path=path,
        manifest=manifest,
        json_pointer=json_pointer,
    )


def validate_archive(path: str | Path, limits: Limits | None = None) -> ValidationResult:
    archive_path = Path(path)
    result = ValidationResult(input=archive_path, mode="archive")
    limits = limits or Limits()

    if archive_path.suffix.lower() != ".oaa":
        result.add(issue("package.extension_oaa", "Archive filesystem name does not use the `.oaa` extension.", str(archive_path)))

    if archive_path.exists() and archive_path.is_file() and archive_path.stat().st_size > limits.max_archive_size:
        result.add(issue("security.resource_limits", "Archive exceeds the configured archive size limit.", str(archive_path)))

    source = load_archive(archive_path)
    if source.archive_error is not None:
        result.add(issue("package.archive_readable", "Input is not a readable ZIP-compatible OAA archive.", str(archive_path)))
        return result
    validate_source(source, result, limits)
    return result


def validate_directory(path: str | Path, limits: Limits | None = None) -> ValidationResult:
    directory = Path(path)
    result = ValidationResult(input=directory, mode="directory")
    limits = limits or Limits()
    source = load_directory(directory)
    validate_source(source, result, limits)
    return result


def validate_source(source: OaaSource, result: ValidationResult, limits: Limits) -> None:
    check_resource_limits(source, result, limits)
    if source.mode == "archive":
        check_archive_package(source, result)
    check_paths(source, result)
    check_mimetype(source, result)

    manifests = parse_manifests(source, result, limits)
    collection = manifests.get(".oacollection")
    if collection is None:
        if source.has_file(".oacollection"):
            return
        result.add(issue("collection.manifest_present", "Archive is missing the root `.oacollection` manifest.", ".oacollection"))
        return

    validate_collection(source, result, manifests, collection)


def check_resource_limits(source: OaaSource, result: ValidationResult, limits: Limits) -> None:
    if len(source.entries) > limits.max_entries:
        result.add(issue("security.resource_limits", "Archive entry count exceeds the configured limit.", str(source.root)))
    total = 0
    for entry in source.entries:
        total += entry.file_size
        if entry.file_size > limits.max_entry_size:
            result.add(issue("security.resource_limits", "Archive entry exceeds the configured individual file size limit.", entry.path))
    if total > limits.max_uncompressed_size:
        result.add(issue("security.resource_limits", "Archive uncompressed size exceeds the configured limit.", str(source.root)))


def check_archive_package(source: OaaSource, result: ValidationResult) -> None:
    for duplicate in sorted(source.duplicate_paths):
        result.add(issue("package.duplicate_entries", "Archive contains duplicate entries with the same path.", duplicate))
    for entry in source.entries:
        if entry.encrypted:
            result.add(issue("package.encrypted_entries", "Archive entry is encrypted.", entry.path))
        if entry.compress_type not in SUPPORTED_COMPRESSION:
            result.add(issue("package.compression_method", "Archive entry does not use Store or Deflate compression.", entry.path))
        if not entry.utf8_flag and any(ord(char) > 127 for char in entry.path):
            result.add(issue("paths.utf8_names", "Non-ASCII archive entry name is not marked as UTF-8.", entry.path))

    if source.entries:
        first = source.entries[0]
        if first.path != "mimetype":
            result.add(issue("package.mimetype_first", "`mimetype` is not the first ZIP entry.", first.path))
    mimetype_entries = [entry for entry in source.entries if entry.path == "mimetype"]
    if mimetype_entries and mimetype_entries[0].compress_type != zipfile.ZIP_STORED:
        result.add(issue("package.mimetype_stored", "`mimetype` is not stored without compression.", "mimetype"))


def check_paths(source: OaaSource, result: ValidationResult) -> None:
    lower_seen: dict[str, str] = {}
    for entry in source.entries:
        problems = archive_path_problems(entry.path, allow_directory=entry.is_dir)
        for problem in problems:
            result.add(issue("paths.safe_archive_path", problem, entry.path))
        if unicodedata.normalize("NFC", entry.path) != entry.path:
            result.add(issue("paths.nfc", "Archive entry path is not Unicode NFC.", entry.path))
        lowered = entry.path.lower()
        if lowered in lower_seen and lower_seen[lowered] != entry.path:
            continue
        lower_seen[lowered] = entry.path


def archive_path_problems(path: str, *, allow_directory: bool = False) -> list[str]:
    problems: list[str] = []
    if not path:
        return ["Archive entry path is empty."]
    if "\\" in path:
        problems.append("Archive entry path contains a backslash separator.")
    if path.startswith("/"):
        problems.append("Archive entry path is absolute.")
    parts = path.split("/")
    for index, part in enumerate(parts):
        if part == "" and not (allow_directory and index == len(parts) - 1):
            problems.append("Archive entry path contains an empty segment.")
        elif part == ".":
            problems.append("Archive entry path contains a `.` segment.")
        elif part == "..":
            problems.append("Archive entry path contains a `..` traversal segment.")
    return problems


def manifest_path_problems(path: Any) -> list[str]:
    if not isinstance(path, str):
        return ["Manifest path is not a string."]
    problems = archive_path_problems(path)
    if path != path.strip():
        problems.append("Manifest path contains leading or trailing whitespace and is not trimmed before resolution.")
    return problems


def check_mimetype(source: OaaSource, result: ValidationResult) -> None:
    if not source.has_file("mimetype"):
        result.add(issue("package.mimetype_present", "Archive is missing required root `mimetype` file.", "mimetype"))
        return
    data = source.read_bytes("mimetype")
    if data != MIMETYPE:
        result.add(issue("package.mimetype_value", "Root `mimetype` value is not exact.", "mimetype"))


def parse_manifests(source: OaaSource, result: ValidationResult, limits: Limits) -> dict[str, dict[str, Any] | None]:
    paths = [".oacollection"]
    collection_data = parse_manifest(source, result, ".oacollection", limits)
    manifests: dict[str, dict[str, Any] | None] = {".oacollection": collection_data}
    if not isinstance(collection_data, dict):
        return manifests
    for ref_type in ("galleries", "artworks"):
        for ref in collection_data.get(ref_type, []) if isinstance(collection_data.get(ref_type), list) else []:
            if isinstance(ref, dict) and isinstance(ref.get("path"), str):
                paths.append(ref["path"])
    for path in paths[1:]:
        manifests[path] = parse_manifest(source, result, path, limits)

    versions = {
        path: manifest.get("schema_version")
        for path, manifest in manifests.items()
        if isinstance(manifest, dict) and "schema_version" in manifest
    }
    if len(set(versions.values())) > 1:
        for path in versions:
            result.add(issue("manifests.same_schema_versions", "Manifest schema versions in this archive do not all match.", path, manifest=path))
    return manifests


def parse_manifest(source: OaaSource, result: ValidationResult, path: str, limits: Limits) -> dict[str, Any] | None:
    if not source.has_file(path):
        return None
    entry = next((item for item in source.entries if item.path == path), None)
    if entry is not None and entry.file_size > limits.max_manifest_size:
        result.add(issue("security.resource_limits", "Manifest exceeds the configured manifest size limit.", path, manifest=path))
        return None
    raw = source.read_bytes(path)
    if raw is None:
        result.add(issue("manifests.json_object", "Manifest cannot be read as UTF-8 JSON.", path, manifest=path))
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        result.add(issue("manifests.byte_order_mark", "Manifest starts with a byte order mark.", path, manifest=path))
    try:
        text = raw.decode("utf-8-sig")
        data = json.loads(text, object_pairs_hook=reject_duplicate_members)
    except DuplicateMemberError as exc:
        result.add(issue("manifests.duplicate_json_members", str(exc), path, manifest=path))
        return None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        result.add(issue("manifests.json_object", f"Manifest is not valid UTF-8 JSON: {exc}", path, manifest=path))
        return None
    if not isinstance(data, dict):
        result.add(issue("manifests.json_object", "Manifest top level is not a JSON object.", path, manifest=path))
        return None
    if json_depth(data) > limits.max_json_depth:
        result.add(issue("security.resource_limits", "Manifest JSON nesting depth exceeds configured limit.", path, manifest=path))
    validate_schema_version(result, data, path)
    validate_manifest_schema(result, data, path)
    scan_manifest_for_local_paths(result, data, path, "")
    return data


@cache
def manifest_schema() -> dict[str, Any]:
    for path in (PACKAGE_SCHEMA_PATH, REPO_SCHEMA_PATH):
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
    raise FileNotFoundError("Could not locate bundled OAA manifest JSON Schema.")


@cache
def manifest_schema_validator(kind: str) -> Draft202012Validator:
    schema = manifest_schema()
    branch_by_kind = {
        "collection": schema["oneOf"][0],
        "gallery": schema["oneOf"][1],
        "artwork": schema["oneOf"][2],
    }
    selected_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        **branch_by_kind.get(kind, {"oneOf": schema["oneOf"]}),
    }
    Draft202012Validator.check_schema(selected_schema)
    return Draft202012Validator(selected_schema)


def manifest_kind_from_path(path: str) -> str:
    if path == ".oacollection":
        return "collection"
    if path.endswith("/.oagallery"):
        return "gallery"
    if path.endswith("/.oaartwork"):
        return "artwork"
    return "unknown"


def validate_manifest_schema(result: ValidationResult, manifest: dict[str, Any], path: str) -> None:
    validator = manifest_schema_validator(manifest_kind_from_path(path))
    errors = sorted(
        validator.iter_errors(manifest),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    for error in errors:
        pointer = json_pointer(error.absolute_path)
        location = f" at `{pointer}`" if pointer else ""
        result.add(
            issue(
                "manifests.field_type",
                f"Manifest does not match the OAA JSON Schema{location}: {error.message}",
                path,
                manifest=path,
                json_pointer=pointer,
            )
        )


def reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateMemberError(f"Manifest JSON object contains duplicate member name `{key}`.")
        output[key] = value
    return output


def json_depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((json_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((json_depth(item) for item in value), default=0)
    return 1


def validate_schema_version(result: ValidationResult, manifest: dict[str, Any], path: str) -> None:
    if "schema_version" not in manifest:
        result.add(issue("manifests.schema_version_required", "Manifest is missing `schema_version`.", path, manifest=path))
        return
    if manifest["schema_version"] != SUPPORTED_SCHEMA:
        result.add(issue("manifests.schema_version_supported", "Manifest `schema_version` is not supported by this validator.", path, manifest=path))


def validate_collection(source: OaaSource, result: ValidationResult, manifests: dict[str, dict[str, Any] | None], collection: dict[str, Any]) -> None:
    validate_unknown_optional_fields(result, collection, ".oacollection", COLLECTION_BASE_FIELDS | {"extensions"})
    require_fields(result, collection, ".oacollection", ["schema_version", "id", "name", "galleries", "artworks"], "collection.required_fields")
    validate_required_string(result, collection, "id", ".oacollection", "/id")
    validate_required_string(result, collection, "name", ".oacollection", "/name")
    validate_external_links(result, collection.get("external_links", []), ".oacollection", "/external_links")
    validate_extensions(result, collection.get("extensions"), ".oacollection", "/extensions", collection, COLLECTION_BASE_FIELDS)

    galleries = collection.get("galleries")
    artworks = collection.get("artworks")
    if not isinstance(galleries, list):
        result.add(issue("collection.required_fields", "Collection `galleries` field is not an array.", ".oacollection", manifest=".oacollection", json_pointer="/galleries"))
        galleries = []
    if not isinstance(artworks, list):
        result.add(issue("collection.required_fields", "Collection `artworks` field is not an array.", ".oacollection", manifest=".oacollection", json_pointer="/artworks"))
        artworks = []

    gallery_refs = validate_collection_refs(result, galleries, ".oacollection", "gallery")
    artwork_refs = validate_collection_refs(result, artworks, ".oacollection", "artwork")
    collection_artwork_ids = {ref["id"] for ref in artwork_refs if isinstance(ref.get("id"), str)}

    for ref in gallery_refs:
        path = ref.get("path")
        if not isinstance(path, str):
            continue
        if not source.has_file(path):
            result.add(issue("collection.gallery_manifest_present", "Referenced gallery manifest is missing.", path, manifest=".oacollection"))
            continue
        manifest = manifests.get(path)
        if isinstance(manifest, dict):
            validate_gallery(result, manifest, path, collection_artwork_ids)
            if manifest.get("id") != ref.get("id"):
                result.add(issue("collection.gallery_manifest_id_match", "Gallery manifest `id` does not match collection reference.", path, manifest=path, json_pointer="/id"))

    for ref in artwork_refs:
        path = ref.get("path")
        if not isinstance(path, str):
            continue
        if not source.has_file(path):
            result.add(issue("collection.artwork_manifest_present", "Referenced artwork manifest is missing.", path, manifest=".oacollection"))
            continue
        manifest = manifests.get(path)
        if isinstance(manifest, dict):
            validate_artwork(source, result, manifest, path)
            if manifest.get("id") != ref.get("id"):
                result.add(issue("collection.artwork_manifest_id_match", "Artwork manifest `id` does not match collection reference.", path, manifest=path, json_pointer="/id"))


def require_fields(result: ValidationResult, obj: dict[str, Any], path: str, fields: list[str], rule_id: str) -> None:
    for field in fields:
        if field not in obj:
            result.add(issue(rule_id, f"Required field `{field}` is missing.", path, manifest=path, json_pointer=f"/{field}"))


def validate_required_string(result: ValidationResult, obj: dict[str, Any], key: str, manifest: str, pointer: str) -> None:
    value = obj.get(key)
    if isinstance(value, str) and value == "":
        result.add(issue("manifests.required_string_not_empty", f"Required string `{key}` is empty.", manifest, manifest=manifest, json_pointer=pointer))
    if isinstance(value, str) and value.strip() == "" and value != "":
        result.add(issue("manifests.required_identifier_not_whitespace", f"Required identifier `{key}` is whitespace-only.", manifest, manifest=manifest, json_pointer=pointer))


def validate_collection_refs(result: ValidationResult, refs: list[Any], manifest: str, ref_type: str) -> list[dict[str, Any]]:
    object_rule = "collection.gallery_refs_objects" if ref_type == "gallery" else "collection.artwork_refs_objects"
    unique_id_rule = "collection.unique_gallery_ids" if ref_type == "gallery" else "collection.unique_artwork_ids"
    unique_path_rule = "collection.unique_gallery_paths" if ref_type == "gallery" else "collection.unique_artwork_paths"
    path_requirement = ("OAA-MAN-015", "OAA-COL-016") if ref_type == "gallery" else ("OAA-MAN-015", "OAA-COL-020")
    valid_refs: list[dict[str, Any]] = []
    ids: list[str] = []
    paths: list[str] = []
    for index, ref in enumerate(refs):
        pointer = f"/{ref_type}s/{index}"
        if not isinstance(ref, dict):
            result.add(issue(object_rule, f"Collection `{ref_type}s[]` entry is not an object.", manifest, manifest=manifest, json_pointer=pointer))
            continue
        valid_refs.append(ref)
        validate_required_string(result, ref, "id", manifest, f"{pointer}/id")
        for problem in manifest_path_problems(ref.get("path")):
            result.add(issue("paths.manifest_path_safe", problem, str(ref.get("path")), manifest=manifest, json_pointer=f"{pointer}/path", requirement_ids=path_requirement))
        if isinstance(ref.get("id"), str):
            ids.append(ref["id"])
        if isinstance(ref.get("path"), str):
            paths.append(ref["path"])
        validate_extensions(result, ref.get("extensions"), manifest, f"{pointer}/extensions", ref, COLLECTION_REF_BASE_FIELDS)
    add_duplicate_issues(result, ids, unique_id_rule, manifest, f"/{ref_type}s")
    add_duplicate_issues(result, paths, unique_path_rule, manifest, f"/{ref_type}s")
    return valid_refs


def add_duplicate_issues(result: ValidationResult, values: list[str], rule_id: str, manifest: str, pointer: str) -> None:
    for value, count in Counter(values).items():
        if count > 1:
            result.add(issue(rule_id, f"Duplicate value `{value}`.", manifest, manifest=manifest, json_pointer=pointer))


def validate_gallery(result: ValidationResult, manifest: dict[str, Any], path: str, collection_artwork_ids: set[str]) -> None:
    validate_unknown_optional_fields(result, manifest, path, GALLERY_BASE_FIELDS | {"extensions"})
    require_fields(result, manifest, path, ["schema_version", "id", "name", "artworks"], "gallery.required_fields")
    validate_required_string(result, manifest, "id", path, "/id")
    validate_required_string(result, manifest, "name", path, "/name")
    validate_external_links(result, manifest.get("external_links", []), path, "/external_links")
    validate_extensions(result, manifest.get("extensions"), path, "/extensions", manifest, GALLERY_BASE_FIELDS)
    artworks = manifest.get("artworks")
    if not isinstance(artworks, list):
        result.add(issue("gallery.required_fields", "Gallery `artworks` field is not an array.", path, manifest=path, json_pointer="/artworks"))
        return
    ids: list[str] = []
    for index, ref in enumerate(artworks):
        pointer = f"/artworks/{index}"
        if not isinstance(ref, dict):
            result.add(issue("gallery.artwork_refs_objects", "Gallery `artworks[]` entry is not an object.", path, manifest=path, json_pointer=pointer))
            continue
        extras = set(ref) & MUTABLE_GALLERY_ARTWORK_FIELDS
        if extras:
            result.add(issue("gallery.no_mutable_artwork_metadata", "Gallery artwork reference duplicates mutable artwork metadata.", path, manifest=path, json_pointer=pointer))
        validate_required_string(result, ref, "id", path, f"{pointer}/id")
        if isinstance(ref.get("id"), str):
            ids.append(ref["id"])
            if ref["id"] not in collection_artwork_ids:
                result.add(issue("gallery.artwork_refs_resolve", "Gallery artwork reference does not resolve to a collection artwork ID.", path, manifest=path, json_pointer=f"{pointer}/id"))
        validate_extensions(result, ref.get("extensions"), path, f"{pointer}/extensions", ref, GALLERY_ARTWORK_REF_BASE_FIELDS)
    add_duplicate_issues(result, ids, "gallery.unique_artwork_ids", path, "/artworks")


def validate_artwork(source: OaaSource, result: ValidationResult, manifest: dict[str, Any], path: str) -> None:
    validate_unknown_optional_fields(result, manifest, path, ARTWORK_BASE_FIELDS | {"extensions"})
    require_fields(result, manifest, path, ["schema_version", "id", "title", "files"], "artwork.required_fields")
    validate_required_string(result, manifest, "id", path, "/id")
    validate_required_string(result, manifest, "title", path, "/title")
    validate_external_links(result, manifest.get("external_links", []), path, "/external_links")
    validate_extensions(result, manifest.get("extensions"), path, "/extensions", manifest, ARTWORK_BASE_FIELDS)

    public_metadata = manifest.get("public_metadata")
    if public_metadata is not None and not isinstance(public_metadata, dict):
        result.add(issue("artwork.public_metadata_object", "Artwork `public_metadata` is not an object.", path, manifest=path, json_pointer="/public_metadata"))
    elif isinstance(public_metadata, dict):
        validate_public_metadata(result, public_metadata, path)
    private_metadata = manifest.get("private_metadata")
    if private_metadata is not None and not isinstance(private_metadata, dict):
        result.add(issue("artwork.private_metadata_object", "Artwork `private_metadata` is not an object.", path, manifest=path, json_pointer="/private_metadata"))
    elif isinstance(private_metadata, dict):
        validate_extensions(result, private_metadata.get("extensions"), path, "/private_metadata/extensions", private_metadata, PRIVATE_METADATA_BASE_FIELDS)

    files = manifest.get("files")
    if not isinstance(files, list):
        result.add(issue("artwork.required_fields", "Artwork `files` field is not an array.", path, manifest=path, json_pointer="/files"))
        return
    validate_files(source, result, files, path)


def validate_public_metadata(result: ValidationResult, data: dict[str, Any], manifest: str) -> None:
    status = data.get("publication_status")
    if status is not None and status not in {"published_art", "unpublished_art"}:
        result.add(issue("artwork.publication_status", "Base `publication_status` is not an allowed OAA value.", manifest, manifest=manifest, json_pointer="/public_metadata/publication_status"))
    artist_credits = data.get("artist_credits", [])
    if artist_credits is not None and not isinstance(artist_credits, list):
        result.add(issue("artwork.artist_credit_objects", "`artist_credits` is not an array.", manifest, manifest=manifest, json_pointer="/public_metadata/artist_credits"))
    elif isinstance(artist_credits, list):
        for index, credit in enumerate(artist_credits):
            if not isinstance(credit, dict):
                result.add(issue("artwork.artist_credit_objects", "`artist_credits[]` entry is not an object.", manifest, manifest=manifest, json_pointer=f"/public_metadata/artist_credits/{index}"))
            else:
                if not any(credit.get(field) for field in ("display_name", "first_name", "last_name", "role")):
                    result.add(issue("artwork.artist_credit_objects", "`artist_credits[]` entry contains no artist name or role fields.", manifest, manifest=manifest, json_pointer=f"/public_metadata/artist_credits/{index}"))
                validate_extensions(result, credit.get("extensions"), manifest, f"/public_metadata/artist_credits/{index}/extensions", credit, ARTIST_CREDIT_BASE_FIELDS)
    validate_extensions(result, data.get("extensions"), manifest, "/public_metadata/extensions", data, PUBLIC_METADATA_BASE_FIELDS)


def validate_files(source: OaaSource, result: ValidationResult, files: list[Any], artwork_manifest: str) -> None:
    ids: list[str] = []
    primary_count = 0
    artwork_dir = artwork_manifest.rsplit("/", 1)[0] if "/" in artwork_manifest else ""
    for index, file_entry in enumerate(files):
        pointer = f"/files/{index}"
        if not isinstance(file_entry, dict):
            result.add(issue("files.entries_objects", "`files[]` entry is not an object.", artwork_manifest, manifest=artwork_manifest, json_pointer=pointer))
            continue
        validate_required_string(result, file_entry, "id", artwork_manifest, f"{pointer}/id")
        if isinstance(file_entry.get("id"), str):
            ids.append(file_entry["id"])
        rel = file_entry.get("relative_path")
        problems = manifest_path_problems(rel)
        if isinstance(rel, str) and "/" in rel:
            # A slash is allowed in relative paths, but traversal/absolute checks still apply.
            problems = archive_path_problems(rel)
            if rel != rel.strip():
                problems.append("File relative path contains leading or trailing whitespace.")
        if problems:
            for problem in problems:
                result.add(issue("files.relative_path_safe", problem, str(rel), manifest=artwork_manifest, json_pointer=f"{pointer}/relative_path"))
        elif isinstance(rel, str):
            resolved = f"{artwork_dir}/{rel}" if artwork_dir else rel
            if archive_path_problems(resolved) or not source.has_file(resolved):
                result.add(issue("files.relative_path_exists", "Artwork file entry does not resolve to an embedded archive file.", resolved, manifest=artwork_manifest, json_pointer=f"{pointer}/relative_path"))
        if file_entry.get("is_primary") is True:
            primary_count += 1
        kind = file_entry.get("file_kind")
        if not isinstance(kind, str) or kind not in KNOWN_FILE_KINDS:
            result.add(issue("files.file_kind", "Base `file_kind` is not an allowed OAA value.", artwork_manifest, manifest=artwork_manifest, json_pointer=f"{pointer}/file_kind"))
        role = file_entry.get("image_role")
        if role is not None and (not isinstance(role, str) or role not in KNOWN_IMAGE_ROLES):
            result.add(issue("files.image_role", "Base `image_role` is not an allowed OAA value.", artwork_manifest, manifest=artwork_manifest, json_pointer=f"{pointer}/image_role"))
        check_media_risk(result, file_entry, artwork_manifest, pointer)
        validate_external_links(result, file_entry.get("external_links", []), artwork_manifest, f"{pointer}/external_links")
        validate_extensions(result, file_entry.get("extensions"), artwork_manifest, f"{pointer}/extensions", file_entry, FILE_BASE_FIELDS)
    add_duplicate_issues(result, ids, "files.unique_file_ids", artwork_manifest, "/files")
    if primary_count > 1:
        result.add(issue("files.multiple_primary", "More than one file entry has `is_primary: true`.", artwork_manifest, manifest=artwork_manifest, json_pointer="/files"))


def check_media_risk(result: ValidationResult, file_entry: dict[str, Any], manifest: str, pointer: str) -> None:
    name = str(file_entry.get("relative_path") or file_entry.get("file_name") or "")
    suffix = Path(name).suffix.lower()
    media_type = file_entry.get("media_type")
    if suffix in HIGH_RISK_EXTENSIONS or media_type in HIGH_RISK_MEDIA_TYPES:
        result.add(issue("security.high_risk_media", "Embedded file type may have active or high-risk behavior.", manifest, manifest=manifest, json_pointer=pointer))


def validate_external_links(result: ValidationResult, links: Any, manifest: str, pointer: str) -> None:
    if links in (None, []):
        return
    if not isinstance(links, list):
        result.add(issue("external_links.object", "`external_links` is not an array of objects.", manifest, manifest=manifest, json_pointer=pointer))
        return
    for index, link in enumerate(links):
        item_pointer = f"{pointer}/{index}"
        if not isinstance(link, dict):
            result.add(issue("external_links.object", "`external_links[]` entry is not an object.", manifest, manifest=manifest, json_pointer=item_pointer))
            continue
        provider = link.get("provider")
        if not isinstance(provider, str) or not provider or not PROVIDER_RE.match(provider) or provider.startswith(".") or provider.endswith(".") or ".." in provider:
            result.add(issue("external_links.provider", "External link provider identifier violates the OAA provider grammar.", manifest, manifest=manifest, json_pointer=f"{item_pointer}/provider"))
        elif provider not in KNOWN_PROVIDERS:
            result.add(issue("external_links.unknown_provider", "External link provider is unknown and will be treated generically.", manifest, manifest=manifest, json_pointer=f"{item_pointer}/provider"))
        link_id = link.get("id")
        if not isinstance(link_id, str) or link_id == "":
            result.add(issue("external_links.id", "External link `id` is missing or empty.", manifest, manifest=manifest, json_pointer=f"{item_pointer}/id"))
        url = link.get("url")
        if not isinstance(url, str):
            result.add(issue("external_links.url", "External link `url` is not a string.", manifest, manifest=manifest, json_pointer=f"{item_pointer}/url", requirement_ids=("OAA-LINK-010",), severity=Severity.FATAL))
        elif url and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", url):
            result.add(issue("external_links.url", "External link `url` is non-empty but not absolute.", manifest, manifest=manifest, json_pointer=f"{item_pointer}/url", requirement_ids=("OAA-LINK-007",)))
        validate_extensions(result, link.get("extensions"), manifest, f"{item_pointer}/extensions", link, EXTERNAL_LINK_BASE_FIELDS)


def validate_extensions(result: ValidationResult, extensions: Any, manifest: str, pointer: str, parent: dict[str, Any] | None = None, base_fields: set[str] | None = None) -> None:
    if extensions is None:
        return
    if not isinstance(extensions, dict):
        result.add(issue("extensions.container_object", "`extensions` value is not an object.", manifest, manifest=manifest, json_pointer=pointer))
        return
    present_base_fields = {field for field in (base_fields or set()) if parent is not None and field in parent}
    for name, block in extensions.items():
        block_pointer = f"{pointer}/{escape_json_pointer(name)}"
        if not isinstance(block, dict):
            result.add(issue("extensions.block_object", "Extension block value is not an object.", manifest, manifest=manifest, json_pointer=block_pointer))
            continue
        for field in sorted(set(block) & present_base_fields):
            result.add(issue("extensions.no_base_field_shadow", f"Extension block field `{field}` shadows a present OAA base field.", manifest, manifest=manifest, json_pointer=f"{block_pointer}/{escape_json_pointer(field)}"))
        if "extensions" in block:
            result.add(issue("extensions.no_nested_extensions", "Extension block contains a nested `extensions` container.", manifest, manifest=manifest, json_pointer=block_pointer))
        if name not in KNOWN_EXTENSION_BLOCKS:
            result.add(issue("extensions.unknown_block", "Extension block is unknown and will be ignored for OAA interpretation.", manifest, manifest=manifest, json_pointer=block_pointer))


def scan_manifest_for_local_paths(result: ValidationResult, value: Any, manifest: str, pointer: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            item_pointer = f"{pointer}/{escape_json_pointer(str(key))}" if pointer else f"/{escape_json_pointer(str(key))}"
            scan_manifest_for_local_paths(result, item, manifest, item_pointer)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_manifest_for_local_paths(result, item, manifest, f"{pointer}/{index}")
    elif isinstance(value, str) and LOCAL_PATH_RE.search(value):
        result.add(issue("security.local_path_in_manifest", "Manifest value contains an apparent absolute local filesystem path.", manifest, manifest=manifest, json_pointer=pointer))


def validate_unknown_optional_fields(result: ValidationResult, obj: dict[str, Any], manifest: str, allowed: set[str]) -> None:
    for key in obj:
        if key not in allowed:
            result.add(issue("manifests.unknown_optional_fields", f"Unknown optional field `{key}` is ignored for OAA interpretation.", manifest, manifest=manifest, json_pointer=f"/{escape_json_pointer(key)}"))


def escape_json_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def json_pointer(parts: Any) -> str:
    path = list(parts)
    if not path:
        return ""
    return "/" + "/".join(escape_json_pointer(str(part)) for part in path)
