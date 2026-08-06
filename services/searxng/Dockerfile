ARG SEARXNG_TAG=2026.7.26-b060c780d
FROM searxng/searxng:${SEARXNG_TAG}

LABEL org.opencontainers.image.title="Odysseus SearXNG"
LABEL org.opencontainers.image.description="SearXNG with the Odysseus search-profile selector"
LABEL org.opencontainers.image.source="https://github.com/puchadave/HERMES-Inteligence-Platform-Architektur"

COPY overlay/searx/templates/simple/search.html /usr/local/searxng/searx/templates/simple/search.html
