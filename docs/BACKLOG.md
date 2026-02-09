# KProvEngine — Backlog

Status: Active
Scope: Deferred (V2+)
Authority: CHANGE_CONTROL.md

This document records **explicitly deferred work** that is out of scope for
KProvEngine V1. Items listed here must not be implemented until a V2 planning
cycle is formally approved.

---

## V2: Remote Storage, Metadata Indexing, and Run Cataloging

**Status:** Backlogged
**Priority:** Medium → High (driven by real-world adoption and scale)

### Goal

Enable optional, pluggable infrastructure for remote persistence, indexing,
and discovery of KProvEngine runs without compromising V1’s local-first and
deterministic guarantees.

---

### Motivation

As usage scales, users will require:

- Off-machine persistence of evidence bundles
- Searchable history of runs across projects
- Structured discovery and retrieval of provenance artifacts

These capabilities must remain **optional**, **auditable**, and **non-authoritative**
with respect to human review.

---

### Scope (V2+ Only)

#### 1. Storage Adapters

- Define a `StorageAdapter` interface
- Provide reference implementations for:
  - AWS S3
  - Google Cloud Storage (GCS)
  - Azure Blob Storage (optional)
- Canonical object layout and stable key naming
- No implicit uploads; explicit user action only

#### 2. Metadata Indexing

- Define a deterministic index schema for run metadata
- Support indexing of:
  - run ID
  - timestamps
  - input artifact hashes
  - evidence artifact paths
  - optional tags and annotations
- Backend options to evaluate:
  - SQLite (embedded, default)
  - Elastic / OpenSearch (optional)
  - Vector databases (explicitly deferred beyond V2)

#### 3. Run Cataloging

- Implement a catalog module to:
  - list runs
  - filter by date, tag, input type
  - retrieve summaries and metadata
  - cross-reference evidence bundles
- Catalog must be read-only by default

#### 4. CLI Integration

- CLI commands for:
  - pushing runs to remote storage
  - indexing completed runs
  - querying the run catalog
- No background sync or agents

#### 5. CI and Governance Updates

- Update governance documents:
  - `STACK_V2_LOCKED.md`
  - `PROMPT_V2_LOCKED.md`
  - `REVIEW_GATE_V2.md`
- Document operational constraints and risks
- Preserve all V1 governance artifacts for traceability

---

### Non-Goals (Explicit)

The following are **not** included in V2:

- Compliance or certification claims
- Autonomous or agent-driven workflows
- Real-time artifact streaming
- ML-driven or semantic search
- Hosted SaaS services

---

### Acceptance Criteria (V2)

- Storage adapter interfaces defined and documented
- AWS S3 and GCS adapters implemented as examples
- Deterministic index schema documented and implemented
- Run catalog module with query APIs
- CLI commands demonstrating remote push and catalog query
- Unit and integration tests covering adapters and indexing

---

### Risks and Mitigations

- **Security:** credentials managed via secure configuration only
- **Cost:** remote storage costs documented and opt-in
- **Determinism:** canonical paths and object keys must remain stable
- **Complexity:** remote features isolated behind adapters

---

### Test Plan (High-Level)

- Unit tests for storage adapters (mocked APIs)
- Integration tests using emulators (e.g., localstack, GCS emulator)
- Index lifecycle tests (insert → query → verify)
- CLI smoke tests for remote operations

---

### Related Documents (Future)

- `docs/governance/PROMPT_V2_LOCKED.md`
- `docs/governance/REVIEW_GATE_V2.md`
- `docs/architecture_remote.md`
- `src/kprovengine/storage/adapters/`
- `src/kprovengine/catalog/`

---

## V2: Advanced Governance and Policy Enforcement

**Status:** Backlogged
**Priority:** Medium

### Description

Introduce optional, explicit governance and policy enforcement layers for
organizations operating KProvEngine at scale.

### Scope (V2+)

- Policy-as-code integration (OPA or equivalent)
- Formalized evidence invariants and manifest rules
- Snapshot compliance checks
- CI-integrated policy validation
- Evidence auditing workflows

### Non-Goals

- Automated approval or validation
- Regulatory certification claims
- Runtime policy enforcement without human review

### Next Actions

- Define policy scope and invariants
- Evaluate OPA/Rego applicability
- Draft example policies
- Document governance extension model

---

## Guiding Principle

Backlog items exist to **absorb pressure without corrupting V1**.

If a feature requires:
- remote state
- orchestration
- policy engines
- compliance claims

it belongs here, not in V1.

Discipline preserves credibility.
