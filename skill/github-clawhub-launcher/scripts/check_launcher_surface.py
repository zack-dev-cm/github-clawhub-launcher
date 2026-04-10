#!/usr/bin/env python3
"""Validate a local GitHub + ClawHub release surface from a launch manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def add_issue(bucket: list[dict[str, str]], kind: str, message: str) -> None:
    bucket.append({"kind": kind, "message": message})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON file.")
    parser.add_argument("--repo-root", default=".", help="Local repo root to validate.")
    parser.add_argument("--out", required=True, help="Output JSON report.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = load_json(manifest_path)
    github = payload.get("github") or {}
    clawhub = payload.get("clawhub") or {}
    validation = payload.get("validation") or {}

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    repo_name = str(github.get("repo_name") or "").strip()
    if not repo_name or not REPO_RE.fullmatch(repo_name):
        add_issue(errors, "repo_name", "GitHub repo_name is missing or contains invalid characters.")

    slug = str(clawhub.get("slug") or "").strip()
    if not slug or not SLUG_RE.fullmatch(slug):
        add_issue(errors, "slug", "ClawHub slug is missing or must be lowercase letters, numbers, or hyphens.")

    version = str(clawhub.get("version") or "").strip()
    if not SEMVER_RE.fullmatch(version):
        add_issue(errors, "version", "Version must be semver, for example 1.0.0.")

    description = str(github.get("description") or "").strip()
    if len(description) < 40:
        add_issue(warnings, "description", "GitHub description is very short for a public repo.")

    changelog = str(clawhub.get("changelog") or "").strip()
    if not changelog:
        add_issue(warnings, "changelog", "ClawHub changelog is empty.")

    skill_path = str(clawhub.get("skill_path") or "").strip()
    if not skill_path:
        add_issue(errors, "skill_path", "ClawHub skill_path is missing.")

    for rel_path in validation.get("required_paths") or []:
        candidate = repo_root / str(rel_path)
        if not candidate.exists():
            add_issue(errors, "missing_path", f"Required path is missing: {rel_path}")

    for rel_path in validation.get("recommended_paths") or []:
        candidate = repo_root / str(rel_path)
        if not candidate.exists():
            add_issue(warnings, "missing_recommended_path", f"Recommended path is missing: {rel_path}")

    topics = github.get("topics") or []
    tags = clawhub.get("tags") or []
    if not topics:
        add_issue(warnings, "topics", "No GitHub topics configured.")
    if not tags:
        add_issue(warnings, "tags", "No ClawHub tags configured.")

    report = {
        "schema_version": "1.0",
        "manifest_path": str(manifest_path),
        "repo_root": str(repo_root),
        "status": "publish-ready" if not errors else "needs-fix",
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }

    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

