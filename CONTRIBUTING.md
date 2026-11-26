<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contributing

[中文](CONTRIBUTING_CN.md) | English

Open an Issue for a reproducible problem or workflow proposal, or submit a focused PR. See [Support](SUPPORT.md) for questions and [Security](SECURITY.md) for sensitive reports. Never publish credentials, private code, user data or complete agent transcripts.

Useful contributions include evidence-backed decision rules with a clear scope, repository-profile corrections with fixed references and actual verification dates, clearer entrypoints that preserve authorization boundaries, and validator fixes with minimal regression fixtures.

Keep `SKILL.md` focused on discovery, essential invariants and reference routing. Use relative package links without sibling-skill or author-machine dependencies. Keep complete `LICENSE` and `NOTICE` files in standalone packages. Preserve protocol and project rule IDs. Historical diagnoses belong in references, not universal requirements.

## Before submitting

1. Set up the Python environment in [README](README.md).
2. Run `python scripts/validate.py`, `python -m unittest discover -s tests -v`, and `git diff --check`.
3. For behavioral changes, rerun applicable [offline scenarios](docs/validation.md), using an independent context when available. Give evaluators raw requests and fixtures, not expected answers. Do not perform live writes to test instructions.
4. Describe resulting behavior, evidence, limits and provenance in the PR. Keep English/Chinese community documents aligned; skill references currently use Chinese.

Structural validation does not prove behavior. Moving text does not revalidate an old PR or environment. Read [provenance](docs/provenance.md), verify contribution rights and retain attribution. Identify new third-party text, assets, dependencies and license obligations.

Unless explicitly stated otherwise, contributions are submitted under Apache-2.0. Submit only work you are entitled to contribute. This repository does not establish an ASF CLA process or require ASF committer status. Maintainers review behavior and scope; passing CI does not itself authorize merge.
