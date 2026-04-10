#!/usr/bin/env python3
"""Create a machine-readable launch manifest for a GitHub repo and ClawHub package."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Output JSON file.")
    parser.add_argument("--repo-name", required=True, help="GitHub repository name.")
    parser.add_argument("--skill-path", required=True, help="Local skill path relative to the repo root.")
    parser.add_argument("--slug", required=True, help="ClawHub slug.")
    parser.add_argument("--version", required=True, help="Package version, for example 1.0.0.")
    parser.add_argument("--name", required=True, help="Public skill or package name.")
    parser.add_argument("--description", required=True, help="One-line public description.")
    parser.add_argument("--github-owner", default="zack-dev-cm", help="GitHub owner or org.")
    parser.add_argument("--branch", default="main", help="GitHub default branch.")
    parser.add_argument("--homepage", default="", help="Optional homepage URL.")
    parser.add_argument("--changelog", default="Initial public release.", help="Short ClawHub changelog line.")
    parser.add_argument("--summary", default="", help="Optional release summary paragraph.")
    parser.add_argument("--topic", action="append", default=[], help="Repeatable GitHub topic.")
    parser.add_argument("--tag", action="append", default=[], help="Repeatable ClawHub tag.")
    args = parser.parse_args()

    repo_name = args.repo_name.strip()
    slug = args.slug.strip()
    version = args.version.strip()
    public_name = args.name.strip()
    description = args.description.strip()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "github": {
            "owner": args.github_owner.strip(),
            "repo_name": repo_name,
            "description": description,
            "homepage": args.homepage.strip(),
            "default_branch": args.branch.strip() or "main",
            "topics": dedupe(args.topic),
            "release_tag": f"v{version}",
        },
        "clawhub": {
            "skill_path": args.skill_path.strip(),
            "slug": slug,
            "name": public_name,
            "version": version,
            "changelog": args.changelog.strip(),
            "tags": dedupe(args.tag),
        },
        "release": {
            "title": f"{public_name} v{version}",
            "summary": args.summary.strip(),
            "highlights": [],
        },
        "validation": {
            "required_paths": [
                "README.md",
                "LICENSE",
                args.skill_path.strip(),
                f"{args.skill_path.strip()}/SKILL.md",
                f"{args.skill_path.strip()}/agents/openai.yaml",
            ],
            "recommended_paths": [
                f"{args.skill_path.strip()}/scripts",
            ],
            "status": "draft",
        },
        "notes": [],
    }

    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

