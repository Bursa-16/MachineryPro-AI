"""Report exact-duplicate files in the Machinery AI source corpus (READ-ONLY).

Finds byte-identical files (same size AND same SHA-256) among the Stage 0
source material and writes ``data/dedup_report.csv``. This tool NEVER deletes,
moves or modifies anything - it only reports, so cleanup can be reviewed and
approved by a human afterwards.

Usage:
    python scripts/dedup_report.py [--root PATH] [--min-size N]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

EXCLUDED_DIR_NAMES = {
    "__pycache__", ".git", ".hg", ".svn", ".venv", "venv", "env",
    "node_modules", ".idea", ".vscode", ".pytest_cache", ".ruff_cache",
}
PROJECT_DIRS = {"backend", "frontend", "data", "docs", "scripts", "config", "tests"}
PROJECT_ROOT_FILES = {"README.md", "pyproject.toml", ".gitignore"}

CSV_COLUMNS = [
    "group_id",
    "size_bytes",
    "sha256",
    "copies_in_group",
    "relative_path",
    "is_first_copy",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="ignore duplicate candidates smaller than this many bytes",
    )
    args = parser.parse_args(argv)

    root: Path = args.root
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}", file=sys.stderr)
        return 2

    print(f"Scanning for byte-identical files under: {root} (read-only)")

    # Fast path: only hash files whose byte-size collides with another file.
    by_size: dict[int, list[Path]] = defaultdict(list)
    all_files = list(iter_source_files(root))
    for path in all_files:
        by_size[path.stat().st_size].append(path)

    dup_groups: list[tuple[str, int, list[Path]]] = []
    for size, same_size_files in sorted(by_size.items(), reverse=True):
        if size < args.min_size or len(same_size_files) < 2:
            continue
        by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in same_size_files:
            by_hash[sha256_of(path)].append(path)
        for digest, group in sorted(by_hash.items()):
            if len(group) > 1:
                dup_groups.append((digest, size, sorted(group)))

    out_path = root / "data" / "dedup_report.csv"
    rows: list[dict[str, object]] = []
    for group_id, (digest, size, group) in enumerate(dup_groups, start=1):
        for index, path in enumerate(group):
            rows.append(
                {
                    "group_id": group_id,
                    "size_bytes": size,
                    "sha256": digest,
                    "copies_in_group": len(group),
                    "relative_path": path.relative_to(root).as_posix(),
                    "is_first_copy": index == 0,
                }
            )

    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    wasted_bytes = sum(size * (len(group) - 1) for _, size, group in dup_groups)

    print("\n=== Duplicate report ===")
    print(f"Files scanned        : {len(all_files)}")
    print(f"Duplicate groups     : {len(dup_groups)}")
    print(f"Redundant copies     : {sum(len(g) - 1 for _, _, g in dup_groups)}")
    print(f"Recoverable bytes    : {wasted_bytes:,}")
    print("\nTop groups by wasted space:")
    for group_id, (digest, size, group) in sorted(
        enumerate(dup_groups, start=1), key=lambda item: -(item[1][1] * (len(item[1][2]) - 1))
    )[:15]:
        print(
            f"  #{group_id:<3} x{len(group)}  {size:>12,} B  "
            f"e.g. {group[0].name}"
        )
    print(f"\nWritten              : {out_path}")
    print("No files were modified, moved or deleted (report only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
