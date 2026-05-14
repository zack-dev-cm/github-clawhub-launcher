#!/usr/bin/env python3
"""Review a GitHub + ClawHub launch using surface, usage, and auto-review gates."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


RISK_PATTERNS = {
    "credential_exfiltration": re.compile(
        r"\b(send|upload|post|transmit|exfiltrat\w*)\b.{0,100}"
        r"\b(secret|token|api[_ -]?key|credential|password|cookie|\.env|ssh|keychain)\b",
        re.IGNORECASE,
    ),
    "credential_probe": re.compile(
        r"\b(read|collect|scan|dump|steal|harvest)\b.{0,100}"
        r"(~/(?:\.ssh|\.aws|\.gnupg)|id_rsa|keychain|cookies?|\.env|tokens?)",
        re.IGNORECASE,
    ),
    "security_weakening": re.compile(
        r"\b(disable|bypass|weaken|turn off)\b.{0,80}"
        r"\b(auto[-_ ]?review|sandbox|approval|firewall|gatekeeper|selinux|sip|policy)\b|"
        r"\bapproval_policy\s*=\s*[\"']never[\"']",
        re.IGNORECASE,
    ),
    "destructive_action": re.compile(
        r"(rm\s+-rf\s+(?:/|\$HOME|~)|mkfs\s|dd\s+if=.*\s+of=/dev/|"
        r"chmod\s+-R\s+777\s+(?:/|\$HOME|~))",
        re.IGNORECASE,
    ),
}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".ts", ".sh", ""}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def run_surface_check(manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    script = Path(__file__).resolve().parent / "check_launcher_surface.py"
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "surface-check.json"
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--manifest",
                str(manifest_path),
                "--repo-root",
                str(repo_root),
                "--out",
                str(out_path),
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        return load_json(out_path)


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts[:-1]):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return sorted(files)


def scan_auto_review_risks(repo_root: Path, skill_path: str) -> list[dict[str, object]]:
    root = (repo_root / skill_path).resolve()
    findings: list[dict[str, object]] = []
    if not root.exists():
        return findings
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for code, pattern in RISK_PATTERNS.items():
                if pattern.search(line):
                    findings.append({"code": code, "path": rel_path, "line": line_number})
    return findings


def scan_codex_usage(
    codex_home: Path,
    tokens: list[str],
    *,
    days: int,
    max_session_bytes: int,
) -> dict[str, object]:
    sessions_root = codex_home / "sessions"
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    counts: Counter[str] = Counter()
    scanned = 0
    matched_files = 0
    if not sessions_root.exists():
        return {
            "codex_home": str(codex_home),
            "days": days,
            "session_files_scanned": 0,
            "matching_session_files": 0,
            "max_session_bytes": max_session_bytes,
            "mention_counts": {},
        }

    for path in sessions_root.rglob("*.jsonl"):
        try:
            stat = path.stat()
        except OSError:
            continue
        modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        if modified < cutoff:
            continue
        scanned += 1
        try:
            with path.open("rb") as handle:
                raw = handle.read(max_session_bytes)
        except OSError:
            continue
        text = raw.decode("utf-8", errors="ignore")
        file_matched = False
        for token in tokens:
            count = text.count(token)
            if count:
                counts[token] += count
                file_matched = True
        if file_matched:
            matched_files += 1

    return {
        "codex_home": str(codex_home),
        "days": days,
        "session_files_scanned": scanned,
        "matching_session_files": matched_files,
        "max_session_bytes": max_session_bytes,
        "mention_counts": dict(sorted(counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON file.")
    parser.add_argument("--repo-root", default=".", help="Local repo root.")
    parser.add_argument("--out", required=True, help="Output JSON review report.")
    parser.add_argument("--codex-home", default="~/.codex", help="Codex home for usage scan.")
    parser.add_argument("--session-days", type=int, default=30, help="Session lookback window.")
    parser.add_argument(
        "--max-session-bytes",
        type=int,
        default=2_000_000,
        help="Maximum bytes read from each Codex session file during usage scan.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    github = manifest.get("github") or {}
    clawhub = manifest.get("clawhub") or {}
    skill_path = str(clawhub.get("skill_path") or "").strip()
    slug = str(clawhub.get("slug") or "").strip()
    repo_name = str(github.get("repo_name") or "").strip()
    tokens = [item for item in (slug, repo_name, "clawhub", "ClawHub") if item]

    surface = run_surface_check(manifest_path, repo_root)
    risks = scan_auto_review_risks(repo_root, skill_path)
    usage = scan_codex_usage(
        Path(args.codex_home).expanduser().resolve(),
        tokens,
        days=args.session_days,
        max_session_bytes=args.max_session_bytes,
    )

    errors = list(surface.get("errors") or [])
    if risks:
        errors.append(
            {
                "kind": "auto_review_risk",
                "message": "Skill content contains action classes that should be blocked or manually reworked.",
            }
        )

    report = {
        "schema_version": "1.0",
        "status": "review-ready" if not errors else "needs-fix",
        "manifest_path": str(manifest_path),
        "repo_root": str(repo_root),
        "surface": surface,
        "auto_review": {
            "source": "https://developers.openai.com/codex/concepts/sandboxing/auto-review",
            "principles": [
                "auto_review_is_a_reviewer_swap_not_a_permission_grant",
                "sandbox_boundaries_stay_in_force",
                "denied_actions_require_materially_safer_alternatives_or_user_stop",
                "session_transcripts_can_inform_policy_and_permission_tuning",
            ],
            "risk_findings": risks,
        },
        "usage": usage,
        "counts": {
            "surface_errors": len(surface.get("errors") or []),
            "surface_warnings": len(surface.get("warnings") or []),
            "auto_review_risks": len(risks),
            "errors": len(errors),
        },
    }

    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)
    return 0 if report["status"] == "review-ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
