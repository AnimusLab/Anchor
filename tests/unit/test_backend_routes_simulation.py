import json
import pytest
from unittest.mock import MagicMock, patch

def simulate_identity_registration(payload, mock_db):
    """Simulates Next.js /api/v1/identity/register logic."""
    project_name = payload.get("project_name")
    public_key_pem = payload.get("public_key_pem")
    fingerprint = payload.get("public_key_fingerprint")

    if not project_name or not public_key_pem or not fingerprint:
        return {"status": 400, "body": {"error": "Missing Mandatory Registration Cryptographic Fields"}}

    if fingerprint in mock_db["identities"]:
        return {"status": 409, "body": {"error": "Cryptographic Public Key Fingerprint Conflict. Node Registration Denied."}}

    mock_db["identities"][fingerprint] = {
        "projectName": project_name,
        "publicKeyPem": public_key_pem,
        "publicKeyFingerprint": fingerprint,
        "status": "PENDING_WHITELIST",
        "registeredBy": "CLI_AUTO_REGISTRATION"
    }

    return {
        "status": 201,
        "body": {
            "status": "STAGED",
            "message": "Node key identity received successfully. Awaiting Admin structural provisioning approval.",
            "fingerprint": fingerprint
        }
    }

def simulate_telemetry_stream(payload, mock_db):
    """Simulates Next.js /api/v1/telemetry/event logic."""
    fingerprint = payload.get("identity_fingerprint")
    identity = mock_db["identities"].get(fingerprint)

    if not identity or identity.get("status") != "ACTIVE":
        return {"status": 401, "body": {"error": "Unverified Identity Fingerprint. Telemetry Packet Dropped."}}

    event_id = payload.get("event_id", "evt_12345")
    mock_db["events"][event_id] = {
        "id": event_id,
        "siloId": payload.get("silo_id", "DEFAULT_SILO"),
        "projectName": payload.get("project_name", identity["projectName"]),
        "complianceVerdict": payload.get("compliance_verdict", "NON_COMPLIANT"),
        "riskScore": float(payload.get("risk_score", 0.0)),
        "identityFingerprint": fingerprint,
        "violationsJson": json.dumps(payload.get("violations", []))
    }

    return {
        "status": 200,
        "body": {
            "status": "LOGGED",
            "transaction_id": event_id
        }
    }


def test_identity_registration_success_and_conflict():
    mock_db = {"identities": {}, "events": {}}
    payload = {
        "project_name": "JPMorgan-Payment-Pipeline",
        "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQE...",
        "public_key_fingerprint": "sha256:b49d424a21b4142ddb670bce34f798"
    }

    # Initial Registration
    res1 = simulate_identity_registration(payload, mock_db)
    assert res1["status"] == 201
    assert res1["body"]["status"] == "STAGED"
    assert res1["body"]["fingerprint"] == "sha256:b49d424a21b4142ddb670bce34f798"
    assert mock_db["identities"]["sha256:b49d424a21b4142ddb670bce34f798"]["status"] == "PENDING_WHITELIST"

    # Duplicate Registration Conflict
    res2 = simulate_identity_registration(payload, mock_db)
    assert res2["status"] == 409
    assert "Conflict" in res2["body"]["error"]


def test_telemetry_event_unauthorized_and_active():
    mock_db = {"identities": {}, "events": {}}
    fp = "sha256:b49d424a21b4142ddb670bce34f798"
    
    reg_payload = {
        "project_name": "JPMorgan-Payment-Pipeline",
        "public_key_pem": "-----BEGIN PUBLIC KEY-----...",
        "public_key_fingerprint": fp
    }
    simulate_identity_registration(reg_payload, mock_db)

    telem_payload = {
        "event_id": "evt_998877",
        "silo_id": "JPMC-MUMBAI-004",
        "project_name": "JPMorgan-Payment-Pipeline",
        "identity_fingerprint": fp,
        "compliance_verdict": "NON_COMPLIANT",
        "risk_score": "7.5",
        "violations": [
            {
                "rule_id": "EU-ART14",
                "file": "D:/autogen/run_cmd.py",
                "line": 467,
                "message": "Unsandboxed execution"
            }
        ]
    }

    # Should fail with 401 because status is PENDING_WHITELIST
    res1 = simulate_telemetry_stream(telem_payload, mock_db)
    assert res1["status"] == 401
    assert "Unverified Identity Fingerprint" in res1["body"]["error"]

    # Admin approves identity (status = ACTIVE)
    mock_db["identities"][fp]["status"] = "ACTIVE"

    # Now telemetry streaming succeeds with 200 OK
    res2 = simulate_telemetry_stream(telem_payload, mock_db)
    assert res2["status"] == 200
    assert res2["body"]["status"] == "LOGGED"
    assert res2["body"]["transaction_id"] == "evt_998877"
    assert "evt_998877" in mock_db["events"]
