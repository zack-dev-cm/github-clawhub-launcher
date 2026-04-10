#!/usr/bin/env python3
"""Render concise GitHub release notes from a launch manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON file.")
    parser.add_argument("--out", required=True, help="Output markdown file.")
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest).expanduser().resolve())
    github = manifest.get("github") or {}
    clawhub = manifest.get("clawhub") or {}
    release = manifest.get("release") or {}

    title = str(release.get("title") or f"{clawhub.get('name', 'Release')} {clawhub.get('version', '')}").strip()
    summary = str(release.get("summary") or "").strip()

    lines = [f"# {title}", ""]
    if summary:
        lines.extend([summary, ""])

    lines.extend(
        [
            "## Highlights",
            f"- public GitHub repo: `{github.get('owner', '')}/{github.get('repo_name', '')}`",
            f"- ClawHub package: `{clawhub.get('slug', '')}@{clawhub.get('version', '')}`",
            f"- skill path: `{clawhub.get('skill_path', '')}`",
        ]
    )

    topics = github.get("topics") or []
    if topics:
        lines.append(f"- GitHub topics: `{', '.join(str(item) for item in topics)}`")

    tags = clawhub.get("tags") or []
    if tags:
        lines.append(f"- ClawHub tags: `{', '.join(str(item) for item in tags)}`")

    changelog = str(clawhub.get("changelog") or "").strip()
    if changelog:
        lines.extend(["", "## Changelog", f"- {changelog}"])

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

