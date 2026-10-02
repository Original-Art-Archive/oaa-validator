# SPDX-License-Identifier: MIT
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import bz2
import os
import re
import stat
import struct
import zipfile
import zlib

from .model import Limits


class CapacityExceeded(ValueError):
    pass


class UnsupportedCompression(ValueError):
    pass


@dataclass(frozen=True)
class SourceEntry:
    path: str
    is_dir: bool = False
    file_size: int = 0
    compress_size: int = 0
    compress_type: int | None = None
    flag_bits: int = 0
    unsafe_type: bool = False

    @property
    def encrypted(self) -> bool:
        return bool(self.flag_bits & 0x1)

    @property
    def utf8_flag(self) -> bool:
        return bool(self.flag_bits & 0x800)


@dataclass
class OaaSource:
    root: Path
    mode: str
    entries: list[SourceEntry]
    duplicate_paths: set[str]
    archive: zipfile.ZipFile | None = None
    limits: Limits = field(default_factory=Limits)
    _index: dict[str, SourceEntry] = field(init=False)

    def __post_init__(self):
        self._index = {entry.path: entry for entry in self.entries}

    def close(self):
        if self.archive is not None:
            self.archive.close()

    def has_file(self, path: str) -> bool:
        entry = self._index.get(path)
        return entry is not None and not entry.is_dir

    def size(self, path: str) -> int:
        return self._index[path].file_size

    @contextmanager
    def open_file(self, path: str):
        # Never resolve unvalidated input, even during recovery.
        if (path.startswith("/") or "\\" in path or "\x00" in path
                or re.match(r"^[A-Za-z]:", path)
                or any(part in {"", ".", ".."} for part in path.split("/"))):
            raise ValueError("Unsafe source path")
        if not self.has_file(path) or self._index[path].unsafe_type:
            raise ValueError("Not a regular source file")
        if self.mode == "directory":
            target = self.root
            for part in path.split("/"):
                target = target / part
                info = target.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("Filesystem redirection is not supported")
            if not target.resolve().is_relative_to(self.root.resolve()):
                raise ValueError("Source escaped its root")
            with target.open("rb") as handle:
                yield handle
        else:
            with self.archive.open(path, "r") as handle:
                yield handle

    def read_bytes(self, path: str, max_bytes: int | None = None) -> bytes | None:
        if not self.has_file(path):
            return None
        limit = self.limits.max_manifest_size if max_bytes is None else max_bytes
        limit = min(limit, self.limits.max_entry_size, self.limits.max_uncompressed_size)
        if self.size(path) > limit:
            raise CapacityExceeded("Content exceeds the configured bounded-read limit")
        data = bytearray()
        for chunk in self.content_chunks(self._index[path]):
            if len(data) + len(chunk) > limit:
                raise CapacityExceeded("Content exceeds the configured bounded-read limit")
            data.extend(chunk)
        if len(data) != self.size(path):
            raise ValueError("Entry content length differs from its declared length")
        if self.archive is not None and zlib.crc32(data) != self.archive.getinfo(path).CRC:
            raise zipfile.BadZipFile("Entry CRC differs from its content")
        return bytes(data)

    def verify_content(self) -> None:
        total = 0
        for entry in self.entries:
            if entry.is_dir:
                continue
            count = 0
            crc = 0
            for chunk in self.content_chunks(entry):
                count += len(chunk)
                total += len(chunk)
                if count > self.limits.max_entry_size or total > self.limits.max_uncompressed_size:
                    raise CapacityExceeded("Actual decompressed content exceeds configured limits")
                crc = zlib.crc32(chunk, crc)
            if count != entry.file_size:
                raise ValueError("Entry content length differs from its declared length")
            if self.archive is not None and crc != self.archive.getinfo(entry.path).CRC:
                raise zipfile.BadZipFile("Entry CRC differs from its content")

    def content_chunks(self, entry):
        if self.mode == "directory":
            with self.open_file(entry.path) as handle:
                while chunk := handle.read(65536):
                    yield chunk
            return
        if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2):
            raise UnsupportedCompression("Cannot safely read the root manifest compression method")
        # ZipExtFile truncates output to the declared file_size. Check the raw
        # compressed stream independently so a forged length cannot hide data.
        with self.open_file(entry.path):
            pass  # stdlib checks local names, flags, and overlapping entries.
        info = self.archive.getinfo(entry.path)
        handle = self.archive.fp
        handle.seek(info.header_offset)
        header = handle.read(30)
        if len(header) != 30 or header[:4] != b"PK\x03\x04":
            raise zipfile.BadZipFile("Invalid local file header")
        name_size, extra_size = struct.unpack_from("<HH", header, 26)
        handle.seek(info.header_offset + 30 + name_size + extra_size)
        deflate = entry.compress_type == zipfile.ZIP_DEFLATED
        # BZIP2 is bootstrap-only support for legacy version detection; the 1.0
        # validator rejects it before reading any remaining payloads.
        decoder = zlib.decompressobj(-15) if deflate else (
            bz2.BZ2Decompressor() if entry.compress_type == zipfile.ZIP_BZIP2 else None)
        remaining = info.compress_size
        while remaining:
            raw = handle.read(min(65536, remaining))
            if not raw:
                raise zipfile.BadZipFile("Truncated compressed stream")
            remaining -= len(raw)
            if decoder is None:
                yield raw
                continue
            decoded = decoder.decompress(raw, 65536)
            while True:
                # Never feed input back after EOF: unconsumed_tail may persist
                # while unused_data grows and the decoder produces empty chunks.
                if decoder.unused_data or (decoder.eof and remaining):
                    raise zipfile.BadZipFile("Trailing data after compressed stream")
                if decoded:
                    yield decoded
                if decoder.eof:
                    break
                if deflate:
                    if not decoded and not decoder.unconsumed_tail:
                        break
                    pending = decoder.unconsumed_tail
                else:
                    if decoder.needs_input:
                        break
                    pending = b""
                decoded = decoder.decompress(pending, 65536)
        if decoder is not None and not decoder.eof:
            raise zipfile.BadZipFile("Incomplete compressed stream")


