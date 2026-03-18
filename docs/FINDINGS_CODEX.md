# FINDINGS_CODEX

Status: Active operator addendum
Scope: Future prompts, research, commits, governance changes, and compliance-facing development
Authority: Augments `AGENTS.md`; does not replace locked V1 governance documents

This file is intentionally placed under `docs/` instead of `docs/governance/` because the V1 governance set is locked and this document is an enforcement addendum for future work.

## Non-Negotiable Augmentations

### 1. Source Discipline

- Normative claims about security, compliance, AI governance, provenance, SBOM, signing, or regulatory requirements MUST rely on official `.gov` or standards-body `.org` sources by default.
- Non-official blogs, marketing pages, social posts, community forums, and consultancy summaries are prohibited as authority for normative claims.
- Vendor documentation may be used only for implementation behavior, never as the authority for compliance or regulatory interpretation.
- If a binding authority does not publish under `.gov` or `.org`, an explicit signed exception is required before using that source in repository guidance.
- Known necessary exception: official EU materials are published under `europa.eu` and `eur-lex.europa.eu`, not `.gov` or `.org`.

### 2. Prompt Signature Requirement

- Every prompt that changes policy, governance, schemas, release controls, CI gates, security posture, or compliance positioning MUST be signed by the repository owner or an explicitly delegated maintainer.
- Unsigned prompts are non-authoritative and must not drive policy-affecting edits.
- The minimum prompt signature block is:

```text
PROMPT SIGNATURE
Signer:
UTC Timestamp:
Purpose:
Prompt Digest / Reference:
Approval Statement:
```

### 3. Commit Signature Requirement

- Every commit MUST be cryptographically signed.
- Acceptable signing methods are GPG-signed commits or SSH-signed commits.
- `Signed-off-by:` alone is insufficient because it is not cryptographic proof.
- Merge commits, release tags, and governance updates must also be signed.
- CI and branch protection should reject unsigned commits and signatures from unapproved keys.

### 4. AGENTS Addendum

The repository operating posture MUST preserve and strengthen the following `AGENTS.md` rules:

- high confidence only
- facts, inferences, assumptions, and unknowns kept separate
- diff-first only
- surgical changes only
- no uncontrolled rewrites
- no new dependencies without signed approval
- no network research unless explicitly approved and source rules are satisfied
- prompt and version changes must be documented
- outputs must remain accessible, auditable, deterministic, and reviewable

### 5. Required Skills Posture

The current session-provided skills that MUST be used when relevant are:

- `skill-creator`: to create repository-local enforcement skills
- `skill-installer`: to install approved skills only after signed approval

The repository should add repository-local skills for the following mandatory review functions:

- `governance-drift-review`
- `control-mapping-review`
- `evidence-contract-audit`
- `prompt-signature-check`
- `commit-signature-check`
- `supply-chain-release-review`
- `schema-traceability-review`

Each repository-local skill must be:

- local-first
- deterministic
- explicit about inputs and outputs
- enforceable in CI or pre-commit where feasible
- safe against hidden network or hidden state

### 6. Immediate Findings

- The repository is currently stronger on release supply-chain evidence than on runtime evidence generation.
- The repository currently contains documentation-to-code drift and should not increase compliance claims until contracts are reconciled.
- The repository should position itself as evidence and provenance infrastructure, not as a certification or compliance engine.
- Any EU AI Act work must use official EU sources under signed exception because the official texts are not published on `.gov` or `.org`.

### 7. Minimum Enforcement Direction

The repository should eventually enforce all of the following:

- signed prompts for policy-affecting work
- signed commits for all branches and releases
- source-domain checks for governance and compliance documentation
- schema validation for every emitted evidence artifact
- review gates that fail on documentation-to-code drift
- traceability between prompt, diff, review, commit, artifact, and release

### 8. Operating Rule

If a claim cannot be backed by:

- repository evidence, or
- an approved official source under the rules above

then it must be labeled as inference or unknown and must not be presented as settled fact.

