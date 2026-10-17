"""FastAPI Tool Server & Sovereign Telemetry Engine wired with unmute_core primitives."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slng_client import slng_client
from state import create_call_state
from telemetry import telemetry, ws_manager
from tools_adapter import triage_tool_registry

app = FastAPI(
    title="Sovereign Indic Triage & Compliance Voice Agent Backend (Unmute Core)",
    version="2.0.0",
    description="Tool execution webhooks and real-time telemetry engine powered by unmute-core.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active typed call state instance
active_call_state = create_call_state("+919876543210")
BENCHMARK_LATEST_FILE = Path(__file__).resolve().parent / "benchmark_latest.json"


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "sovereign-indic-triage-backend",
        "slng_sovereign_region": "ap-south / in.api.slng.ai",
        "llm_engine": "Google Gemini 2.5 Flash",
        "unmute_core_version": "0.14.0",
        "unmute_cli_version": "0.7.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/tools/log-incident")
async def log_incident_tool(payload: Dict[str, Any]):
    """Webhook tool executed via unmute_core.tools.ToolRegistry.

    Validates schema, runs native ToolSpec handler, mutates typed CallState,
    and broadcasts structured event via WebSocket.
    """
    # Execute through unmute_core's native ToolRegistry
    result = await triage_tool_registry.call(
        "verify_and_log_incident",
        payload,
        state=active_call_state,
    )

    incident_dict = dict(result) if hasattr(result, "__iter__") else result
    telemetry.log_incident(incident_dict)
    telemetry.log_event("incident_logged", incident_dict)

    # Broadcast to live React dashboard
    await ws_manager.broadcast(
        {
            "event": "incident_logged",
            "incident": incident_dict,
            "metrics": telemetry.get_metrics_summary(),
        }
    )

    return incident_dict


@app.post("/api/tools/fetch-protocol")
async def fetch_emergency_protocol_tool(payload: Dict[str, Any]):
    """Webhook tool executed via unmute_core.tools.ToolRegistry (<50ms SLA)."""
    result = await triage_tool_registry.call(
        "fetch_emergency_protocol",
        payload,
        state=active_call_state,
    )

    proto_dict = dict(result) if hasattr(result, "__iter__") else result
    telemetry.log_event("protocol_fetched", proto_dict)

    await ws_manager.broadcast(
        {
            "event": "protocol_fetched",
            "protocol": proto_dict,
        }
    )

    return proto_dict


@app.get("/api/metrics")
async def get_metrics():
    """Returns telemetry dashboard metrics, turn latencies, and token cost savings."""
    return telemetry.get_metrics_summary()


@app.get("/api/state")
async def get_current_call_state():
    """Returns current typed CallState snapshot."""
    return {
        "call_info": {
            "agent_id": active_call_state.call.agent_id,
            "caller": str(active_call_state.call.remote_number),
        },
        "registered_tools": triage_tool_registry.names(),
        "tool_schemas": triage_tool_registry.schemas(),
    }


@app.post("/api/benchmark")
async def run_benchmark(payload: Dict[str, Any] = None):
    """Triggers real millisecond benchmark execution comparing SLNG Sovereign Indian routing vs US-East direct."""
    scenario_name = (payload or {}).get(
        "scenario", "Live Hinglish & Traffic Noise Sovereign Triage"
    )

    # Execute simulation through SovereignSlngClient
    sim_data = await slng_client.simulate_turn_execution(
        transcript_text="Indiranagar 100 feet road collision and emergency response",
        noise_level_db=78.0,
    )

    result = await telemetry.execute_live_benchmark(scenario_name)
    result["slng_client_telemetry"] = sim_data

    # Persist latest benchmark to benchmark_latest.json
    BENCHMARK_LATEST_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")

    await ws_manager.broadcast(
        {
            "event": "benchmark_completed",
            "benchmark": result,
            "metrics": telemetry.get_metrics_summary(),
        }
    )
    return result


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """WebSocket endpoint streaming live voice agent turns, handoffs, tool events, and benchmarks."""
    await ws_manager.connect(websocket)
    try:
        # Send initial state snapshot on connection
        await websocket.send_json(
            {
                "event": "connected",
                "message": "Connected to Sovereign Indic Telemetry Stream (unmute-core)",
                "metrics": telemetry.get_metrics_summary(),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
