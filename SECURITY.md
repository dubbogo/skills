<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Policy

[中文](SECURITY_CN.md) | English

This repository distributes agent instructions and local validation tooling. Security issues include secret disclosure, authorization bypass, untrusted host execution and unintended external writes. Only latest `main` content is maintained; no versioned support commitment is established.

Do not put exploitable details, credentials or private source in public Issues. If GitHub **Security → Report a vulnerability** is available, use that private channel; its availability has not been verified for this version. Otherwise request a private contact using a neutral public message without sensitive values or exploit details. No dedicated security mailbox or response-time guarantee is configured; do not invent one.

Include the skill and commit, sanitized minimal request/fixture, observed action, expected authorization boundary and impact. Use disposable data, never production or another person's account. Do not test exposed credentials for validity. Their owner should revoke or rotate them; text deletion does not revoke access.

Skills are guidance, not a sandbox or access-control mechanism. Inspect packages before use, keep secrets out of fixtures and logs, enforce execution restrictions independently, and verify user authorization before external actions. Coordinate disclosure with maintainers before publishing a safe summary.
