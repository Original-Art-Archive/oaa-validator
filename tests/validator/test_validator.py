import json
import os
import shutil
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from validator.oaa_validator import Limits, validate_archive, validate_directory


def load_fixture_file(relative):
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)["fixtures"]


def copy_tree(source, target):
    shutil.copytree(ROOT / source, target)


def set_path_value(data, path, value):
    current = data
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value


def apply_json_update(path, update):
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    for key in update.get("remove_keys", []):
        data.pop(key, None)
    for key, value in update.get("set", {}).items():
        data[key] = value
    if "set_path" in update:
        set_path_value(data, update["set_path"], update["value"])
    if update.get("duplicate_first_file"):
        data["files"].append(dict(data["files"][0]))
    if "duplicate_first_file_with_new_id" in update:
        item = dict(data["files"][0])
        item["id"] = update["duplicate_first_file_with_new_id"]
        data["files"].append(item)
    if "append_file" in update:
        data["files"].append(update["append_file"])
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path, data):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def apply_mutations(root, fixture):
    for rel in fixture.get("remove", []):
        target = root / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    for rel, text in fixture.get("write_text", {}).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for rel, hex_text in fixture.get("write_bytes", {}).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes.fromhex(hex_text))
    for rel, text in fixture.get("add_file", {}).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for rel, update in fixture.get("json_updates", {}).items():
        apply_json_update(root / rel, update)


def build_archive(source_dir, archive_path, fixture=None):
    fixture = fixture or {}
    seen_mimetype = False
    defer_mimetype = fixture.get("mimetype_not_first")
    mimetype_compression = zipfile.ZIP_DEFLATED if fixture.get("mimetype_compressed") else zipfile.ZIP_STORED
    with zipfile.ZipFile(archive_path, "w") as archive:
        mimetype = source_dir / "mimetype"
        if mimetype.exists() and not defer_mimetype:
            archive.write(mimetype, "mimetype", compress_type=mimetype_compression)
            seen_mimetype = True
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source_dir).as_posix()
            if rel == "mimetype":
                continue
            archive.write(path, rel, compress_type=zipfile.ZIP_DEFLATED)
        if mimetype.exists() and defer_mimetype:
            archive.write(mimetype, "mimetype", compress_type=mimetype_compression)
            seen_mimetype = True
        for entry in fixture.get("extra_archive_entries", []):
            archive.writestr(entry["path"], entry.get("text", ""))
        if "duplicate_archive_entry" in fixture:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(fixture["duplicate_archive_entry"], "duplicate")
    patch = fixture.get("zip_patch")
    if patch:
        patch_zip_flags(archive_path, patch)


def patch_zip_flags(path, patch):
    data = bytearray(path.read_bytes())
    if patch == "encrypted_first_entry":
        patch_zip_flag_bits(data, 0x0001)
    elif patch == "unsupported_non_manifest_compression":
        patch_zip_compression(data, 99, skip_name=b"mimetype")
    elif patch == "clear_utf8_flag_on_non_ascii":
        patch_zip_utf8_flag_for_non_ascii(data, clear=True)
    path.write_bytes(data)


def patch_zip_flag_bits(data, bits):
    i = 0
    while i < len(data) - 4:
        sig = data[i:i + 4]
        if sig == b"PK\x03\x04":
            flags = struct.unpack_from("<H", data, i + 6)[0]
            struct.pack_into("<H", data, i + 6, flags | bits)
            name_len = struct.unpack_from("<H", data, i + 26)[0]
            extra_len = struct.unpack_from("<H", data, i + 28)[0]
            comp_size = struct.unpack_from("<I", data, i + 18)[0]
            i += 30 + name_len + extra_len + comp_size
            continue
        if sig == b"PK\x01\x02":
            flags = struct.unpack_from("<H", data, i + 8)[0]
            struct.pack_into("<H", data, i + 8, flags | bits)
            i += 46
            continue
        i += 1


def patch_zip_compression(data, method, skip_name):
    i = 0
    patched = False
    while i < len(data) - 4:
        sig = data[i:i + 4]
        if sig == b"PK\x03\x04":
            name_len = struct.unpack_from("<H", data, i + 26)[0]
            extra_len = struct.unpack_from("<H", data, i + 28)[0]
            comp_size = struct.unpack_from("<I", data, i + 18)[0]
            name = bytes(data[i + 30:i + 30 + name_len])
            if name == b"README.md" and not patched:
                struct.pack_into("<H", data, i + 8, method)
                patched = True
            i += 30 + name_len + extra_len + comp_size
            continue
        if sig == b"PK\x01\x02":
            name_len = struct.unpack_from("<H", data, i + 28)[0]
            extra_len = struct.unpack_from("<H", data, i + 30)[0]
            comment_len = struct.unpack_from("<H", data, i + 32)[0]
            name = bytes(data[i + 46:i + 46 + name_len])
            if name == b"README.md":
                struct.pack_into("<H", data, i + 10, method)
            i += 46 + name_len + extra_len + comment_len
            continue
        i += 1


