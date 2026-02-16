# AI Usage & Prompt Injection Security Policy

Project: kprovengine (OSS Core)
Version: V1
Status: Enforced by governance review

## 1. Scope

This policy governs:

- Use of AI code assistants (Copilot, ChatGPT, etc.)
- LLM integrations in adapters
- Handling of proprietary or sensitive data
- Prompt injection defenses

## 2. Data Classification Rules

The following MUST NOT be sent to external AI services:

- Private repository source code
- Customer data
- Secrets (.env, API keys, tokens)
- Credentials or cryptographic material
- Unreleased vulnerability details

Developers MUST redact:

- Absolute paths
- Hostnames
- Environment variables
- Internal system identifiers

## 3. Prompt Injection Controls (LLM Mode)

If LLM adapters are enabled:

- All retrieved content is treated as untrusted.
- System instructions MUST be immutable and separated.
- Tool execution MUST be allowlisted.
- No arbitrary shell execution permitted.
- No filesystem reads outside run directory.
- No environment variable exposure.

## 4. Auditability

All model calls MUST:

- Record input hash
- Record output hash
- Record model identifier
- Record timestamp (UTC, ISO-8601 Z)

## 5. Supply Chain

Release artifacts MUST:

- Be built in CI
- Have SBOM attached
- Have provenance attestation
- Be cryptographically signed

## 6. Violations

Violations require:

- Immediate revocation of release tag (if applicable)
- Incident note in SECURITY.md
