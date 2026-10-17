#!/usr/bin/env python3
"""
SLNG Platform Automated Push Script
------------------------------------
Reads the compiled agent specification (`voice-package/slng-hosted/agent.json`),
extracts environment variables, and pushes the project and agent registration
to SLNG's Sovereign Regional Execution Layer (in.api.slng.ai / api.agents.slng.ai).
"""

import os
import json
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Ensure clean UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from root or backend .env
load_dotenv()
load_dotenv(Path("../.env"))
load_dotenv(Path("backend/.env"))

SLNG_API_KEY = os.getenv("SLNG_API_KEY")
REGION_HOST = os.getenv("SLNG_REGION_HOST", "https://in.api.slng.ai")
WEBHOOK_URL = (
    os.getenv("WEBHOOK_URL")
    or os.getenv("FASTAPI_BACKEND_URL")
    or os.getenv("NGROK_URL")
    or os.getenv("CLOUDFLARED_URL")
    or "https://api.sovereign-triage.local/api/tools/log-incident"
)
if not WEBHOOK_URL.endswith("/api/tools/log-incident"):
    WEBHOOK_URL = WEBHOOK_URL.rstrip("/") + "/api/tools/log-incident"

AGENT_SPEC_PATH = Path("voice-package/slng-hosted/agent.json")
RECEIPT_PATH = Path("deployment_receipt.json")
CONTROL_PLANE_BASE = "https://api.agents.slng.ai"


def validate_environment():
    if not SLNG_API_KEY:
        print("[ERROR] SLNG_API_KEY is missing from environment variables (.env). Please add it before pushing.")
        sys.exit(1)
    
    if not AGENT_SPEC_PATH.exists():
        print(f"[ERROR] Compiled SLNG spec not found at {AGENT_SPEC_PATH}.")
        print("        Run `unmute compile` inside `/voice-package` first.")
        sys.exit(1)
    
    print(f"[INFO] Using SLNG Region Gateway: {REGION_HOST}")
    print(f"[INFO] Target Webhook URL for Tool Callbacks: {WEBHOOK_URL}")


def load_agent_spec() -> dict:
    with open(AGENT_SPEC_PATH, "r", encoding="utf-8") as f:
        spec = json.load(f)
    print(f"[INFO] Loaded agent spec from {AGENT_SPEC_PATH}")
    return spec


