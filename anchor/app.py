"""
AnimusLab Anchor Core Gateway - FastAPI integration layer.

Audits agent payloads against the native Anchor engine and streams violation
events to an authenticated telemetry WebSocket.

Security defaults (fail closed):
  * Every /v1/audit request needs ``Authorization: Bearer <ANCHOR_GATEWAY_TOKEN>``.
    If no token is configured the gateway answers 503 instead of running open.
    Set ANCHOR_GATEWAY_ALLOW_UNAUTHENTICATED=1 only for local development.
  * Request bodies are capped (ANCHOR_GATEWAY_MAX_BODY_BYTES, default 1 MiB).
  * Internal error details are logged, not returned to the caller.
Bind the server to 127.0.0.1 unless it sits behind a trusted reverse proxy.
"""
import hmac
import logging
import os

try:
    from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
    from anchor.server.telemetry import telemetry_bus
except ImportError as exc:  # pragma: no cover - depends on install extras
    raise ImportError(
        "The Anchor Gateway requires the optional 'server' dependencies.\n"
        "Install server support with: pip install anchor-audit[server]\n"
        f"(original import error: {exc})"
    ) from exc

try:
    from anchor_core_rs import AnchorEngine
except ImportError as exc:  # pragma: no cover - native extension required
    raise RuntimeError(
        "Anchor server mode requires the native engine. Install anchor-audit with the Rust extension "
        "enabled before starting the gateway."
    ) from exc

import anchor

logger = logging.getLogger("anchor.gateway")

app = FastAPI(
    title="AnimusLab Anchor Core Gateway",
    description="Governance gateway for agentic AI payloads",
    version=anchor.__version__,
)

# Global Rust Engine instance initialized once at startup
engine = AnchorEngine()

_DEFAULT_MAX_BODY = 1024 * 1024
_TRUTHY = {"1", "true", "on", "yes"}


def _authorize(request: Request) -> None:
    """Raise HTTPException unless the caller presents the configured bearer token."""
    token = os.environ.get("ANCHOR_GATEWAY_TOKEN", "")
    if not token:
        if os.environ.get("ANCHOR_GATEWAY_ALLOW_UNAUTHENTICATED", "").strip().lower() in _TRUTHY:
            return
        raise HTTPException(
            status_code=503,
            detail="Gateway is not configured: set ANCHOR_GATEWAY_TOKEN",
        )
    header = request.headers.get("authorization", "")
    scheme, _, supplied = header.partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(
        supplied.strip().encode(), token.encode()
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _read_body_limited(request: Request) -> bytes:
    try:
        limit = int(os.environ.get("ANCHOR_GATEWAY_MAX_BODY_BYTES", _DEFAULT_MAX_BODY))
    except ValueError:
        limit = _DEFAULT_MAX_BODY
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise HTTPException(status_code=413, detail="Payload too large")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail="Payload too large")
        chunks.append(chunk)
    return b"".join(chunks)


async def _gate(request: Request, use_async: bool):
    _authorize(request)
    try:
        raw_payload_bytes = await _read_body_limited(request)
        if use_async:
            audit_report = await engine.audit_payload_async(raw_payload_bytes)
        else:
            audit_report = engine.audit_payload(raw_payload_bytes)

        if not audit_report["is_compliant"]:
            await telemetry_bus.broadcast_violation(audit_report)
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Governance Invariant Breach",
                    "log": audit_report["violations"],
                    "engine_version": audit_report["rule_version"],
                },
            )

        return {
            "status": "ALLOWED",
            "telemetry": {
                "engine_version": audit_report["rule_version"],
                "latency_us": audit_report["execution_microsec"],
            },
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Gateway audit failed")
        raise HTTPException(status_code=500, detail="Internal audit error")


@app.post("/v1/audit/gate")
async def process_agent_decision(request: Request):
    """Synchronous payload audit gate."""
    return await _gate(request, use_async=False)


@app.post("/v1/audit/gate/async")
async def process_agent_decision_async(request: Request):
    """Async background audit gate."""
    return await _gate(request, use_async=True)


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Live telemetry stream. Authentication and origin checks happen in the bus."""
    await telemetry_bus.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_bus.disconnect(websocket)
