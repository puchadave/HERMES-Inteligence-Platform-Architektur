FROM node:22-bookworm-slim

ARG OPENOSINT_VERSION=2.25.0
ARG SUPERGATEWAY_VERSION=3.4.3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dnsutils \
    git \
    python3 \
    python3-pip \
    whois \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global "supergateway@${SUPERGATEWAY_VERSION}" \
    && python3 -m pip install --break-system-packages --no-cache-dir \
       "openosint[all]==${OPENOSINT_VERSION}" \
       holehe \
       sherlock-project \
       sublist3r

RUN useradd --create-home --uid 10001 openosint \
    && mkdir -p /reports \
    && chown -R openosint:openosint /reports

USER openosint
WORKDIR /home/openosint

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --retries=5 \
  CMD curl --fail --silent http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["supergateway"]
CMD ["--stdio", "openosint-mcp", "--outputTransport", "streamableHttp", "--stateful", "--sessionTimeout", "300000", "--port", "8000", "--streamableHttpPath", "/mcp", "--healthEndpoint", "/healthz", "--logLevel", "info"]
