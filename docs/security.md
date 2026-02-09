# Security Posture (V1)

This document describes the security and safety posture of **KProvEngine v1.x**.
The project is local-first and conservative by design.

---

## Goals

- Prevent accidental leakage of secrets or personally identifiable information (PII)
- Produce audit-friendly evidence artifacts without over-collection
- Keep AI usage bounded, transparent, and subject to human oversight
- Maintain reproducibility and traceability of outputs

---

## Controls

### Source Control Hygiene

- .gitignore excludes:
  - .env
  - run directories
  - OCR input images
  - evidence output bundles
  - vault or state directories
- Binary artifacts and generated outputs must not be committed.

### Pre-Commit (Recommended)

Local pre-commit hooks should enforce:

- linting and formatting
- secret scanning
- basic file hygiene checks

### CI Enforcement

CI workflows enforce:

- secret scanning via gitleaks
- detection of forbidden tracked artifacts
- test and lint execution before merge

---

## AI Safety Constraints

- AI components are assistive, not autonomous
- AI outputs are treated as drafts unless explicitly reviewed
- Human-in-the-loop (HITL) review is a first-class concept
- LangChain usage is adapter-scoped only:
  - no orchestration ownership
  - no state management
- No remote or cloud AI APIs are used in V1

---

## Evidence Artifacts

When enabled, evidence artifacts may include:

- hashes and manifests
- provenance records
- toolchain metadata
- human review records
- attestations

These artifacts support auditability and traceability, not regulatory certification.

---

## Compliance Claims

KProvEngine is not a certified or compliant product.

The project demonstrates techniques that support auditability and reproducibility but makes no claims of regulatory approval or compliance certification.

---

## Threat Model (High-Level)

Out of scope for V1:

- multi-user authentication
- network-exposed services
- hosted deployments

Primary risks addressed in V1:

- accidental data leakage
- uncontrolled AI behavior
- non-reproducible outputs
