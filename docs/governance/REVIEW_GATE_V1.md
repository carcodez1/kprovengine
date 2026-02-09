# KProvEngine — Review Gate (V1)

Status: Active  
Applies to: All code changes in V1.x

---

## Purpose

This document defines the review and verification criteria for KProvEngine V1.

It is used to evaluate whether new code, documentation, or configuration
remains compliant with the V1 Master Prompt and does not introduce scope,
behavioral, or claim drift.

This is a **review control**, not a development guide.

---

## Review Prompt (Use Verbatim)

When reviewing any change, answer the following explicitly:

1. **Scope**
   - Does this change introduce new behavior beyond V1 scope?
   - Does it imply features (OCR quality, LLM correctness, compliance) not yet implemented?

2. **Claims**
   - Does any code, docstring, README text, or output imply:
     - compliance certification?
     - audit guarantees beyond artifact generation?
     - autonomous or agentic behavior?
   - If yes, the change must be rejected or revised.

3. **Architecture**
   - Does this preserve the separation between:
     - core pipeline
     - adapters
     - evidence contracts
   - Are adapters still optional and non-authoritative?

4. **Determinism & Locality**
   - Does this introduce:
     - network access?
     - hidden state?
     - nondeterministic side effects beyond run IDs?
   - If yes, document explicitly or defer to V2.

5. **Imports & Dependencies**
   - Are all new dependencies justified, minimal, and local-first?
   - Are heavy dependencies isolated behind adapters?

6. **Evidence & HITL**
   - Does this preserve explicit human review status?
   - Does it avoid implying automated approval or validation?

7. **CI / Tooling**
   - Do tests, lint, and build still pass?
   - Does CI remain green without OCR/LLM binaries?

---

## Acceptance Criteria

A change may be accepted if and only if:
- All questions above are answered satisfactorily
- No V1 constraints are violated
- Any future work is recorded in BACKLOG.md, not implemented

---

## Rejection Rule

If a reviewer cannot confidently answer “yes” or “not applicable” to all
review questions, the change must be rejected or deferred.