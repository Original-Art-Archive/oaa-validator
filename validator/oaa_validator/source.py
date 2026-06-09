from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import zipfile


@dataclass(frozen=True)
class SourceEntry:
    path: str
    is_dir: bool = False
    file_size: int = 0
    compress_size: int = 0
    compress_type: int | None = None
    flag_bits: int = 0

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
    archive_error: str | None = None

    def file_paths(self) -> set[str]:
        return {entry.path for entry in self.entries if not entry.is_dir}

    def has_file(self, path: str) -> bool:
        return path in self.file_paths()

    def read_bytes(self, path: str) -> bytes | None:
        if self.mode == "directory":
            target = self.root / Path(path)
            if not target.is_file():
                return None
            return target.read_bytes()
        try:
            with zipfile.ZipFile(self.root, "r") as archive:
                with archive.open(path, "r") as handle:
                    return handle.read()
        except (KeyError, RuntimeError, NotImplementedError, zipfile.BadZipFile):
            return None


def load_directory(path: Path) -> OaaSource:
    entries: list[SourceEntry] = []
    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(path).as_posix()
        entries.append(SourceEntry(path=rel, file_size=item.stat().st_size))
    return OaaSource(root=path, mode="directory", entries=entries, duplicate_paths=set())


def load_archive(path: Path) -> OaaSource:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
    except zipfile.BadZipFile as exc:
        return OaaSource(root=path, mode="archive", entries=[], duplicate_paths=set(), archive_error=str(exc))

    entries: list[SourceEntry] = []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for info in infos:
        if info.filename in seen:
            duplicates.add(info.filename)
        seen.add(info.filename)
        entries.append(
            SourceEntry(
                path=info.filename,
                is_dir=info.is_dir(),
                file_size=info.file_size,
                compress_size=info.compress_size,
                compress_type=info.compress_type,
                flag_bits=info.flag_bits,
            )
        )
    return OaaSource(root=path, mode="archive", entries=entries, duplicate_paths=duplicates)
