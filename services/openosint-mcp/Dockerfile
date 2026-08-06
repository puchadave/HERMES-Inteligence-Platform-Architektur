FROM node:22-bookworm-slim

ARG OPENOSINT_VERSION=2.25.0
ARG SUPERGATEWAY_VERSION=3.4.3
ARG HOLEHE_VERSION=1.61
ARG SHERLOCK_PROJECT_VERSION=0.16.0
ARG SUBLIST3R_VERSION=1.0
ARG PHONEINFOGA_VERSION=2.11.0
ARG PHONEINFOGA_SHA256=6173dfc4ec009a6fe688068bac5a250646f5a8f56409098f5edcc7e404b12a52

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
    tar \
    whois \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global "supergateway@${SUPERGATEWAY_VERSION}" \
    && python3 -m pip install --break-system-packages --no-cache-dir \
       "openosint[all]==${OPENOSINT_VERSION}" \
       "holehe==${HOLEHE_VERSION}" \
       "sherlock-project==${SHERLOCK_PROJECT_VERSION}" \
       "Sublist3r==${SUBLIST3R_VERSION}"

RUN set -eux; \
    archive="phoneinfoga_Linux_x86_64.tar.gz"; \
    curl --fail --location --retry 4 \
      "https://github.com/sundowndev/phoneinfoga/releases/download/v${PHONEINFOGA_VERSION}/${archive}" \
      --output "/tmp/${archive}"; \
    echo "${PHONEINFOGA_SHA256}  /tmp/${archive}" | sha256sum --check -; \
    tar --extract --gzip --file "/tmp/${archive}" --directory /tmp; \
    install --mode 0755 /tmp/phoneinfoga /usr/local/bin/phoneinfoga; \
    phoneinfoga version; \
    rm -f "/tmp/${archive}" /tmp/phoneinfoga

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
