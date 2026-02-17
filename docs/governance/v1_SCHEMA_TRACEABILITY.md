# V1 Schema Traceability Matrix — KProvEngine

## Scope

This document defines traceability between:

- JSON artifacts
- JSON schemas
- Source code
- Tests
- Governance guarantees

---

## Artifact → Schema Mapping

| Artifact File     | Schema File              |
| ----------------- | ------------------------ |
| CLI stdout        | cli_success.schema.json  |
| provenance.json   | provenance.schema.json   |
| manifest.json     | manifest.schema.json     |
| run_summary.json  | run_summary.schema.json  |
| toolchain.json    | toolchain.schema.json    |
| human_review.json | human_review.schema.json |

---

## Schema → Code Mapping

| Schema                   | Code Module                              |
| ------------------------ | ---------------------------------------- |
| cli_success.schema.json  | src/kprovengine/cli.py                   |
| provenance.schema.json   | src/kprovengine/evidence/provenance.py   |
| manifest.schema.json     | src/kprovengine/manifest/manifest.py     |
| run_summary.schema.json  | src/kprovengine/pipeline/run.py          |
| toolchain.schema.json    | src/kprovengine/evidence/toolchain.py    |
| human_review.schema.json | src/kprovengine/evidence/human_review.py |

---

## Schema → Test Enforcement

| Schema       | Test File                           |
| ------------ | ----------------------------------- |
| cli_success  | tests/integration/test_cli_smoke.py |
| provenance   | tests/unit/test_evidence.py         |
| manifest     | tests/unit/test_manifest.py         |
| toolchain    | tests/unit/test_evidence.py         |
| human_review | tests/unit/test_evidence.py         |

---

## Governance Guarantee

V1 guarantees:

- JSON surface stability
- additionalProperties = false
- Deterministic key set
- Backward compatible additive changes require schema version bump

Any breaking change requires:

1. Major version increment
2. Schema update
3. Test update
4. Governance update
