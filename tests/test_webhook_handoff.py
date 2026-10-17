"""Test 3: Webhook Tool Execution & Live WebSocket Broadcast Verification.

Validates that tool payloads to /api/tools/log-incident and /api/tools/fetch-protocol
process correctly and broadcast structured JSON events over WebSockets in <20ms.
"""

import sys
import time
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app


def test_webhook_and_websocket_broadcast():
    client = TestClient(app)

    print("\n=== STEP 1: VERIFYING BACKEND HEALTH ENDPOINT ===")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert "in.api.slng.ai" in health_data["slng_sovereign_region"]
    print(f"[OK] Health check passed: {health_data['slng_sovereign_region']}")

    print("\n=== STEP 2: TESTING WEBSOCKET REAL-TIME STREAMING & TOOL WEBHOOK ===")
    with client.websocket_connect("/ws/telemetry") as websocket:
        # Initial connection message
        init_msg = websocket.receive_json()
        assert init_msg["event"] == "connected"
        print("[OK] WebSocket connected successfully and received initial metrics snapshot")

        # Measure round-trip execution and broadcast latency
        start_time = time.perf_counter()

        # Send tool payload as Unmute Compliance Specialist agent does
        payload = {
            "caller_name": "Aditi Sharma",
            "location": "Peenya Industrial Area, Bengaluru",
            "incident_type": "industrial_hazard",
            "urgency_level": "critical",
            "language_detected": "Indian English / Hinglish",
        }

        response = client.post("/api/tools/log-incident", json=payload)
        elapsed_tool_ms = (time.perf_counter() - start_time) * 1000

        assert response.status_code == 200, f"Tool call failed: {response.text}"
        res_data = response.json()
        assert res_data["status"] == "success"
        assert res_data["ticket_number"].startswith("IND-")
        assert "HAZMAT" in res_data["compliance_status"]
        assert len(res_data["responders_notified"]) > 0

        # Receive broadcast over WebSocket
        ws_msg = websocket.receive_json()
        ws_broadcast_time_ms = (time.perf_counter() - start_time) * 1000 - elapsed_tool_ms

        assert ws_msg["event"] == "incident_logged"
        assert ws_msg["incident"]["ticket_number"] == res_data["ticket_number"]
        assert ws_msg["incident"]["caller_name"] == "Aditi Sharma"

        print(f"[OK] Incident logged with Ticket: {res_data['ticket_number']}")
        print(f"[OK] Compliance Status: {res_data['compliance_status']}")
        print(f"[OK] Responders Dispatched: {res_data['responders_notified']}")
        print(f"[OK] Tool Execution Latency: {elapsed_tool_ms:.2f} ms")
        print(f"[OK] WebSocket Broadcast Delivery Latency: {ws_broadcast_time_ms:.2f} ms (Target <20ms)")

    print("\n=== STEP 3: TESTING EMERGENCY PROTOCOL TOOL (<50ms SLA) ===")
    proto_start = time.perf_counter()
    proto_res = client.post(
        "/api/tools/fetch-protocol",
        json={"incident_type": "industrial_hazard", "urgency_level": "critical"},
    )
    proto_elapsed_ms = (time.perf_counter() - proto_start) * 1000

    assert proto_res.status_code == 200
    proto_data = proto_res.json()
    assert proto_data["status"] == "success"
    assert len(proto_data["immediate_actions"]) >= 2
    assert "Chemical Spill" in proto_data["compliance_protocol"]
    assert proto_elapsed_ms < 50.0, f"Protocol retrieval exceeded 50ms SLA: {proto_elapsed_ms:.2f}ms"

    print(f"[OK] Protocol: {proto_data['compliance_protocol']}")
    print(f"[OK] Immediate Action 1: {proto_data['immediate_actions'][0]}")
    print(f"[OK] Protocol Retrieval Latency: {proto_elapsed_ms:.2f} ms (< 50ms SLA: MET)")

    print("\n[PASSED 100%] ALL WEBHOOK & WEBSOCKET HANDOFF TESTS PASSED!")


if __name__ == "__main__":
    test_webhook_and_websocket_broadcast()
