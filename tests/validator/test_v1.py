# SPDX-License-Identifier: CC0-1.0
import copy
import json
import hashlib
import io
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

from validator.oaa_validator import Limits, validate_archive
from validator.oaa_validator.source import OaaSource, load_archive
from validator.oaa_validator.cli import main

MIME = b"application/vnd.original-art-archive+zip"


def records():
    return {
        ".oacollection": {"schema_version": "1.0", "id": "same", "name": "Test",
                          "galleries": [{"id": "same", "path": "groups/g/.oagallery"}],
                          "artworks": [{"id": "same", "path": "pieces/a/.oaartwork"}]},
        "groups/g/.oagallery": {"schema_version": "1.0", "id": "same", "name": "Test", "artworks": []},
        "pieces/a/.oaartwork": {"schema_version": "1.0", "id": "same", "title": "Test",
                              "files": [{"id": "f", "relative_path": "scan.bin", "file_kind": "raw", "size_bytes": 3}]},
    }


def write_archive(path, manifests=None, extras=(), compression=zipfile.ZIP_DEFLATED, zip64=False):
    manifests = records() if manifests is None else manifests
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        archive.writestr("mimetype", MIME, compress_type=zipfile.ZIP_STORED)
        for name, value in manifests.items():
            archive.writestr(name, json.dumps(value) if isinstance(value, dict) else value)
        if zip64:
            with archive.open("pieces/a/scan.bin", "w", force_zip64=True) as handle:
                handle.write(b"abc")
        else:
            archive.writestr("pieces/a/scan.bin", b"abc")
        for name, value in extras:
            archive.writestr(name, value)


class VersionOneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "test.oaa"

    def validate(self, manifests=None, **kwargs):
        write_archive(self.archive, manifests, **kwargs)
        return validate_archive(self.archive)

    def test_v1_layout_identity_empty_membership_and_zip64(self):
        self.assertTrue(self.validate(zip64=True).valid)

    def test_extensions_are_opaque_and_unknown_fields_are_accepted(self):
        data = records()
        data["pieces/a/.oaartwork"].update({"artworks": [], "extensions": {"com.example": {
            "title": "Other", "extensions": {"dpi_x": -1}, "local_note": "C:/old/folder"}}})
        self.assertTrue(self.validate(data, extras=[("extra/.oaartwork", "not a manifest record")]).valid)

    def test_nullable_values_and_real_dates(self):
        for date, expected in [(None, True), ("2024-02-29", True), ("2025-02-29", False)]:
            data = records()
            art = data["pieces/a/.oaartwork"]
            art["private_metadata"] = {"purchase_date": date}
            art["files"][0].update({"dpi_x": None, "dpi_y": 300, "width": None, "height": 12})
            with self.subTest(date=date):
                self.assertEqual(self.validate(data).valid, expected)

    def test_size_mismatch(self):
        data = records()
        data["pieces/a/.oaartwork"]["files"][0]["size_bytes"] = 4
        result = self.validate(data)
        self.assertIn("files.size_bytes", {i.rule_id for i in result.issues})
        self.assertFalse(result.valid)

    def test_non_json_numbers_and_wrong_types_do_not_crash(self):
        for value in [float("nan"), float("inf"), {}, []]:
            data = records()
            data["pieces/a/.oaartwork"]["public_metadata"] = {"publication_status": value}
            with self.subTest(value=value):
                self.assertFalse(self.validate(data).valid)

    def test_unsupported_version_is_incomplete_not_invalid(self):
        data = records()
        for value in data.values():
            value["schema_version"] = "9.0"
        result = self.validate(data)
        self.assertIsNone(result.valid)
        self.assertEqual(result.to_dict()["status"], "unsupported")

    def test_unsupported_root_does_not_guess_future_manifest_structure(self):
        data = records()
        data[".oacollection"]["schema_version"] = "9.0"
        data["groups/g/.oagallery"] = "future opaque child data"
        self.assertEqual(self.validate(data).status, "unsupported")

    def test_capacity_stops_before_content_reads(self):
        write_archive(self.archive)
        with patch.object(OaaSource, "read_bytes", side_effect=AssertionError("read after capacity limit")):
            result = validate_archive(self.archive, Limits(max_uncompressed_size=1))
        self.assertIsNone(result.valid)
        self.assertEqual(result.to_dict()["status"], "capacity_exceeded")

    def test_unsafe_entry_types_conflicts_and_compression(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for extras in [[(link, "outside")], [("pieces", "file")], [("C:/outside", "bad")]]:
            with self.subTest(extras=extras):
                self.assertFalse(self.validate(extras=extras).valid)
        self.assertFalse(self.validate(compression=zipfile.ZIP_BZIP2).valid)

    def test_true_zip64_end_records(self):
        # Force actual ZIP64 end records on a small fixture, not just a local header.
        with patch.object(zipfile, "ZIP64_LIMIT", 100):
            write_archive(self.archive)
        self.assertIn(b"PK\x06\x06", self.archive.read_bytes())
        self.assertTrue(validate_archive(self.archive).valid)

    def test_central_directory_capacity_precedes_zipfile_allocation(self):
        write_archive(self.archive)
        with patch.object(zipfile, "ZipFile", side_effect=AssertionError("allocated directory")):
            result = validate_archive(self.archive, Limits(max_directory_size=1))
        self.assertEqual(result.status, "capacity_exceeded")

    def test_all_declared_capacities_stop_with_incomplete_result(self):
        write_archive(self.archive)
        for option in ("max_archive_size", "max_uncompressed_size", "max_entries", "max_entry_size",
                       "max_manifest_size", "max_json_depth", "max_directory_size"):
            with self.subTest(option=option):
                result = validate_archive(self.archive, Limits(**{option: 1}))
                self.assertIsNone(result.valid)
                self.assertFalse(result.to_dict()["complete"])
                self.assertEqual(result.status, "capacity_exceeded")

    def test_deep_json_and_numeric_parser_capacity(self):
        for raw in ['{"schema_version":"1.0","x":' + '[' * 101 + '0' + ']' * 101 + '}',
                    '{"schema_version":"1.0","x":' + '1' * 4301 + '}']:
            result = self.validate({".oacollection": raw})
            self.assertIsNone(result.valid)
            self.assertEqual(result.status, "capacity_exceeded")

    def test_wrong_version_types_and_duplicate_json_members(self):
        for version in ([], {}, None, 1, True, ""):
            data = records()
            data[".oacollection"]["schema_version"] = version
            with self.subTest(version=version):
                self.assertFalse(self.validate(data).valid)
        self.assertFalse(self.validate({".oacollection": '{"id":"a","id":"b"}'}).valid)

    def test_numeric_values_not_booleans_or_nonpositive_dimensions(self):
        for field in ("size_bytes", "width", "height", "dpi_x", "dpi_y"):
            for value in (True, False, -1, "12", [], {}):
                data = records()
                data["pieces/a/.oaartwork"]["files"][0][field] = value
                with self.subTest(field=field, value=value):
                    self.assertFalse(self.validate(data).valid)
        data = records()
        data["pieces/a/.oaartwork"]["files"][0].update(width=12.0, dpi_x=72.25)
        self.assertTrue(self.validate(data).valid)

    def test_external_urls_and_repeated_provider_associations(self):
        for url, expected in [("", True), ("https://example.org/a%20b?q=1#x", True),
                              ("urn:example:item", True), ("https://[::1]/", True),
                              ("relative/item", False), ("file:///private", False),
                              ("C:/private", False), ("https:///path", False),
                              ("https://example.org/%no", False), ("https://example.org/a b", False),
                              ("https://example.org:invalid", False), (None, False)]:
            data = records()
            link = {"provider": "com.unknown", "id": "not-a-merge-key", "url": url}
            data["pieces/a/.oaartwork"]["external_links"] = [link, copy.deepcopy(link)]
            with self.subTest(url=url):
                self.assertEqual(self.validate(data).valid, expected)

    def test_uri_component_grammar(self):
        for url, expected in [("https://example.org/a#b#c", False),
                              ("https://example.org/a[b]", False),
                              ("https://[::1]trailing/", False),
                              ("https://user@@example.org/", False),
                              ("https://example.org:65536/", True),
                              ("custom://host:abc/path", False)]:
            data = records()
            data["pieces/a/.oaartwork"]["external_links"] = [{"provider": "com.example", "id": "x", "url": url}]
            with self.subTest(url=url):
                self.assertEqual(self.validate(data).valid, expected)

    def test_exact_provider_and_manifest_path_grammar(self):
        data = records()
        data["pieces/a/.oaartwork"]["external_links"] = [{"provider": "com.example\n", "id": "x", "url": ""}]
        self.assertFalse(self.validate(data).valid)
        for path, expected in [("groups/g/.oagallery\n", False), ("groups/line\nbreak/.oagallery", True)]:
            data = records()
            data[".oacollection"]["galleries"][0]["path"] = path
            data[path] = data.pop("groups/g/.oagallery")
            with self.subTest(path=path):
                self.assertEqual(self.validate(data).valid, expected)

    def test_empty_collection_metadata_only_and_case_distinct_extras(self):
        data = records()
        data[".oacollection"].update(galleries=[], artworks=[])
        self.assertTrue(self.validate(data).valid)
        data = records()
        data["pieces/a/.oaartwork"]["files"] = []
        self.assertTrue(self.validate(data, extras=[("Extra.txt", "one"), ("extra.txt", "two")]).valid)

    def test_corrupt_unreferenced_bytes_and_truncated_archives(self):
        write_archive(self.archive, extras=[("extra.bin", b"CORRUPT-ME")], compression=zipfile.ZIP_STORED)
        original = self.archive.read_bytes()
        self.archive.write_bytes(original.replace(b"CORRUPT-ME", b"CORRUPT-XE"))
        self.assertFalse(validate_archive(self.archive).valid)
        for length in (0, 1, 20, len(original) - 10):
            self.archive.write_bytes(original[:length])
            with self.subTest(length=length):
                self.assertFalse(validate_archive(self.archive).valid)

    def test_forged_uncompressed_length_cannot_hide_payload(self):
        write_archive(self.archive, extras=[("extra.bin", b"abc" + b"x" * 100000)])
        raw = bytearray(self.archive.read_bytes())
        with zipfile.ZipFile(self.archive) as archive:
            header = archive.getinfo("extra.bin").header_offset
        # Both headers claim only the prefix, with a matching CRC of that prefix.
        struct.pack_into("<I", raw, header + 14, zlib.crc32(b"abc"))
        struct.pack_into("<I", raw, header + 22, 3)
        offset = raw.index(b"PK\x01\x02")
        while raw[offset:offset + 4] == b"PK\x01\x02":
            length, extra, comment = struct.unpack_from("<HHH", raw, offset + 28)
            if raw[offset + 46:offset + 46 + length] == b"extra.bin":
                struct.pack_into("<I", raw, offset + 16, zlib.crc32(b"abc"))
                struct.pack_into("<I", raw, offset + 24, 3)
                break
            offset += 46 + length + extra + comment
        self.archive.write_bytes(raw)
        self.assertFalse(validate_archive(self.archive).valid)
        limited = validate_archive(self.archive, Limits(max_entry_size=2048))
        self.assertEqual(limited.status, "capacity_exceeded")

    def test_deflate_trailing_garbage_at_chunk_boundary_terminates(self):
        content = b"x" * 65537
        compressor = zlib.compressobj(wbits=-15)
        compressed = compressor.compress(content) + compressor.flush() + b"garbage"
        entry = zipfile.ZipInfo("extra.bin")
        write_archive(self.archive, extras=[(entry, compressed)])
        raw = bytearray(self.archive.read_bytes())
        with zipfile.ZipFile(self.archive) as archive:
            header = archive.getinfo("extra.bin").header_offset
            central = archive.start_dir
        struct.pack_into("<H", raw, header + 8, zipfile.ZIP_DEFLATED)
        struct.pack_into("<I", raw, header + 14, zlib.crc32(content))
        struct.pack_into("<I", raw, header + 22, len(content))
        while raw[central:central + 4] == b"PK\x01\x02":
            length, extra, comment = struct.unpack_from("<HHH", raw, central + 28)
            if raw[central + 46:central + 46 + length] == b"extra.bin":
                struct.pack_into("<H", raw, central + 10, zipfile.ZIP_DEFLATED)
                struct.pack_into("<I", raw, central + 16, zlib.crc32(content))
                struct.pack_into("<I", raw, central + 24, len(content))
                break
            central += 46 + length + extra + comment
        self.archive.write_bytes(raw)
        # Bound the original failure without letting the in-process test hang.
        source = load_archive(self.archive, Limits())
        try:
            chunks = source.content_chunks(next(e for e in source.entries if e.path == "extra.bin"))
            with self.assertRaises(zipfile.BadZipFile):
                for _ in range(4):
                    next(chunks)
        finally:
            source.close()
        # Also guard the public API against a future infinite-loop regression.
        run = subprocess.run([sys.executable, "-c",
                              "import json,sys; from validator.oaa_validator import validate_archive; "
                              "print(json.dumps(validate_archive(sys.argv[1]).to_dict()))", str(self.archive)],
                             cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["valid"])
        self.assertIn("package.archive_readable", {item["rule_id"] for item in result["issues"]})

    def test_legacy_bzip2_extra_is_unsupported_not_invalid(self):
        for version, expected in [("0.1", "unsupported"), ("1.0", "invalid")]:
            data = records()
            for manifest in data.values():
                manifest["schema_version"] = version
            extra = zipfile.ZipInfo("extra.bin")
            extra.compress_type = zipfile.ZIP_BZIP2
            write_archive(self.archive, data, extras=[(extra, b"legacy payload")])
            with self.subTest(version=version):
                result = validate_archive(self.archive)
                self.assertEqual(result.status, expected)
                if version == "0.1":
                    self.assertIsNone(result.valid)
                    self.assertFalse(result.to_dict()["complete"])
                    self.assertNotIn("package.compression_method", {i.rule_id for i in result.issues})
                else:
                    self.assertIn("package.compression_method", {i.rule_id for i in result.issues})

    def test_version_probe_reads_only_root_and_keeps_safety_limits(self):
        data = records()
        data[".oacollection"]["schema_version"] = "0.1"
        link = zipfile.ZipInfo("unread-link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        write_archive(self.archive, data, extras=[(link, b"outside"), ("../unsafe", b"unread")])
        chunks = OaaSource.content_chunks
        reads = []

        def root_only(source, entry):
            reads.append(entry.path)
            self.assertEqual(entry.path, ".oacollection")
            return chunks(source, entry)

        with patch.object(OaaSource, "content_chunks", root_only):
            result = validate_archive(self.archive)
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(reads, [".oacollection"])
        with patch.object(OaaSource, "content_chunks", side_effect=AssertionError("read beyond capacity")):
            result = validate_archive(self.archive, Limits(max_uncompressed_size=1))
        self.assertEqual(result.status, "capacity_exceeded")

    def test_bzip2_root_probe_is_bounded_and_version_specific(self):
        for version in ("0.1", "1.0"):
            data = records()
            for manifest in data.values():
                manifest["schema_version"] = version
            data[".oacollection"]["extra"] = "x" * 65537
            write_archive(self.archive, data, compression=zipfile.ZIP_BZIP2)
            with self.subTest(version=version):
                result = validate_archive(self.archive)
                self.assertEqual(result.status, "unsupported" if version == "0.1" else "invalid")
                limited = validate_archive(self.archive, Limits(max_manifest_size=1024))
                self.assertEqual(limited.status, "capacity_exceeded")

    def test_unreadable_root_compression_is_unsupported_without_decompression(self):
        write_archive(self.archive, compression=zipfile.ZIP_LZMA)
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("unbounded codec")):
            result = validate_archive(self.archive)
        self.assertEqual(result.status, "unsupported")
        self.assertIsNone(result.valid)
        self.assertFalse(result.to_dict()["complete"])

    def test_clean_deflate_chunk_boundaries_remain_valid(self):
        for size in (0, 65535, 65536, 65537, 131072):
            with self.subTest(size=size):
                self.assertTrue(self.validate(extras=[("extra.bin", b"x" * size)]).valid)

    def test_private_values_no_network_extraction_or_source_mutation(self):
        data = records()
        art = data["pieces/a/.oaartwork"]
        art["public_metadata"] = {"is_public": True}
        art["private_metadata"] = {"personal_notes": "DO-NOT-PUBLISH-THIS-VALUE",
                                   "extensions": {"com.example": {"secret": "DO-NOT-PUBLISH-THIS-VALUE"}}}
        art["external_links"] = [{"provider": "com.example", "id": "x", "url": "https://example.org/not-fetched"}]
        write_archive(self.archive, data, extras=[("private-supporting.txt", "DO-NOT-PUBLISH-THIS-VALUE")])
        before = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with patch("socket.socket", side_effect=AssertionError("network access")), \
             patch.object(zipfile.ZipFile, "extractall", side_effect=AssertionError("extraction")), \
             patch.object(zipfile.ZipFile, "extract", side_effect=AssertionError("extraction")), \
             patch("subprocess.Popen", side_effect=AssertionError("opening media")):
            result = validate_archive(self.archive)
        self.assertTrue(result.valid)
        self.assertNotIn("DO-NOT-PUBLISH-THIS-VALUE", json.dumps(result.to_dict()))
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(), before)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.archive])

    def test_cli_exit_codes_distinguish_incomplete_and_invalid(self):
        write_archive(self.archive)
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(["validate", str(self.archive), "--json"]), 0)
            self.assertEqual(main(["validate", str(self.archive), "--max-entries", "1"]), 3)
            write_archive(self.archive, {".oacollection": "not-json"})
            self.assertEqual(main(["validate", str(self.archive)]), 1)

    def test_candidate_writer_preserves_bytes_and_refuses_overwrite(self):
        from tools.prepare_candidate import write_example
        result = write_example("minimal", self.archive)
        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["complete"])
        with self.assertRaises(FileExistsError):
            write_example("minimal", self.archive)

    def test_duplicate_references_do_not_repeat_manifest_processing(self):
        from validator.oaa_validator import validator as implementation
        data = records()
        data[".oacollection"]["artworks"] *= 100
        with patch.object(implementation, "parse_manifest", wraps=implementation.parse_manifest) as parse, \
             patch.object(implementation, "validate_artwork", wraps=implementation.validate_artwork) as interpret:
            self.assertFalse(self.validate(data).valid)
        self.assertEqual(parse.call_count, 3)
        self.assertEqual(interpret.call_count, 1)


if __name__ == "__main__":
    unittest.main()