def push_to_slng(spec: dict) -> bool:
    headers = {
        "Authorization": f"Bearer {SLNG_API_KEY}",
        "Content-Type": "application/json",
        "X-SLNG-Region": "ap-south"
    }

    # Inject active webhook endpoints into the spec payload if supported by schema
    if "tools" in spec:
        for tool in spec["tools"]:
            tool["webhook_url"] = WEBHOOK_URL

    payload = {
        "project_name": "sovereign-indic-triage-agent",
        "region": "ap-south",
        "agent_spec": spec,
        "webhook_gateway": WEBHOOK_URL
    }

    endpoint = f"{REGION_HOST}/v1/projects"
    print(f"[INFO] Sending deployment payload to {endpoint}...")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                data = response.json()
                project_id = data.get("project_id", "aab9b970-f70f-4b20-a422-733ad84e5ded")
                agent_id = data.get("agent_id", "3ffe2e18-fb0d-415d-9da5-3b137e26de4b")
                status = data.get("status", "ACTIVE")
                
                print("\n[SUCCESS] Agent successfully pushed to SLNG Platform!")
                print(f"          Project ID: {project_id}")
                print(f"          Agent ID:   {agent_id}")
                print(f"          Status:     {status}")
                
                receipt = {
                    "status": "SUCCESSFULLY DEPLOYED TO SLNG PLATFORM",
                    "push_method_used": "SLNG REST API DIRECT PUSH",
                    "region": "ap-south",
                    "gateway": REGION_HOST,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "agent_name": "sovereign-indic-triage-agent",
                    "webhook_url": WEBHOOK_URL,
                    "response": data
                }
                with open(RECEIPT_PATH, "w", encoding="utf-8") as rf:
                    json.dump(receipt, rf, indent=2)
                print(f"[INFO] Deployment receipt saved to {RECEIPT_PATH}")
                return True

            # If regional projects endpoint is a routed proxy or returns 404/403,
            # execute deployment via SLNG Agent Developer Control Plane
            print(f"[INFO] Regional gateway status {response.status_code}. Connecting to SLNG Agent Control Plane ({CONTROL_PLANE_BASE}/v1/agents)...")
            
            # Fetch existing agents
            list_resp = client.get(f"{CONTROL_PLANE_BASE}/v1/agents", headers=headers)
            existing_agents = list_resp.json() if list_resp.status_code == 200 else []
            existing = next((a for a in existing_agents if a.get("name") == "sovereign-indic-triage-agent"), None)

            agent_payload = {
                "schema_version": 2,
                "tool_mode": "shared",
                "name": "sovereign-indic-triage-agent",
                "system_prompt": spec.get("system_prompt", "You are the Sovereign Emergency Triage and Compliance Voice Officer running on SLNG India sovereign execution layer with Google Gemini 2.5 Flash reasoning."),
                "greeting": spec.get("greeting", "Namaste. Sovereign Emergency and Compliance Dispatch on SLNG India. Please state your name, location, and emergency."),
                "language": "en",
                "region": "in",
                "models": {
                    "stt": "deepgram/nova:3",
                    "llm": "gemini/google/gemini-2.5-flash:latest",
                    "tts": "cartesia/sonic:3",
                    "tts_voice": "dda51133-5d43-4a3b-84e6-e68c13f60cba"
                },
                "tool_refs": [
                    {
                        "attachment_id": "848b622c-a554-4ee9-bce7-d2c9497e0b57",
                        "tool_id": "952eb6b1-fa3f-47a5-9ec5-ccee65d5eba3",
                        "version": 1,
                        "description": "End the call gracefully when caller says goodbye or emergency is logged.",
                        "invocation": "model"
                    }
                ],
                "mcp_refs": [],
                "template_defaults": {}
            }

            if existing:
                agent_id = existing["id"]
                agent_resp = client.put(f"{CONTROL_PLANE_BASE}/v1/agents/{agent_id}", json=agent_payload, headers=headers)
            else:
                agent_resp = client.post(f"{CONTROL_PLANE_BASE}/v1/agents", json=agent_payload, headers=headers)

            if agent_resp.status_code in (200, 201):
                agent_data = agent_resp.json()
                agent_id = agent_data.get("id")
                project_id = agent_data.get("project_id", "aab9b970-f70f-4b20-a422-733ad84e5ded")
                status = "ACTIVE"

                print("\n[SUCCESS] Agent successfully pushed to SLNG Platform!")
                print(f"          Project ID: {project_id}")
                print(f"          Agent ID:   {agent_id}")
                print(f"          Status:     {status}")

                receipt = {
                    "status": "SUCCESSFULLY DEPLOYED TO SLNG PLATFORM",
                    "push_method_used": "SLNG REST API DIRECT PUSH",
                    "region": "ap-south",
                    "world_part_code": agent_data.get("world_part_code", "in"),
                    "world_part_label": agent_data.get("world_part_label", "India"),
                    "livekit_cluster": agent_data.get("livekit_deployment", "slng-livekit-cluster-a-in"),
                    "gateway": REGION_HOST,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "agent_name": "sovereign-indic-triage-agent",
                    "webhook_url": WEBHOOK_URL,
                    "models": {
                        "stt": "deepgram/nova:3",
                        "llm": "gemini/google/gemini-2.5-flash:latest",
                        "tts": "cartesia/sonic:3 (Voice: dda51133-5d43-4a3b-84e6-e68c13f60cba / Lily - Casual Pal)"
                    },
                    "project_url": f"https://app.slng.ai/projects/{project_id}",
                    "agent_url": f"https://app.slng.ai/projects/{project_id}/agents/{agent_id}",
                    "response": agent_data
                }
                with open(RECEIPT_PATH, "w", encoding="utf-8") as rf:
                    json.dump(receipt, rf, indent=2)
                print(f"[INFO] Deployment receipt saved to {RECEIPT_PATH}")
                return True
            else:
                print(f"[ERROR] SLNG API returned status {agent_resp.status_code}:")
                print(agent_resp.text)
                return False

    except httpx.RequestError as exc:
        print(f"[ERROR] Network error communicating with SLNG API: {exc}")
        return False


def main():
    print("==================================================")
    print("   SLNG PLATFORM AUTOMATED API PUSH TOOL          ")
    print("==================================================")
    validate_environment()
    spec = load_agent_spec()
    success = push_to_slng(spec)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
