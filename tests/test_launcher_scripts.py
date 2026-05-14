from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "github-clawhub-launcher" / "scripts"


class LauncherScriptTests(unittest.TestCase):
    def test_surface_check_allows_target_skill_without_launcher_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            repo = work / "demo-repo"
            skill = repo / "skill"
            agents = skill / "agents"
            agents.mkdir(parents=True)
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                """---
name: demo-skill
description: Demo skill used to prove launch validation does not require vendored launcher scripts.
---
""",
                encoding="utf-8",
            )
            (agents / "openai.yaml").write_text("name: demo-skill\n", encoding="utf-8")

            manifest = work / "manifest.json"
            check = work / "check.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_launcher_manifest.py"),
                    "--out",
                    str(manifest),
                    "--repo-name",
                    "demo-repo",
                    "--skill-path",
                    "skill",
                    "--slug",
                    "demo-skill",
                    "--version",
                    "1.0.0",
                    "--name",
                    "Demo Skill",
                    "--description",
                    "Demo skill used to validate release surface checks for a normal target repo.",
                    "--topic",
                    "clawhub",
                    "--tag",
                    "clawhub",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_launcher_surface.py"),
                    "--manifest",
                    str(manifest),
                    "--repo-root",
                    str(repo),
                    "--out",
                    str(check),
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )

            payload = json.loads(check.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "publish-ready")
            self.assertEqual(payload["counts"]["errors"], 0)

    def test_rendered_commands_use_bundled_launcher_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            repo = work / "demo-repo"
            (repo / "skill").mkdir(parents=True)
            manifest = work / "manifest.json"
            out = work / "commands.md"
            manifest.write_text(
                json.dumps(
                    {
                        "github": {
                            "owner": "zack-dev-cm",
                            "repo_name": "demo-repo",
                            "description": "Demo repo",
                            "topics": [],
                            "release_tag": "v1.0.0",
                        },
                        "clawhub": {
                            "skill_path": "skill",
                            "slug": "demo-skill",
                            "name": "Demo Skill",
                            "version": "1.0.0",
                            "changelog": "Initial release.",
                            "tags": [],
                        },
                        "release": {"title": "Demo Skill v1.0.0"},
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_launcher_commands.py"),
                    "--manifest",
                    str(manifest),
                    "--repo-root",
                    str(repo),
                    "--out",
                    str(out),
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )

            text = out.read_text(encoding="utf-8")
            self.assertIn(str(SCRIPTS / "check_launcher_surface.py"), text)
            self.assertIn(str(SCRIPTS / "review_release_readiness.py"), text)
            self.assertIn(str(SCRIPTS / "render_release_notes.py"), text)
            self.assertNotIn(str(repo / "skill" / "scripts" / "check_launcher_surface.py"), text)

    def test_review_release_readiness_counts_usage_and_flags_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            repo = work / "demo-repo"
            skill = repo / "skill"
            agents = skill / "agents"
            agents.mkdir(parents=True)
            (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
            (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                """---
name: demo-skill
description: Demo skill used to validate release readiness review behavior.
---

# Demo

Read public release notes only.
""",
                encoding="utf-8",
            )
            (agents / "openai.yaml").write_text("name: demo-skill\n", encoding="utf-8")

            codex_home = work / "codex-home"
            session_dir = codex_home / "sessions" / "2026" / "05" / "14"
            session_dir.mkdir(parents=True)
            (session_dir / "rollout.jsonl").write_text(
                "demo-skill shipped with clawhub\n",
                encoding="utf-8",
            )

            manifest = work / "manifest.json"
            out = work / "review.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_launcher_manifest.py"),
                    "--out",
                    str(manifest),
                    "--repo-name",
                    "demo-repo",
                    "--skill-path",
                    "skill",
                    "--slug",
                    "demo-skill",
                    "--version",
                    "1.0.0",
                    "--name",
                    "Demo Skill",
                    "--description",
                    "Demo skill used to validate release readiness review behavior.",
                    "--topic",
                    "clawhub",
                    "--tag",
                    "clawhub",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "review_release_readiness.py"),
                    "--manifest",
                    str(manifest),
                    "--repo-root",
                    str(repo),
                    "--codex-home",
                    str(codex_home),
                    "--out",
                    str(out),
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )

            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "review-ready")
            self.assertEqual(payload["counts"]["auto_review_risks"], 0)
            self.assertGreaterEqual(payload["usage"]["mention_counts"]["demo-skill"], 1)
            self.assertIn(
                "auto_review_is_a_reviewer_swap_not_a_permission_grant",
                payload["auto_review"]["principles"],
            )


if __name__ == "__main__":
    unittest.main()
