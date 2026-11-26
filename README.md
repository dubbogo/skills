<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dubbogo Skills

[中文](README_CN.md) | English

Agent skills for requirement analysis, task handoff, PowerContext Rust migration and engineering PR review. The first version adapts workflows from `alexstocks/arch-practice/alg/openclaw` into focused entrypoints with references loaded by role, stage and risk.

This is a community repository under the Dubbogo GitHub organization. It does not claim ASF project status or endorsement. Apache-2.0 is the license, not a project-status designation.

## Skills

| Skill | Use when | Deliverable |
|---|---|---|
| [task-issue-harness](task-issue-harness/SKILL.md) | Clarifying requirements, preparing Task Issues, or implementing approved contracts | Reviewable contracts and evidence-bound handoffs |
| [powercontext-rust-migration](powercontext-rust-migration/SKILL.md) | Analyzing or executing PowerContext Python-to-Rust units | Semantic, native-path, installed-wheel and performance evidence |
| [engineering-pr-review](engineering-pr-review/SKILL.md) | Reviewing PRs, updated Heads and merge readiness | Current-snapshot findings and authorized inline comments |

The review package indexes 10 repository profiles and historical diagnostic material. Fork identities remain separate. Diagnostic experience does not automatically add mandatory checks.

## Installation

Clone this repository, then copy the **whole directory** of a selected skill into your runtime's supported discovery directory. For example, run from the clone root:

```powershell
$skillName = 'task-issue-harness'
$skillRoot = Join-Path $env:USERPROFILE '.agents\skills'
$destination = Join-Path $skillRoot $skillName
if (Test-Path -LiteralPath $destination) { throw "Already installed: $destination" }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath (Join-Path (Get-Location) $skillName) -Destination $destination -Recurse
```

```sh
skill_name=task-issue-harness
skill_root="$HOME/.agents/skills"
mkdir -p "$skill_root"
if [ -e "$skill_root/$skill_name" ]; then
  echo "Already installed: $skill_root/$skill_name" >&2
  exit 1
fi
cp -R "./$skill_name" "$skill_root/$skill_name"
```

These examples refuse to replace an existing installation. Use your runtime's configured path if different. Refresh or reopen the agent session as required, and confirm the skill is listed before relying on automatic selection. Every package includes `LICENSE` and `NOTICE` and works without sibling skills, the original working directory or a mandatory MCP server. Installation is manual; no global agent configuration is modified.

## Usage

```text
Use $task-issue-harness to prepare Task Issue drafts only for this requirement.
Use $task-issue-harness to implement the approved Issue using its existing authorization.
Use $powercontext-rust-migration to assess a first unit; do not implement yet.
Use $engineering-pr-review to review this PR locally without posting comments.
```

Automatic discovery does not grant permission to publish, push, merge or deploy. Preserve current user instructions and valid prior authorization. Select one review protocol rather than stacking conflicting legacy review skills. The harness retains explicit contract approval and execution-mode gates.

## Structure and maintenance

Each skill has `SKILL.md`, `agents/openai.yaml`, and references. Task Issue output templates live in `assets/`. The repository also includes `scripts/validate.py`, validator regression tests, `.github/` collaboration templates and CI, and `docs/` conversion evidence.

Read [architecture](docs/architecture.md), [provenance](docs/provenance.md), [source manifest](docs/source-manifest.json), and [behavioral validation](docs/validation.md). This repository is the maintained source for these packages; upstream documents are not loaded at runtime or synchronized automatically. Import hashes distinguish working-tree revisions from their committed baseline. An import date does not refresh a historical validation date. Community documents are bilingual; skill instructions and references currently use Chinese.

## Validation

Python 3.11+ is required only to validate the repository, not to use the skills. From the clone root:

```sh
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests -v
git diff --check
```

On Windows without activation, use `.venv\Scripts\python.exe` for subsequent Python commands. Checks cover package metadata, distribution files, fences, plain inline local links, and explicit rule/experience index anchors. Titled or reference-style links and general heading fragments are not validated; use plain inline links for package navigation. Checks do not execute workflows, verify remote URLs or prove agent behavior. CI is configured for Linux and Windows; remote success must be verified separately. See [offline scenarios](docs/validation.md) for behavioral changes.

## Community and license

See [Contributing](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md), [Security](SECURITY.md), [Support](SUPPORT.md) and [Changelog](CHANGELOG.md), each with a Chinese version.

Licensed under [Apache-2.0](LICENSE). [LICENSE_CN.md](LICENSE_CN.md) is an unofficial reading translation; the unmodified English license governs. Preserve [NOTICE](NOTICE) and [attribution](docs/provenance.md) when redistributing. Names and trademarks remain with their owners.
