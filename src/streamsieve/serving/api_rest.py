"""REST surface (FastAPI; target: a platform can onboard in under an hour).

Draft endpoints:
  POST /v1/sessions                 register a sandbox evaluation session (synthetic/file sources)
  GET  /v1/sessions/{id}/decisions  stream decision records (NDJSON/SSE)
  GET  /v1/healthz | /readyz | /mode
  GET  /metrics                     Prometheus
  POST /v1/sessions/{id}/sanitize   trigger timed purge (G6, audited)

Status: to be filled in months 2-3 (interface draft only; engine not wired yet).
"""
from __future__ import annotations


def create_app(config: dict):  # pragma: no cover - stub
    try:
        from fastapi import FastAPI  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError("fastapi required: pip install 'streamsieve[serving]'") from exc

    app = FastAPI(title="StreamSieve", version="0.1.0")

    @app.get("/v1/healthz")
    def healthz() -> dict:
        return {"status": "alive"}

    # TODO(M2-3): wire sessions / decisions / sanitize / metrics routes
    return app
