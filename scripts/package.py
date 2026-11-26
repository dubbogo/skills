#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build each skill zip and validate its extracted contents independently."""

import argparse
import hashlib
import tempfile
import zipfile
from pathlib import Path

try:
    from scripts.validate import validate
except ModuleNotFoundError:  # Support `python scripts/package.py` from the clone root.
    from validate import validate


def build_packages(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    errors = validate(root)
    if errors:
        raise ValueError("Invalid source packages:\n" + "\n".join(errors))
    output.mkdir(parents=True, exist_ok=True)
    archives = []
    checksums = []
    for entry in sorted(root.glob("*/SKILL.md")):
        package = entry.parent
        if output.is_relative_to(package):
            raise ValueError("Output must be outside skill directories")
        files = sorted(path for path in package.rglob("*") if path.is_file())
        if any(path.is_symlink() for path in package.rglob("*")):
            raise ValueError(f"{package.name}: distribution must not contain symlinks")
        archive_path = output / f"{package.name}.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(root).as_posix())
        with tempfile.TemporaryDirectory(prefix="skill-distribution-") as task_temp:
            extracted = Path(task_temp)
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(extracted)
                for path in files:
                    if (extracted / path.relative_to(root)).read_bytes() != path.read_bytes():
                        raise ValueError(f"{package.name}: archive changed file contents")
            errors = validate(extracted)
            if errors:
                raise ValueError("Invalid standalone archive:\n" + "\n".join(errors))
        archives.append(archive_path)
        checksums.append(
            f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {archive_path.name}"
        )
    (output / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    return archives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    for archive in build_packages(args.root, args.output_dir):
        print(f"PASS: standalone archive {archive.name}")


if __name__ == "__main__":
    main()