def patch_zip_utf8_flag_for_non_ascii(data, *, clear):
    i = 0
    while i < len(data) - 4:
        sig = data[i:i + 4]
        if sig == b"PK\x03\x04":
            name_len = struct.unpack_from("<H", data, i + 26)[0]
            extra_len = struct.unpack_from("<H", data, i + 28)[0]
            comp_size = struct.unpack_from("<I", data, i + 18)[0]
            name = bytes(data[i + 30:i + 30 + name_len])
            if any(byte > 127 for byte in name):
                flags = struct.unpack_from("<H", data, i + 6)[0]
                flags = flags & ~0x800 if clear else flags | 0x800
                struct.pack_into("<H", data, i + 6, flags)
            i += 30 + name_len + extra_len + comp_size
            continue
        if sig == b"PK\x01\x02":
            name_len = struct.unpack_from("<H", data, i + 28)[0]
            extra_len = struct.unpack_from("<H", data, i + 30)[0]
            comment_len = struct.unpack_from("<H", data, i + 32)[0]
            name = bytes(data[i + 46:i + 46 + name_len])
            if any(byte > 127 for byte in name):
                flags = struct.unpack_from("<H", data, i + 8)[0]
                flags = flags & ~0x800 if clear else flags | 0x800
                struct.pack_into("<H", data, i + 8, flags)
            i += 46 + name_len + extra_len + comment_len
            continue
        i += 1


def issue_key(issue):
    return (issue.rule_id, issue.severity.value)


def prepare_full_fixture(tmp_path, name):
    source = tmp_path / name
    copy_tree("examples/full", source)
    manifest_path = source / "artworks" / "OAA-00044" / ".oaartwork"
    artwork_dir = manifest_path.parent
    return source, manifest_path, artwork_dir, load_json(manifest_path)


def finding_keys(result):
    return {(issue.rule_id, issue.severity.value) for issue in result.issues}


class ValidatorFixtureTests(unittest.TestCase):
    def test_valid_fixtures_pass(self):
        fixtures = load_fixture_file("validator/fixtures/valid/examples.json")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for fixture in fixtures:
                with self.subTest(fixture=fixture["id"]):
                    source = tmp_path / fixture["id"]
                    copy_tree(fixture["source"], source)
                    if fixture["mode"] == "directory":
                        result = validate_directory(source)
                    else:
                        archive = tmp_path / f"{fixture['id']}.oaa"
                        build_archive(source, archive)
                        result = validate_archive(archive)
                    self.assertEqual(result.valid, fixture["expected_valid"], result.to_dict())

    def test_invalid_fixture_findings_match_requirements(self):
        fixtures = load_fixture_file("validator/fixtures/invalid/cases.json")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for fixture in fixtures:
                with self.subTest(fixture=fixture["id"]):
                    if fixture.get("kind") == "non_zip":
                        archive = tmp_path / "not-an-archive.oaa"
                        archive.write_text("not zip", encoding="utf-8")
                        result = validate_archive(archive)
                    else:
                        source = tmp_path / fixture["id"]
                        copy_tree(fixture["source"], source)
                        apply_mutations(source, fixture)
                        if fixture["mode"] == "archive":
                            archive_name = fixture.get("archive_name", f"{fixture['id']}.oaa")
                            archive = tmp_path / archive_name
                            build_archive(source, archive, fixture)
                            limits = Limits(**fixture.get("limits", {}))
                            result = validate_archive(archive, limits=limits)
                        else:
                            limits = Limits(**fixture.get("limits", {}))
                            result = validate_directory(source, limits=limits)
                    self.assertEqual(result.valid, fixture["expected_valid"], result.to_dict())
                    actual = {issue_key(issue): issue for issue in result.issues}
                    for expected in fixture["expected_findings"]:
                        key = (expected["rule_id"], expected["severity"])
                        self.assertIn(key, actual, result.to_dict())
                        self.assertEqual(
                            set(actual[key].requirement_ids),
                            set(expected["requirement_ids"]),
                        )
                    for issue in result.issues:
                        self.assertTrue(issue.requirement_ids)


