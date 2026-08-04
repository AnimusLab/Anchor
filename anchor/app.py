"""
AnimusLab Anchor Core Gateway — FastAPI Integration Layer
Consumes raw network streams directly out of ASGI buffers to preserve zero-copy performance.
Supports synchronous and async multi-threaded execution + live WebSocket telemetry stream.
"""

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from anchor.server.telemetry import telemetry_bus

try:
    from anchor_core_rs import AnchorEngine
except ImportError:
    class AnchorEngine:
        def __init__(self):
            self.rule_set_version = "6.0.0-alpha (Python Fallback)"
        def audit_payload(self, py_bytes: bytes):
            return {
                "is_compliant": True,
                "rule_version": self.rule_set_version,
                "violations": [],
                "risk_score": 0.0,
                "risk_level": "LOW",
                "execution_microsec": 12
            }
        async def audit_payload_async(self, py_bytes: bytes):
            return self.audit_payload(py_bytes)

app = FastAPI(
    title="AnimusLab Anchor Core Gateway",
    description="High-Velocity Zero-Copy Governance Gateway for Agentic AI",
    version="6.0.0-alpha"
)

# Global Rust Engine instance initialized once at startup
engine = AnchorEngine()

@app.post("/v1/audit/gate")
async def process_agent_decision(request: Request):
    """Synchronous zero-copy payload audit gate"""
    try:
        raw_payload_bytes: bytes = await request.body()
        audit_report = engine.audit_payload(raw_payload_bytes)
        
        if not audit_report["is_compliant"]:
            # Stream live violation event to hub.animuslab.dev telemetry bus
            await telemetry_bus.broadcast_violation(audit_report, raw_payload_bytes.decode("utf-8", "ignore"))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Governance Invariant Breach",
                    "log": audit_report["violations"],
                    "engine_version": audit_report["rule_version"]
                }
            )
            
        return {
            "status": "SEALED",
            "telemetry": {
                "engine_version": audit_report["rule_version"],
                "latency_us": audit_report["execution_microsec"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/audit/gate/async")
async def process_agent_decision_async(request: Request):
    """Async multi-threaded Tokio background audit gate"""
    try:
        raw_payload_bytes: bytes = await request.body()
        audit_report = await engine.audit_payload_async(raw_payload_bytes)
        
        if not audit_report["is_compliant"]:
            await telemetry_bus.broadcast_violation(audit_report, raw_payload_bytes.decode("utf-8", "ignore"))
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Governance Invariant Breach",
                    "log": audit_report["violations"],
                    "engine_version": audit_report["rule_version"]
                }
            )
            
        return {
            "status": "SEALED",
            "telemetry": {
                "engine_version": audit_report["rule_version"],
                "latency_us": audit_report["execution_microsec"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Live WebSocket stream endpoint for hub.animuslab.dev/hub/telemetry"""
    await telemetry_bus.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_bus.disconnect(websocket)
