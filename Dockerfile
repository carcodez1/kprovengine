# syntax=docker/dockerfile:1

FROM python:3.12-slim

ARG VCS_REF="unknown"
ARG BUILD_DATE="unknown"

LABEL org.opencontainers.image.title="kprovengine" \
    org.opencontainers.image.description="KProvEngine OSS core: local-first provenance scaffold (V1)" \
    org.opencontainers.image.source="https://github.com/carcodez1/kprovengine" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.revision="${VCS_REF}" \
    org.opencontainers.image.created="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    XDG_CACHE_HOME=/tmp

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy full repo for build correctness
COPY . /app

# Install as root into system site-packages (build needs write access)
RUN python -m pip install --upgrade pip \
    && python -m pip install .

# Create non-root user for runtime *after* install
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["kprovengine"]
CMD ["--help"]
