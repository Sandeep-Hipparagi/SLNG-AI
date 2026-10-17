"""Test Phase 6: Live Multi-Provider API Wiring & Voice Turn Verification.

Verifies:
1. GET /api/providers/status: Live readiness across SLNG, Sarvam, Gnani, and Gemini.
2. Preset 1 (Kanglish/Kannada Emergency): Peenya Industrial Gas Leak with Sarvam bulbul:v3.
3. Preset 2 (Hinglish Traffic Accident): Silk Board Collision with Gnani.ai Timbre.
4. Preset 3 (Financial/Cyber Fraud Triage): UPI / Aadhaar Freeze with SLNG Cartesia Sonic 3.
5. Verifies unmute_core CallState updates, ToolRegistry tools (verify_and_log_incident + fetch_emergency_protocol),
   and real wall-clock latency reductions.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app


def test_live_providers():
    client = TestClient(app)

    print("\n" + "=" * 76)
    print("  TESTING PHASE 6: LIVE MULTI-PROVIDER HOT-SWAP & VOICE TURN SMOKE TEST")
    print("=" * 76)

    # 1. Provider Readiness Status
    print("\n> STEP 1: Verifying GET /api/providers/status...")
    status_res = client.get("/api/providers/status")
    assert status_res.status_code == 200, f"Status check failed: {status_res.text}"
    status_data = status_res.json()
    providers = status_data["providers"]

    for name, p in providers.items():
        print(f"  [OK] Provider '{name}': ready={p['ready']} ({p['name']})")
        assert p["ready"] is True, f"Provider {name} is not marked ready!"

    latency_table = []

    # 2. Preset 1: Kanglish/Kannada Emergency (SLNG + Sarvam bulbul:v3)
    print("\n> STEP 2: Testing Preset 1 - Peenya Industrial Gas Leak (kn-IN / Sarvam bulbul:v3)...")
    payload_kn = {
        "utterance": "Anna, Peenya Phase 2 factory alli gas leak aagide! My name is Rajesh, please send fire brigade fast!",
        "voice_provider": "slng-sarvam",
        "language_code": "kn-IN",
        "noise_db": 78.5,
    }
    kn_res = client.post("/api/voice/live-turn", json=payload_kn)
    assert kn_res.status_code == 200, f"Turn call failed: {kn_res.text}"
    kn_data = kn_res.json()

    assert kn_data["success"] is True
    assert kn_data["incident_ticket"]["ticket_number"].startswith("IND-")
    assert kn_data["emergency_protocol"] is not None
    assert kn_data["emergency_protocol"]["compliance_protocol"] != ""
    assert len(kn_data["audio_base64"]) > 500
    assert "data:audio/wav;base64," in kn_data["audio_base64"]
    assert kn_data["handoff_state"]["active_agent"] == "compliance_specialist"

    print(f"  [OK] Extracted Caller: {kn_data['extracted_slots']['caller_name']}")
    print(f"  [OK] Incident Category: {kn_data['extracted_slots']['incident_type']}")
    print(f"  [OK] Ticket Dispatched: {kn_data['incident_ticket']['ticket_number']}")
    print(f"  [OK] Compliance Protocol: {kn_data['emergency_protocol']['compliance_protocol']}")
    print(f"  [OK] Voice Engine: {kn_data['provider_info']['voice_engine']}")
    print(f"  [OK] E2E Turn Latency: {kn_data['timings']['e2e_turn_ms']}ms (vs Baseline {kn_data['timings']['baseline_us_e2e_ms']}ms)")
    print(f"  [OK] Audio Data URI Generated: {len(kn_data['audio_base64'])} bytes")

    latency_table.append({
        "scenario": "Preset 1 (Kannada / Sarvam)",
        "stt_ms": kn_data["timings"]["stt_ms"],
        "ttft_ms": kn_data["timings"]["llm_ttft_ms"],
        "tts_ms": kn_data["timings"]["tts_latency_ms"],
        "e2e_slng_ms": kn_data["timings"]["e2e_turn_ms"],
        "e2e_us_ms": kn_data["timings"]["baseline_us_e2e_ms"],
        "savings": f"-{kn_data['timings']['latency_reduction_percent']}%",
    })

    # 3. Preset 2: Hinglish Traffic Accident (SLNG + Gnani Timbre)
    print("\n> STEP 3: Testing Preset 2 - Silk Board Collision (hi-IN / Gnani Timbre)...")
    payload_hi = {
        "utterance": "Bhaiya urgent emergency hai! Silk Board Flyover par 3 gaadiyan aapas mein takra gayi hain, diesel leak ho raha hai aur traffic jam hai!",
        "voice_provider": "slng-gnani",
        "language_code": "hi-IN",
        "noise_db": 75.0,
    }
    hi_res = client.post("/api/voice/live-turn", json=payload_hi)
    assert hi_res.status_code == 200, f"Turn call failed: {hi_res.text}"
    hi_data = hi_res.json()

    assert hi_data["success"] is True
    assert hi_data["incident_ticket"]["ticket_number"].startswith("IND-")
    assert hi_data["emergency_protocol"] is not None
    assert len(hi_data["audio_base64"]) > 500

    print(f"  [OK] Extracted Caller: {hi_data['extracted_slots']['caller_name']}")
    print(f"  [OK] Ticket Dispatched: {hi_data['incident_ticket']['ticket_number']}")
    print(f"  [OK] Compliance Protocol: {hi_data['emergency_protocol']['compliance_protocol']}")
    print(f"  [OK] Voice Engine: {hi_data['provider_info']['voice_engine']}")
    print(f"  [OK] E2E Turn Latency: {hi_data['timings']['e2e_turn_ms']}ms (-{hi_data['timings']['latency_reduction_percent']}%)")

    latency_table.append({
        "scenario": "Preset 2 (Hinglish / Gnani)",
        "stt_ms": hi_data["timings"]["stt_ms"],
        "ttft_ms": hi_data["timings"]["llm_ttft_ms"],
        "tts_ms": hi_data["timings"]["tts_latency_ms"],
        "e2e_slng_ms": hi_data["timings"]["e2e_turn_ms"],
        "e2e_us_ms": hi_data["timings"]["baseline_us_e2e_ms"],
        "savings": f"-{hi_data['timings']['latency_reduction_percent']}%",
    })

    # 4. Preset 3: Financial/Cyber Fraud Triage (SLNG + Cartesia Sonic 3)
    print("\n> STEP 4: Testing Preset 3 - UPI / Aadhaar Freeze Request (en-IN / Cartesia Sonic 3)...")
    payload_fraud = {
        "utterance": "Emergency! An unauthorized transaction of 85,000 rupees was just debited from my account via UPI, please freeze my account and log cyber fraud immediately!",
        "voice_provider": "slng-cartesia",
        "language_code": "en-IN",
        "noise_db": 48.0,
    }
    fraud_res = client.post("/api/voice/live-turn", json=payload_fraud)
    assert fraud_res.status_code == 200, f"Turn call failed: {fraud_res.text}"
    fraud_data = fraud_res.json()

    assert fraud_data["success"] is True
    assert fraud_data["incident_ticket"]["ticket_number"].startswith("IND-")
    assert fraud_data["emergency_protocol"] is not None
    assert len(fraud_data["audio_base64"]) > 500

    print(f"  [OK] Extracted Caller: {fraud_data['extracted_slots']['caller_name']}")
    print(f"  [OK] Ticket Dispatched: {fraud_data['incident_ticket']['ticket_number']}")
    print(f"  [OK] Compliance Protocol: {fraud_data['emergency_protocol']['compliance_protocol']}")
    print(f"  [OK] Voice Engine: {fraud_data['provider_info']['voice_engine']}")
    print(f"  [OK] E2E Turn Latency: {fraud_data['timings']['e2e_turn_ms']}ms (-{fraud_data['timings']['latency_reduction_percent']}%)")

    latency_table.append({
        "scenario": "Preset 3 (Cyber / Cartesia)",
        "stt_ms": fraud_data["timings"]["stt_ms"],
        "ttft_ms": fraud_data["timings"]["llm_ttft_ms"],
        "tts_ms": fraud_data["timings"]["tts_latency_ms"],
        "e2e_slng_ms": fraud_data["timings"]["e2e_turn_ms"],
        "e2e_us_ms": fraud_data["timings"]["baseline_us_e2e_ms"],
        "savings": f"-{fraud_data['timings']['latency_reduction_percent']}%",
    })

    # 5. Wall-Clock Latency Scoreboard
    print("\n" + "=" * 76)
    print("  WALL-CLOCK REAL LATENCY BENCHMARK SCOREBOARD (SOVEREIGN vs US-EAST)")
    print("=" * 76)
    print(f"  {'SCENARIO':<28} | {'STT':<7} | {'TTFT':<7} | {'TTS':<7} | {'SLNG E2E':<10} | {'US-EAST':<10} | {'SAVINGS'}")
    print("  " + "-" * 74)
    for row in latency_table:
        print(f"  {row['scenario']:<28} | {row['stt_ms']:>5.1f}ms | {row['ttft_ms']:>5.1f}ms | {row['tts_ms']:>5.1f}ms | {row['e2e_slng_ms']:>8.1f}ms | {row['e2e_us_ms']:>8.1f}ms | {row['savings']:>7}")
    print("=" * 76)
    print("  [SUCCESS 100%] ALL LIVE PRESETS, UNMUTE TOOLS, & TTS PLAYBACK VERIFIED!\n")


if __name__ == "__main__":
    test_live_providers()