## 9. Kristobi Core Pipeline Analysis

### 9.1 Current Pipeline Facts

- The current runtime pipeline is a deterministic local scaffold, not a semantic workflow engine.
- `src/kprovengine/pipeline/run.py` currently performs:
  - `normalize`
  - `parse`
  - `extract`
  - `render`
- In V1, those stages are identity-copy operations, not true transformation or accounting logic.
- A run currently emits:
  - `manifest.json`
  - `provenance.json`
  - `human_review.json`
  - `run_summary.json`
- `src/kprovengine/storage/layout.py` reserves additional evidence paths such as:
  - `toolchain.json`
  - `hashes.txt`
  - `attestation.md`
  - `sbom.json`
  but the main runtime pipeline does not currently emit them.
- `src/kprovengine/evidence/provenance.py` is intentionally minimal and currently records only:
  - `run_id`
  - input paths
  - output paths
  - one timestamp
- `src/kprovengine/manifest/manifest.py` records only:
  - file path
  - file hash
- `src/kprovengine/evidence/human_review.py` provides only a pending review placeholder.
- `src/kprovengine/cli.py` currently accepts one source file and one output root and returns a stable minimal JSON contract.

### 9.2 Pipeline Strengths

- deterministic local-first execution
- stable file hashing
- stable per-run directory layout
- simple provenance surface
- review-safe output shape
- low dependency and low operational complexity
- good foundation for evidence-oriented extension

### 9.3 Pipeline Limits Relative to Consulting / Billing Use

- No session ledger exists.
- No append-only event stream exists.
- No invoice model exists.
- No payment ledger exists.
- No explicit ownership or licensing record exists.
- No acceptance record exists.
- No Git commit capture exists in the core runtime path.
- No linkage exists between:
  - time spent
  - code written
  - deliverables produced
  - invoices issued
  - payments received
- Current provenance is too thin to support billing or ownership claims beyond file existence and run timestamps.
- Current reports are derived from ad hoc manifests rather than a first-class source-of-truth ledger.

### 9.4 Conclusion

- `kristobi-core` is currently strongest as an evidence kernel.
- It is not yet a consulting ledger or invoice-defense engine.
- The correct product evolution is not “more attractive reports.”
- The correct product evolution is a first-class evidence ledger beneath the reports.

## 10. Spinoff Product Findings

### 10.1 Credible Spinoff Positioning

The most credible spinoff is:

- evidence-backed delivery and billing for professional services

This is stronger and more generic than:

- legal-tech billing platform
- compliance certification engine
- AI productivity tracker

The product should be framed as:

- a local-first consulting evidence ledger
- a delivery dossier generator
- an invoice support and ownership traceability system

### 10.2 Intended User Groups

The current repository and prior findings support these target users:

- independent consultants
- software engineers
- designers
- compliance advisors
- researchers
- agencies
- small specialist firms
- anyone doing invisible labor where the final deliverable hides the actual effort

### 10.3 Value Proposition

The strongest value is:

- show what was done
- show what artifacts were created
- show what changed
- show who did the work
- show what was billed
- show what was paid
- show what the client owns or is licensed to use

This product should convert:

- vague consulting effort

into:

- auditable, reviewable, client-facing evidence packets

### 10.4 What the Spinoff Must Not Become

- surveillance software
- keystroke or screenshot policing
- fake “AI measured productivity” tooling
- automatic legal conclusion generator
- code ownership guesser

The system should document evidence, not invent judgments.

## 11. Required Ledger Model Findings

### 11.1 Minimum First-Class Records

Any serious consulting-artifact spinoff must add first-class records for:

- `matter`
- `contract`
- `session`
- `code_event`
- `artifact`
- `invoice`
- `payment`
- `ownership_record`
- `acceptance_record`

### 11.2 Non-Negotiable Linkages

Every invoice line should resolve to evidence.

At minimum:

