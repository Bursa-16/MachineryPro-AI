"""Catalog the pre-existing Machinery AI source material (READ-ONLY).

Walks the source locations recorded in Stage 0 discovery - ``Machinery_Article/``,
``Progamlar/`` and loose files in the workspace root - and writes a SHA-256
inventory with duplicate flags to ``data/literature_catalog.csv``.

Guarantees:
    * No source file is modified, moved or deleted.
    * Project-generated directories (backend/, docs/, scripts/, ...) are
      excluded: this catalog describes PRE-EXISTING material only.

Usage:
    python scripts/catalog_literature.py [--root PATH]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

COPY_SUFFIX_RE = re.compile(r"\(\d+\)$")

# Cache/VCS junk that is never cataloged.
EXCLUDED_DIR_NAMES = {
    "__pycache__", ".git", ".hg", ".svn", ".venv", "venv", "env",
    "node_modules", ".idea", ".vscode", ".pytest_cache", ".ruff_cache",
}

# Directories created by the Machinery AI project itself (Stage 1+).
PROJECT_DIRS = {"backend", "frontend", "data", "docs", "scripts", "config", "tests"}

# Files the project creates at the workspace root (also not pre-existing material).
PROJECT_ROOT_FILES = {"README.md", "pyproject.toml", ".gitignore"}
CSV_COLUMNS = [
    "relative_path",
    "name",
    "extension",
    "size_bytes",
    "sha256",
    "mtime_utc",
    "copy_suffix",
    "duplicate_of",
]


def iter_source_files(root: Path):
    """Yield pre-existing source files under *root* (read-only walk)."""
    for entry in sorted(root.iterdir()):
        if entry.is_file():
            if entry.name not in PROJECT_ROOT_FILES:
                yield entry
        elif (
            entry.is_dir()
            and entry.name not in PROJECT_DIRS
            and entry.name not in EXCLUDED_DIR_NAMES
        ):
            for path in sorted(entry.rglob("*")):
                if path.is_file() and not EXCLUDED_DIR_NAMES.intersection(path.parts):
                    yield path


def sha256_of(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    first_seen_by_hash: dict[str, str] = {}
    processed = 0

    for path in iter_source_files(root):
        stat = path.stat()
        digest = sha256_of(path)
        rel = path.relative_to(root).as_posix()

        duplicate_of = ""
        if digest in first_seen_by_hash:
            duplicate_of = first_seen_by_hash[digest]
        else:
            first_seen_by_hash[digest] = rel

        rows.append(
            {
                "relative_path": rel,
                "name": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "sha256": digest,
                "mtime_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
                "copy_suffix": bool(COPY_SUFFIX_RE.search(path.stem)),
                "duplicate_of": duplicate_of,
            }
        )

        processed += 1
        if processed % 100 == 0:
            print(f"  hashed {processed} files...", flush=True)

    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    root: Path = args.root
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}", file=sys.stderr)
        return 2

    out_path = root / "data" / "literature_catalog.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Cataloging source material under: {root} (read-only)")
    rows = build_rows(root)

    # utf-8-sig so Excel renders Turkish filenames correctly.
    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    total_bytes = sum(int(r["size_bytes"]) for r in rows)
    dup_rows = [r for r in rows if r["duplicate_of"]]
    suffix_copies = sum(1 for r in rows if r["copy_suffix"])
    dup_group_count = len({str(r["sha256"]) for r in dup_rows})

    by_ext: dict[str, int] = {}
    for r in rows:
        ext = str(r["extension"]) or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1

    print("\n=== Catalog summary ===")
    print(f"Files cataloged : {len(rows)}")
    print(f"Total bytes     : {total_bytes:,}")
    print(
        "By extension    : "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_ext.items(), key=lambda kv: -kv[1]))
    )
    print(f"Exact duplicates: {len(dup_rows)} redundant copies in {dup_group_count} groups")
    print(f"'(n)' suffixed  : {suffix_copies}")
    print(f"Wasted bytes    : {sum(int(r['size_bytes']) for r in dup_rows):,}")
    print(f"\nWritten         : {out_path}")
    print("No source files were modified, moved or deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
