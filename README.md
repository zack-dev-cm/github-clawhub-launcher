# GitHub + ClawHub Launcher

**Prepare a public GitHub repo and ClawHub skill release from one local project folder.**

GitHub + ClawHub Launcher is a small public OpenClaw skill for release preparation.
It creates a machine-readable launch manifest, checks the public release surface,
renders GitHub release notes, and prints the exact commands needed to publish a repo
and a ClawHub package without rebuilding the process from memory each time.

Pair it with `publish-guard` when you want a leak and public-surface audit before you ship.

## Proof

```bash
status: publish-ready

## GitHub
git add .
git commit -m 'Initial public release: ...'
gh repo create OWNER/REPO --public ...

## ClawHub
npx --yes clawhub publish ...
```

## Quick Start

```bash
python3 skill/github-clawhub-launcher/scripts/init_launcher_manifest.py \
  --out /tmp/launcher-manifest.json \
  --repo-name github-clawhub-launcher \
  --skill-path skill/github-clawhub-launcher \
  --slug github-clawhub-launcher \
  --version 1.0.0 \
  --name "GitHub + ClawHub Launcher" \
  --description "Prepare a public GitHub repo and ClawHub skill release from one local project folder." \
  --topic github \
  --topic clawhub \
  --tag github \
  --tag clawhub

python3 skill/github-clawhub-launcher/scripts/check_launcher_surface.py \
  --manifest /tmp/launcher-manifest.json \
  --repo-root . \
  --out /tmp/launcher-check.json

python3 skill/github-clawhub-launcher/scripts/render_release_notes.py \
  --manifest /tmp/launcher-manifest.json \
  --out /tmp/launcher-release.md

python3 skill/github-clawhub-launcher/scripts/render_launcher_commands.py \
  --manifest /tmp/launcher-manifest.json \
  --repo-root . \
  --out /tmp/launcher-commands.md
```

## What It Covers

- one manifest for GitHub repo metadata, ClawHub package metadata, tags, and changelog text
- a structural check for `README.md`, `LICENSE`, `SKILL.md`, `agents/openai.yaml`, semver, slug shape, and description quality
- release notes rendered from the manifest instead of retyping them each time
- a ready-to-run publish command sheet for GitHub repo creation, release creation, and ClawHub publish

## Included

- `skill/github-clawhub-launcher/SKILL.md`
- `skill/github-clawhub-launcher/agents/openai.yaml`
- `skill/github-clawhub-launcher/scripts/init_launcher_manifest.py`
- `skill/github-clawhub-launcher/scripts/check_launcher_surface.py`
- `skill/github-clawhub-launcher/scripts/render_release_notes.py`
- `skill/github-clawhub-launcher/scripts/render_launcher_commands.py`

## Use Cases

- turn a local skill repo into a repeatable GitHub + ClawHub launch process
- stop rewriting the same publish checklist and release notes for every public package
- validate repo structure before running `gh repo create` and `clawhub publish`
- keep GitHub repo metadata and ClawHub package metadata aligned

## License

MIT