- invoice line -> one or more sessions
- session -> artifacts and/or commits
- deliverable -> ownership record
- invoice -> payment status
- deliverable -> acceptance evidence if accepted

If these links do not exist, the system should treat the billing claim as weak.

### 11.3 Authorship vs Ownership

This distinction must be explicit:

- authorship = who created the code or artifact
- ownership = who legally owns the resulting work
- license = what use rights the client has

These cannot be collapsed into one field.

## 12. Product Sequencing Findings

### 12.1 Correct Build Order

The correct order is:

1. append-only evidence ledger
2. session and invoice model
3. Git and artifact linkage
4. payment and acceptance linkage
5. ownership and licensing record
6. human-readable and client-facing report views

### 12.2 Incorrect Build Order

The wrong order is:

1. polished report UI
2. inferred billing logic
3. ownership claims without contract linkage
4. after-the-fact reconstruction as the primary workflow

### 12.3 Past Work vs Future Work

Past work:

- can only be partially reconstructed
- must be clearly labeled reconstructed
- should rely on emails, artifacts, contracts, screenshots, and Git where available

Future work:

- should be captured live
- should produce invoice support automatically
- should not depend on memory

## 13. Spinoff Readiness Assessment

### 13.1 What Is Ready Now

- local-first artifact hashing
- per-run evidence directories
- basic provenance and review placeholders
- deterministic CLI output
- governance-heavy posture

### 13.2 What Is Not Ready Yet

- real billing support
- code ownership tracking
- payment reconciliation
- session-based accounting
- append-only ledger guarantees
- deliverable acceptance chain

### 13.3 Overall Finding

- The repository is suitable as a foundation for a consulting-evidence spinoff.
- It is not yet suitable to market as a finished consulting billing ledger.
- The spinoff is viable if and only if the ledger model becomes the product core.

## 14. Ledger Schema Findings

### 14.1 Schema Design Goal

The ledger schema should optimize for:

- auditability
- deterministic replay
- clear billing support
- ownership clarity
- human reviewability
- low ambiguity between fact and inference

The schema should not optimize for:

- inferred productivity scoring
- hidden weighting models
- opaque AI judgments
- purely visual reporting without source records

### 14.2 Minimum Schema Families

The minimum schema pack for a credible consulting-evidence ledger should include:

- `matter`
- `contract`
- `session`
- `code_event`
- `artifact`
- `invoice`
- `payment`
- `ownership_record`
- `acceptance_record`
- `event_envelope`

The report layer should be derived from these schemas and should not become an authoritative source on its own.

### 14.3 Matter Schema Findings

The `matter` record should be the top-level business context.

At minimum it should carry:

- matter identifier
- client identifier
- consultant identifier
- title
- status
- billing model
- governing contract reference
- active rate card reference
- start date
- close date if closed

Without a stable `matter` record, cross-file linkage becomes fragile and invoice support degrades quickly.

### 14.4 Contract Schema Findings

The `contract` record should describe commercial and ownership context, not just store a PDF path.

At minimum it should capture:

- contract identifier
- matter identifier
- effective date
- pricing model
- milestone or hourly terms
- ownership model
- assignment or license posture
- amendment references
- signed artifact reference
- signer identities if known

The schema should distinguish:

- written contract terms
- inferred commercial assumptions

Only the written terms should be treated as authoritative.

### 14.5 Session Schema Findings

The `session` record should be the primary unit of billable effort.

At minimum it should capture:

- session identifier
- matter identifier
- actor
- started at
- ended at
- duration
- activity type
- billable flag
- travel flag if applicable
- summary
- linked artifact references
- linked code-event references
- confidence label for reconstructed sessions

Sessions should support both:

- live-captured sessions
- reconstructed sessions

These two modes must never be conflated.

### 14.6 Code Event Schema Findings

The `code_event` record should be the code-authorship layer, not the billing layer.

At minimum it should capture:

