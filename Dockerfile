FROM python:3.12-slim

# Install cosign binary, syft, jq
RUN apt-get update && apt-get install -y jq curl \
    && curl -sSL https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 \
    -o /usr/local/bin/cosign && chmod +x /usr/local/bin/cosign

RUN python3 -m pip install --upgrade pip syft in_toto
