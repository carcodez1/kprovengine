# KProvEngine Architecture (V1)

This document describes the V1 pipeline and evidence flow. It is intentionally
minimal and conservative.

V1 principles:
- The core pipeline is deterministic and local-first.
- OCR/LLM integrations are optional adapters and are non-authoritative.
- Human review is explicit and captured as evidence artifacts.

## V1 Pipeline and Evidence Flow

```mermaid
flowchart LR
  %% KProvEngine V1: pipeline + evidence flow (single-pass, local-first)

  A[Input Artifacts\n(files, images, notes)] --> B[Normalize\n(deterministic)]
  B --> C[Parse\n(format-aware)]
  C --> D[Extract\n(structure)]
  D --> E[Render\n(outputs)]

  %% Optional adapters (non-authoritative)
  subgraph AD[Adapters (Optional / Non-authoritative)]
    O1[OCR Adapter\n(EasyOCR | Tesseract)] --> C
    L1[LLM Adapter\n(Ollama | LangChain-in-adapter)] --> D
  end

  %% Evidence bundle produced from pipeline execution
  E --> F[Evidence Bundle\n(run directory)]
  subgraph EV[Evidence Artifacts (V1)]
    M[manifest.json\n(SHA-256 manifest)]
    P[provenance.json\n(execution metadata)]
    T[toolchain.json\n(tool/version disclosure)]
    H[human_review.json\n(PENDING allowed)]
    X[hashes.txt\n(content hashes)]
    A1[attestation.md\n(human statement)]
    S[sbom.json\n(CI-generated when available)]
  end

  F --> M
  F --> P
  F --> T
  F --> H
  F --> X
  F --> A1
  F --> S

  %% Explicit human-in-the-loop review
  R[Human Reviewer] --> H
  R --> A1