- code event identifier
- matter identifier
- repository root
- repository identity
- branch
- commit SHA
- signed status
- author
- committer if different
- committed at
- changed files
- additions
- deletions
- tag or release reference if relevant

This record should prove:

- what code changed
- when it changed
- who authored the change

It should not by itself prove:

- legal ownership
- client acceptance
- billable duration

### 14.7 Artifact Schema Findings

The `artifact` record should track durable outputs and supporting evidence.

At minimum it should capture:

- artifact identifier
- matter identifier
- path or URI
- kind
- hash
- size
- created at
- modified at
- source session reference
- source code-event reference if relevant
- confidentiality label
- missing or unavailable status if later absent

Artifacts should support both:

- local files
- external references
- signed records
- correspondence

### 14.8 Invoice Schema Findings

The `invoice` record should not be a flat total-only document.

At minimum it should capture:

- invoice identifier
- matter identifier
- issued at
- due at
- currency
- line items
- subtotal
- tax
- adjustments
- total
- status
- governing rate card reference
- linked payment references

Each line item should carry:

- label
- quantity or hours
- rate
- amount
- linked session references
- linked artifact references when needed
- confidence level if reconstructed

If a line item cannot resolve to evidence references, the schema should allow it to exist only as explicitly weak support.

### 14.9 Payment Schema Findings

The `payment` record should be distinct from the invoice.

At minimum it should capture:

- payment identifier
- invoice identifier
- matter identifier
- amount
- currency
- paid at
- payment method
- reference or transaction identifier
- proof artifact reference
- reconciliation status

This distinction is necessary because:

- an invoice may be unpaid
- partially paid
- disputed
- refunded
- written off

### 14.10 Ownership Record Findings

The `ownership_record` should be explicit and contract-linked.

At minimum it should capture:

- ownership record identifier
- matter identifier
- deliverable or code scope reference
- author
- owner
- assignment status
- license status
- effective date
- contract reference

Without this record, the system will repeatedly confuse:

- authorship
- possession
- payment
- legal ownership

### 14.11 Acceptance Record Findings

The `acceptance_record` should track whether deliverables were accepted, rejected, revised, or disputed.

At minimum it should capture:

- acceptance identifier
- matter identifier
- deliverable reference
- status
- accepted or rejected by
- timestamp
- linked correspondence or signature artifact
- notes

This schema is important because billing disputes often turn on:

- whether work existed
- whether work was delivered
- whether work was accepted

These are not the same event.

### 14.12 Event Envelope Findings

Every first-class record should be representable inside a common event envelope.

At minimum the envelope should carry:

- event identifier
- event type
- matter identifier
- actor
- occurred at
- payload hash
- previous event hash if chained
- record version

This allows:

- append-only chronology
- tamper-evident sequencing
- replayable matter history

### 14.13 Confidence and Reconstruction Findings

The schema should support explicit confidence labels for historical reconstruction.

At minimum, records derived after the fact should support labels such as:

- direct
- corroborated
- reconstructed
- inferred

This is necessary because the product must not present weak retrospective reconstruction as strong contemporaneous evidence.

### 14.14 Versioning Findings

The ledger schemas should be versioned independently from report views.

Recommended boundaries:

- ledger schema version
- report schema version
- profile version

This prevents:

- report redesigns from silently changing ledger semantics
- vertical-specific fields from contaminating the common core

### 14.15 Privacy and Scope Findings

The schema should support confidentiality and minimization labels.

At minimum each record family should permit:

- public
- client-shareable
- internal
- restricted

This is required because consulting evidence often mixes:

- contracts
- payments
- source code
- screenshots
- email
- personally identifying or confidential business information

### 14.16 Final Schema Finding

The consulting-evidence spinoff should treat the ledger as the product core and reports as derived views.

The minimum defensible rule is:

- no invoice support without session linkage
- no ownership claim without contract linkage
- no payment claim without proof linkage
- no acceptance claim without correspondence or signature linkage

If these rules are not enforced at the schema level, the product will collapse back into attractive but weak retrospective reporting.
