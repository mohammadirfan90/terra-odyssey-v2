"""Utility script to package the entire Earth System Trend Detective codebase into a clean ZIP archive.

Excludes ephemeral directories (node_modules, .next, __pycache__, .pytest_cache) and builds.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path


def create_codebase_zip(output_filename: str = "earth-system-trend-detective.zip") -> Path:
    root_dir = Path(__file__).resolve().parent
    zip_path = root_dir / output_filename

    exclude_dirs = {
        "node_modules",
        ".next",
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".turbo",
        ".vscode",
        ".idea",
    }

    exclude_exts = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".zip",
    }

    file_count = 0
    total_uncompressed_bytes = 0

    print(f"Creating archive at: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for current_dir, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".next")]
            rel_dir = Path(current_dir).relative_to(root_dir)

            for file in sorted(files):
                file_path = Path(current_dir) / file
                if file_path.suffix in exclude_exts or file == output_filename:
                    continue

                archive_name = rel_dir / file if str(rel_dir) != "." else Path(file)
                zf.write(file_path, arcname=str(archive_name).replace("\\", "/"))
                file_count += 1
                total_uncompressed_bytes += file_path.stat().st_size

    zip_size = zip_path.stat().st_size
    print(f"Archived {file_count} files successfully.")
    print(f"Uncompressed: {total_uncompressed_bytes / (1024 * 1024):.2f} MB")
    print(f"Compressed:   {zip_size / (1024 * 1024):.2f} MB")
    return zip_path


if __name__ == "__main__":
    create_codebase_zip()
