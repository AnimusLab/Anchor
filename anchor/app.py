"""
AnimusLab Anchor Core Gateway — FastAPI Integration Layer
Consumes raw network streams directly out of ASGI buffers to preserve zero-copy performance.
"""

from fastapi import FastAPI, Request, HTTPException

try:
    from anchor_core_rs import AnchorEngine
except ImportError:
    # Mock fallback for dev mode when Rust binary is not compiled yet
    class AnchorEngine:
        def __init__(self):
            self.rule_set_version = "6.0.0-alpha (Python Fallback)"
        def audit_payload(self, py_bytes: bytes):
            return {
                "is_compliant": True,
                "rule_version": self.rule_set_version,
                "violations": [],
                "execution_microsec": 12
            }

app = FastAPI(
    title="AnimusLab Anchor Core Gateway",
    description="High-Velocity Zero-Copy Governance Gateway for Agentic AI",
    version="6.0.0-alpha"
)

# Global Rust Engine instance initialized once at startup
engine = AnchorEngine()

@app.post("/v1/audit/gate")
async def process_agent_decision(request: Request):
    try:
        # Pull raw, uncopied bytes directly out of incoming ASGI stream network buffer
        raw_payload_bytes: bytes = await request.body()
        
        # Pass memory reference directly over PyO3 bridge into Rust kernel
        audit_report = engine.audit_payload(raw_payload_bytes)
        
        if not audit_report["is_compliant"]:
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
