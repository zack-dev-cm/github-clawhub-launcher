#!/usr/bin/env python3
"""Render GitHub and ClawHub publish commands from a launch manifest."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def q(value: str) -> str:
    return shlex.quote(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON file.")
    parser.add_argument("--repo-root", default=".", help="Local repo root.")
    parser.add_argument("--out", required=True, help="Output markdown file.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    github = manifest.get("github") or {}
    clawhub = manifest.get("clawhub") or {}
    release = manifest.get("release") or {}

    owner = str(github.get("owner") or "").strip()
    repo_name = str(github.get("repo_name") or "").strip()
    description = str(github.get("description") or "").strip()
    release_tag = str(github.get("release_tag") or f"v{clawhub.get('version', '')}").strip()
    release_title = str(release.get("title") or f"{clawhub.get('name', '')} {clawhub.get('version', '')}").strip()
    skill_path = str(clawhub.get("skill_path") or "").strip()
    slug = str(clawhub.get("slug") or "").strip()
    name = str(clawhub.get("name") or "").strip()
    version = str(clawhub.get("version") or "").strip()
    changelog = str(clawhub.get("changelog") or "").strip()
    topics = [str(item) for item in github.get("topics") or [] if str(item).strip()]
    tags = [str(item) for item in clawhub.get("tags") or [] if str(item).strip()]

    release_notes_path = f"/tmp/{repo_name}-release.md"
    repo_spec = f"{owner}/{repo_name}" if owner else repo_name
    skill_abs_path = str((repo_root / skill_path).resolve())

    lines = [
        "# Launch Commands",
        "",
        "## Validation",
        "```bash",
        f"python3 {q(str((repo_root / skill_path / 'scripts' / 'check_launcher_surface.py').resolve()))} \\",
        f"  --manifest {q(str(manifest_path))} \\",
        f"  --repo-root {q(str(repo_root))} \\",
        f"  --out {q('/tmp/' + repo_name + '-check.json')}",
        "```",
        "",
        "## GitHub",
        "```bash",
        "git add .",
        f"git commit -m {q(f'Initial public release: {name} v{version}')}",
        f"gh repo create {q(repo_spec)} --public --source {q(str(repo_root))} --remote origin --description {q(description)}",
        "git push -u origin main",
    ]

    if topics:
        topic_flags = " ".join(f"-F {q('names[]=' + topic)}" for topic in topics)
        lines.append(
            "gh api "
            + q(f"repos/{repo_spec}/topics")
            + " -X PUT -H "
            + q("Accept: application/vnd.github+json")
            + " "
            + topic_flags
        )

    lines.extend(
        [
            f"python3 {q(str((repo_root / skill_path / 'scripts' / 'render_release_notes.py').resolve()))} \\",
            f"  --manifest {q(str(manifest_path))} \\",
            f"  --out {q(release_notes_path)}",
            f"gh release create {q(release_tag)} --repo {q(repo_spec)} --title {q(release_title)} --notes-file {q(release_notes_path)}",
            "```",
            "",
            "## ClawHub",
            "```bash",
            "npx --yes clawhub publish "
            + q(skill_abs_path)
            + " --slug "
            + q(slug)
            + " --name "
            + q(name)
            + " --version "
            + q(version)
            + " --changelog "
            + q(changelog)
            + (" --tags " + q(",".join(tags)) if tags else ""),
            "```",
            "",
            "## Notes",
            "- Run `publish-guard` before these commands if the public surface changed recently.",
            "- Review the generated release notes before creating the GitHub release.",
        ]
    )

    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
