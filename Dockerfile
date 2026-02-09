FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/carcodez1/KProvEngine"
LABEL org.opencontainers.image.title="kprovengine"
LABEL org.opencontainers.image.description="KProvEngine V1: local-first provenance scaffold"
LABEL maintainer="Jeffrey Plewak <plewak.jeff@gmail.com>"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal runtime deps only
RUN apt-get update \
  && aspt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install package (no dev deps in runtime image)
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install --no-cache-dir .

# Default: show help
ENTRYPOINT ["python", "-m", "kprovengine"]
CMD ["--help"]
