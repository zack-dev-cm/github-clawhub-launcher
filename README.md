# GitHub + ClawHub Release Reviewer

**Review GitHub and ClawHub release plans before a human publishes.**

GitHub + ClawHub Release Reviewer is a checklist-first ClawHub skill for release
preparation. It reviews release metadata, public wording, versioning, tags,
release notes, test evidence, and final publish order before a human runs any
GitHub or ClawHub action.

The ClawHub artifact is intentionally lightweight: `SKILL.md`,
`agents/openai.yaml`, and the license. Repo helper scripts remain available for
maintainers, but they are excluded from the ClawHub package.

## Proof

The public skill returns a readiness verdict, metadata fixes, release-note draft,
test and audit checklist, and final human-run publish order.

## Quick Start

Use the ClawHub skill with the project facts you already have: repo owner, repo
name, skill path, slug, version, display name, changelog, tags, topics, README
status, test status, and any known blockers.

## What It Covers

- GitHub repo name, owner, description, topics, and release notes
- ClawHub slug, display name, version, changelog, license, and tags
- README, `SKILL.md`, and `agents/openai.yaml` readiness
- public-surface wording risks such as local paths, secrets, private project
  names, private customer data, or unreleased screenshots
- test and audit evidence before a human publishes

## Included

- `skill/github-clawhub-launcher/SKILL.md`
- `skill/github-clawhub-launcher/agents/openai.yaml`
- `skill/github-clawhub-launcher/LICENSE`

## Use Cases

- review a local skill repo before publishing it
- clean up public package wording
- draft concise release notes
- check that tests and audits are documented
- keep GitHub repo metadata and ClawHub package metadata aligned

## License

MIT No Attribution (MIT-0)
