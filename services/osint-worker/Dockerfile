FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 odysseus

COPY pyproject.toml /app/
RUN python -m pip install --no-cache-dir .

COPY app /app/app
RUN mkdir -p /data /reports \
    && chown -R odysseus:odysseus /app /data /reports

USER odysseus

CMD ["python", "-m", "app.worker"]
