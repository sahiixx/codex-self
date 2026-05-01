# ── Build stage ─────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir hatchling

COPY src ./src
RUN pip install --no-cache-dir -e . && pip wheel --no-cache-dir -e . -w /wheels

# ── Runtime stage ───────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime deps from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application
COPY src ./src
COPY dashboard ./dashboard
COPY scripts ./scripts
COPY pyproject.toml ./

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9001/health').read()" || exit 1

EXPOSE 9001

CMD ["python", "-m", "uvicorn", "codex_self.main:app", "--host", "0.0.0.0", "--port", "9001", "--proxy-headers"]