def load_directory(path: Path, limits: Limits) -> OaaSource:
    if not path.is_dir() or path.is_symlink() or path.is_junction():
        raise OSError("Input is not a regular directory")
    entries: list[SourceEntry] = []
    def fail_unreadable(error):
        raise error
    for current, dirs, files in os.walk(path, followlinks=False, onerror=fail_unreadable):
        for name in sorted(dirs + files):
            item = Path(current) / name
            info = item.lstat()
            redirect = stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            is_dir = stat.S_ISDIR(info.st_mode)
            unsafe = redirect or not (is_dir or stat.S_ISREG(info.st_mode))
            if unsafe and name in dirs:
                dirs.remove(name)
            entries.append(SourceEntry(item.relative_to(path).as_posix() + ("/" if is_dir else ""),
                                       is_dir=is_dir, file_size=0 if is_dir else info.st_size, unsafe_type=unsafe))
            if len(entries) > limits.max_entries:
                raise CapacityExceeded("Directory entry count exceeds configured limit")
    return OaaSource(path, "directory", entries, set(), limits=limits)


def load_archive(path: Path, limits: Limits) -> OaaSource:
    if path.stat().st_size > limits.max_archive_size:
        raise CapacityExceeded("Archive exceeds configured archive size limit")
    # ponytail: bounded stdlib ZIP64 end-record reader is private; keep ZIP64
    # regression coverage when upgrading the supported Python runtime.
    with path.open("rb") as handle:
        end = zipfile._EndRecData(handle)
    if end is None:
        raise zipfile.BadZipFile("Missing archive end record")
    if end[zipfile._ECD_ENTRIES_TOTAL] > limits.max_entries or end[zipfile._ECD_SIZE] > limits.max_directory_size:
        raise CapacityExceeded("Archive directory metadata exceeds configured limits")
    archive = zipfile.ZipFile(path, "r")
    try:
        entries: list[SourceEntry] = []
        seen: set[str] = set()
        duplicates: set[str] = set()
        for info in archive.infolist():
            if len(entries) >= limits.max_entries:
                raise CapacityExceeded("Archive entry count exceeds configured limit")
            name = info.orig_filename
            if name in seen:
                duplicates.add(name)
            seen.add(name)
            kind = stat.S_IFMT(info.external_attr >> 16) if info.create_system == 3 else 0
            is_dir = info.is_dir()
            unsafe = kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not is_dir) or (kind == stat.S_IFREG and is_dir)
            entries.append(SourceEntry(name, is_dir, info.file_size, info.compress_size,
                                       info.compress_type, info.flag_bits, unsafe))
        return OaaSource(path, "archive", entries, duplicates, archive, limits)
    except Exception:
        archive.close()
        raise
