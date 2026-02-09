# KProvEngine — Change Control

---

## Purpose

This document defines how changes are proposed, evaluated, and accepted
for KProvEngine.

The goal is to maintain technical credibility and prevent uncontrolled scope
expansion.

---

## V1 Rules

While V1 is active:

- The stack defined in STACK_V1_LOCKED.md is immutable
- The prompt defined in PROMPT_V1_LOCKED.md is authoritative
- Only changes that improve correctness, structure, security, or clarity
  are permitted

---

## Proposing Changes

Any change outside V1 scope must be:

1. Marked explicitly as “Out of V1 scope”
2. Recorded in BACKLOG.md
3. Deferred until V2 planning

No exceptions.

---

## Version Transitions

- V1 → V2 requires:
  - Updated stack document
  - New locked prompt
  - Explicit rationale for scope expansion

Old governance documents are preserved for traceability.

---

## Guiding Principle

Small, correct, defensible systems are preferred over broad or speculative ones.
