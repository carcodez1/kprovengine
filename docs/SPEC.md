## Project Identity Contract (V1 LOCKED)

### Technical Identity (MUST match exactly)

1. Repository slug: `kprovengine`
2. Python distribution name: `kprovengine`
3. Python import root: `kprovengine`
4. CLI entrypoint: `kprovengine`
5. Canonical repository URL: `https://github.com/carcodez1/kprovengine`
6. OCI image title label: `kprovengine`
7. OCI image source label MUST include the canonical repository URL.

### Display Identity (allowed only in documentation/marketing text)

1. Display name: `KProvEngine`

### Allowed usage rules

1. The display name `KProvEngine` is allowed ONLY in:
    - Markdown documentation (`README.md`, `docs/**`, `OSS_GOVERNANCE.md`, `SUPPORT.md`, etc.)
    - OCI image description label text (description only)
2. The technical identity `kprovengine` MUST be used in:
    - `pyproject.toml` metadata (name, scripts)
    - Python package/module names and imports
    - CLI binary name and help/version output (unless explicitly stated otherwise in CLI contract)
    - Docker/OCI labels for `org.opencontainers.image.title` and `org.opencontainers.image.source`
3. Source code under `src/**` MUST NOT contain the display name `KProvEngine` except in top-level module docstrings where explicitly justified.
