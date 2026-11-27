<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

[中文](CHANGELOG_CN.md) | English

## Unreleased

- Add three standalone skills for Task Issue handoff, Python-to-Rust optimization and PR review.
- **Breaking:** rename the `task-issue-harness` skill to `task-issue`; remove the old installed directory and update `$task-issue-harness` invocations before upgrading.
- Rename the pull request review skill to `pr-review`.
- Rename the Python-to-Rust skill to `py2rust` and make its project settings repository-specific.
- Split workflow references; preserve review rule IDs and index 10 repository profiles and historical diagnoses.
- Retire conflicting historical thread instructions and record source hashes and working-tree revisions.
- Add offline validation, regression tests and Linux/Windows CI configuration.
- Complete bilingual community documentation, unofficial Chinese license translation and package notices.

This does not imply a release tag, remote CI success or real-task acceptance.
