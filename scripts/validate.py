#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate portable skill packages and local Markdown links without network access."""

import argparse
import re
from collections import Counter
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt

MARKDOWN = MarkdownIt("commonmark")
# Inspect rejected URI schemes as data too; this parser never renders or fetches links.
MARKDOWN.validateLink = lambda _url: True


def markdown_links(text):
    for token in MARKDOWN.parse(text):
        for child in token.children or []:
            if child.type == "link_open":
                yield child.attrGet("href")
            elif child.type == "image":
                yield child.attrGet("src")


def prose_lines(text):
    """Exclude fenced examples so their illustrative paths are not treated as inputs."""
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not suffix.strip():
                fence = None
            continue
        if fence is None:
            yield line
    if fence:
        raise ValueError("unclosed Markdown fence")


def validate(root):
    root = Path(root).resolve()
    errors = []
    entries = sorted(root.glob("*/SKILL.md"))
    for directory in root.iterdir():
        if directory.is_dir() and not directory.name.startswith("."):
            if not (directory / "SKILL.md").exists() and any(
                (directory / marker).exists() for marker in ("references", "agents", "assets")
            ):
                errors.append(f"{directory.name}: missing SKILL.md entrypoint")
    if not entries:
        return errors + ["No skill entrypoints found"]
    for entry in entries:
        package = entry.parent
        try:
            text = entry.read_text(encoding="utf-8")
            match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
            if not match:
                raise ValueError("missing YAML frontmatter")
            meta = yaml.safe_load(match.group(1))
            if not isinstance(meta, dict):
                raise ValueError("frontmatter must be a mapping")
            allowed = {"name", "description", "license", "allowed-tools", "metadata"}
            if meta.keys() - allowed:
                raise ValueError(
                    "unsupported frontmatter fields: " + ", ".join(sorted(meta.keys() - allowed))
                )
            if meta.get("name") != package.name:
                raise ValueError("skill name must match its directory")
            if (
                not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", package.name)
                or len(package.name) > 64
            ):
                raise ValueError("invalid skill name")
            description = meta.get("description")
            if (
                not isinstance(description, str)
                or not description.strip()
                or len(description) > 1024
            ):
                raise ValueError("description must be a nonempty string of at most 1024 characters")
            if "<" in description or ">" in description:
                raise ValueError("description must not contain angle brackets")
            if meta.get("license") != "Apache-2.0":
                raise ValueError("skill license must declare Apache-2.0")
            if any(
                re.fullmatch(r"\s*\[TODO:[^\n]*\]\s*", line)
                for line in prose_lines(text[match.end() :])
            ):
                raise ValueError("unfinished skill scaffold")
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{entry.relative_to(root)}: {exc}")
        for filename in ("LICENSE", "NOTICE"):
            if not (package / filename).is_file():
                errors.append(f"{package.name}: missing {filename} for standalone distribution")
        license_path = package / "LICENSE"
        if license_path.is_file() and (root / "LICENSE").is_file():
            actual = license_path.read_text(encoding="utf-8").strip()
            expected = (root / "LICENSE").read_text(encoding="utf-8").strip()
            if actual != expected:
                errors.append(f"{package.name}: LICENSE differs from repository license")
        ui = package / "agents/openai.yaml"
        if ui.exists():
            try:
                config = yaml.safe_load(ui.read_text(encoding="utf-8"))
                if not isinstance(config, dict):
                    raise ValueError("UI metadata must be a mapping")
                interface = config["interface"]
                if not isinstance(interface, dict) or any(
                    not isinstance(interface.get(field), str)
                    for field in ("default_prompt", "short_description")
                ):
                    raise ValueError("UI prompt and short description must be strings")
                if f"${package.name}" not in interface["default_prompt"]:
                    raise ValueError("default_prompt must mention the skill")
                if not 25 <= len(interface["short_description"]) <= 64:
                    raise ValueError("short_description must have 25-64 characters")
                policy = config.get("policy", {})
                if not isinstance(policy, dict):
                    raise ValueError("UI policy must be a mapping")
                if policy.get("allow_implicit_invocation", True) is not True:
                    raise ValueError("implicit invocation unexpectedly disabled")
            except (ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
                errors.append(f"{ui.relative_to(root)}: {exc}")
    for document in sorted(root.rglob("*.md")):
        relative = document.relative_to(root)
        if any(part.startswith(".") and part != ".github" for part in relative.parts):
            continue
        package = next(
            (entry.parent for entry in entries if document.is_relative_to(entry.parent)), None
        )
        try:
            lines = list(prose_lines(document.read_text(encoding="utf-8")))
        except ValueError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        anchors = re.findall(r'<a\s+id="([^"]+)"', "\n".join(lines))
        for anchor, count in Counter(anchors).items():
            if count > 1:
                errors.append(f"{relative}: duplicate anchor: {anchor}")
        for destination in markdown_links(document.read_text(encoding="utf-8")):
            parsed = urlsplit(destination)
            path = unquote(parsed.path)
            if (
                parsed.scheme == "file"
                or PureWindowsPath(destination).drive
                or (not parsed.netloc and path.startswith("/"))
            ):
                errors.append(f"{relative}: nonportable machine path: {destination}")
                continue
            if parsed.scheme or parsed.netloc:
                continue
            target = (document.parent / path).resolve() if path else document
            if not target.is_relative_to(package or root):
                errors.append(f"{relative}: link escapes skill/repository: {destination}")
            elif not target.exists():
                errors.append(f"{relative}: missing link target: {destination}")
            elif re.fullmatch(r"(?:exp-\d+|r-pc\d+(?:-\d+)?)", parsed.fragment):
                if not target.is_file() or f'id="{parsed.fragment}"' not in target.read_text(
                    encoding="utf-8"
                ):
                    errors.append(f"{relative}: missing explicit anchor: {destination}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"Validation failed: {len(errors)} error(s)")
        return 1
    print(
        f"PASS: {len(list(args.root.glob('*/SKILL.md')))} skill packages; YAML, distribution files, fences and local link targets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
