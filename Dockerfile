FROM python:3.12-slim

# OCI labels (identity + traceability)
LABEL org.opencontainers.image.title="kprovengine"
LABEL org.opencontainers.image.description="KProvEngine OSS core: local-first provenance scaffold (V1)"
LABEL org.opencontainers.image.source="https://github.com/carcodez1/kprovengine"
LABEL org.opencontainers.image.licenses="MIT"

# Runtime hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Minimal OS deps only (keep attack surface small)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install package (copy only metadata first for layer caching)
COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

# Install the OSS core (no dev deps in image)
RUN python -m pip install --upgrade pip \
    && python -m pip install .

# Default: show CLI help (deterministic, no external deps)
ENTRYPOINT ["kprovengine"]
CMD ["--help"]
