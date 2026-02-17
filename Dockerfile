# syntax=docker/dockerfile:1.7

################################################################################
# Builder: build wheel in an isolated stage
################################################################################
FROM python:3.12-slim AS builder

ARG VCS_REF="unknown"
ARG BUILD_DATE="unknown"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    XDG_CACHE_HOME=/tmp

WORKDIR /src

# Minimal OS deps for building python wheels (keep explicit)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only packaging + source inputs required for a build (deterministic surface)
COPY pyproject.toml README.md LICENSE /src/
COPY src/ /src/src/

# Build wheel in isolated env
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -U pip \
    && python -m pip install build \
    && python -m build -w -o /src/dist

################################################################################
# Runtime: install wheel, drop privileges, immutable-ish defaults
################################################################################
FROM python:3.12-slim AS runtime

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

# Install from wheel only (prevents “copy whole repo then pip install .” drift)
COPY --from=builder /src/dist/*.whl /tmp/dist/

RUN python -m pip install -U pip \
    && python -m pip install /tmp/dist/*.whl \
    && rm -rf /tmp/dist

# Non-root user
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["kprovengine"]
CMD ["--help"]
