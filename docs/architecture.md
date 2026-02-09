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

  A["Input Artifacts<br/>(files, images, notes)"] --> B["Normalize<br/>(deterministic, local-only)"]
  B --> C["Parse<br/>(format-aware, no inference)"]
  C --> D["Extract<br/>(structural extraction)"]
  D --> E["Render<br/>(outputs)"]
  E --> R["Evidence Bundle<br/>(run directory)"]

  %% Optional adapters (non-authoritative)
  subgraph OPT["Adapters (Optional, Non-authoritative)"]
    OCR["OCR Adapter<br/>(EasyOCR / Tesseract)"]
    LLM["LLM Adapter<br/>(Ollama / LangChain)"]
  end

  OCR -.-> C
  OCR -.-> D
  LLM -.-> D

  %% Evidence artifacts (V1)
  subgraph ART["Evidence Artifacts (V1)"]
    M["manifest.json<br/>SHA-256 manifest"]
    P["provenance.json<br/>execution metadata"]
    T["toolchain.json<br/>tool/version disclosure"]
    H["human_review.json<br/>PENDING allowed"]
    X["hashes.txt<br/>content hashes"]
    ATE["attestation.md<br/>human statement"]
    S["sbom.json<br/>CI-generated when available"]
  end

  R --> M
  R --> P
  R --> T
  R --> H
  R --> X
  R --> ATE
  R --> S

  HR["Human Reviewer"] --> H
  HR --> ATE
```
    