class ClosedBaseValueTests(unittest.TestCase):
    def test_publication_status_accepts_allowed_values_null_and_omitted(self):
        cases = [
            ("published", "published_art"),
            ("unpublished", "unpublished_art"),
            ("null", None),
            ("omitted", "__omit__"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name, value in cases:
                with self.subTest(publication_status=name):
                    source, manifest_path, _artwork_dir, data = prepare_full_fixture(tmp_path, name)
                    if value == "__omit__":
                        data["public_metadata"].pop("publication_status", None)
                    else:
                        data["public_metadata"]["publication_status"] = value
                    write_json(manifest_path, data)

                    result = validate_directory(source)

                    self.assertTrue(result.valid, result.to_dict())
                    self.assertNotIn(("artwork.publication_status", "fatal"), finding_keys(result))

    def test_file_kind_and_image_role_accept_all_allowed_values_null_and_omitted(self):
        entries = [
            ("raw-scan.txt", "raw", "raw_scan"),
            ("raw-photo.txt", "raw", "raw_photo"),
            ("corrected-scan.txt", "raw", "corrected_scan"),
            ("detail.txt", "derivative", "detail"),
            ("verso.txt", "raw", "verso"),
            ("reference.txt", "supporting", "reference"),
            ("null-role.txt", "supporting", None),
            ("omitted-role.txt", "derivative", "__omit__"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            source, manifest_path, artwork_dir, data = prepare_full_fixture(Path(tmp), "closed-values")
            data["files"] = []
            for index, (file_name, file_kind, image_role) in enumerate(entries, start=1):
                (artwork_dir / file_name).write_text(f"fixture {index}", encoding="utf-8")
                entry = {
                    "id": f"closed-file-{index}",
                    "file_name": file_name,
                    "relative_path": file_name,
                    "file_kind": file_kind,
                    "is_primary": index == 1,
                    "media_type": "text/plain",
                }
                if image_role != "__omit__":
                    entry["image_role"] = image_role
                data["files"].append(entry)
            write_json(manifest_path, data)

            result = validate_directory(source)

            self.assertTrue(result.valid, result.to_dict())
            keys = finding_keys(result)
            self.assertNotIn(("files.file_kind", "fatal"), keys)
            self.assertNotIn(("files.image_role", "fatal"), keys)

    def test_closed_base_values_reject_invalid_types_and_missing_required_values(self):
        cases = [
            ("publication-status-number", ("public_metadata", "publication_status"), 42, ("artwork.publication_status", "fatal")),
            ("publication-status-display-label", ("public_metadata", "publication_status"), "Published Art", ("artwork.publication_status", "fatal")),
            ("file-kind-missing", ("files", 0, "file_kind"), "__delete__", ("files.file_kind", "fatal")),
            ("file-kind-null", ("files", 0, "file_kind"), None, ("files.file_kind", "fatal")),
            ("image-role-number", ("files", 0, "image_role"), 42, ("files.image_role", "fatal")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name, path, value, expected in cases:
                with self.subTest(case=name):
                    source, manifest_path, _artwork_dir, data = prepare_full_fixture(tmp_path, name)
                    current = data
                    for key in path[:-1]:
                        current = current[key]
                    if value == "__delete__":
                        current.pop(path[-1], None)
                    else:
                        current[path[-1]] = value
                    write_json(manifest_path, data)

                    result = validate_directory(source)

                    self.assertFalse(result.valid, result.to_dict())
                    self.assertIn(expected, finding_keys(result), result.to_dict())


class ManifestSchemaTests(unittest.TestCase):
    def test_json_schema_rejects_manifest_local_type_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, manifest_path, _artwork_dir, data = prepare_full_fixture(Path(tmp), "schema-type-error")
            data["public_metadata"]["is_public"] = "yes"
            write_json(manifest_path, data)

            result = validate_directory(source)

            self.assertFalse(result.valid, result.to_dict())
            self.assertIn(("manifests.field_type", "fatal"), finding_keys(result), result.to_dict())
            schema_issues = [issue for issue in result.issues if issue.rule_id == "manifests.field_type"]
            self.assertEqual(schema_issues[0].json_pointer, "/public_metadata/is_public")


class ValidatorCliTests(unittest.TestCase):
    def test_cli_json_output_includes_rule_and_requirement_ids(self):
        result = subprocess_run([
            sys.executable,
            "validator/oaa_validate.py",
            "validate-dir",
            "examples/minimal",
            "--json",
            "--show-info",
        ])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("issues", payload)
        self.assertEqual(payload["mode"], "directory")


def subprocess_run(args):
    import subprocess

    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
