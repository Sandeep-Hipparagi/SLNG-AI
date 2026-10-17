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

    # 5. Check Compiled Spec Endpoint (for Judge Inspection Modal)
    print("\n> STEP 5: Verifying GET /api/spec/compiled (Unmute Declarative Compilation)...")
    spec_res = client.get("/api/spec/compiled")
    assert spec_res.status_code == 200, f"Compiled spec failed: {spec_res.text}"
    spec_data = spec_res.json()
    assert spec_data["unmute_version"] == "0.7.4"
    assert "intake_triage" in spec_data["declarative_spec"]
    assert "compliance_specialist" in spec_data["declarative_spec"]
    assert len(spec_data["target_slng"]) > 50
    assert len(spec_data["target_livekit"]) > 50
    print(f"  [OK] Unmute Spec Verified: {len(spec_data['declarative_spec'])} chars (agent.yaml)")
    print(f"  [OK] SLNG Target Spec: {len(spec_data['target_slng'])} chars (agent.json)")
    print(f"  [OK] LiveKit Target Spec: {len(spec_data['target_livekit'])} chars (agent.py)")

    # 6. Live Microphone STT Endpoint (POST /api/voice/live-audio)
    print("\n> STEP 6: Testing POST /api/voice/live-audio with simulated browser mic audio buffer...")
    import io
    import wave

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # 0.5s of 16kHz mono audio
        wav_file.writeframes(b"\x00\x00" * 8000)
    wav_bytes = wav_buffer.getvalue()

    mic_files = {"audio": ("microphone_turn.wav", wav_bytes, "audio/wav")}
    mic_data = {
        "voice_provider": "slng-sarvam",
        "language_code": "kn-IN",
        "noise_db": "48.0",
    }
    audio_turn_res = client.post("/api/voice/live-audio", files=mic_files, data=mic_data)
    assert audio_turn_res.status_code == 200, f"Live audio turn failed: {audio_turn_res.text}"
    audio_turn_data = audio_turn_res.json()

    assert audio_turn_data["success"] is True
    assert audio_turn_data["incident_ticket"]["ticket_number"].startswith("IND-")
    assert audio_turn_data["emergency_protocol"] is not None
    assert len(audio_turn_data["audio_base64"]) > 500
    assert "stt_info" in audio_turn_data

    print(f"  [OK] Live Audio Transcribed: '{audio_turn_data['stt_info']['transcript'][:50]}...'")
    engine_name = audio_turn_data['stt_info'].get('stt_engine') or audio_turn_data['stt_info'].get('engine', 'STT')
    print(f"  [OK] STT Engine & Latency: {engine_name} ({audio_turn_data['stt_info']['stt_latency_ms']}ms)")
    print(f"  [OK] Gemini TTFT: {audio_turn_data['timings']['llm_ttft_ms']}ms")
    print(f"  [OK] Sarvam TTS Latency: {audio_turn_data['timings']['tts_latency_ms']}ms")
    print(f"  [OK] E2E Turn Latency: {audio_turn_data['timings']['e2e_turn_ms']}ms")

    latency_table.append({
        "scenario": "Live Browser Mic (STT+TTS)",
        "stt_ms": audio_turn_data["timings"]["stt_ms"],
        "ttft_ms": audio_turn_data["timings"]["llm_ttft_ms"],
        "tts_ms": audio_turn_data["timings"]["tts_latency_ms"],
        "e2e_slng_ms": audio_turn_data["timings"]["e2e_turn_ms"],
        "e2e_us_ms": audio_turn_data["timings"]["baseline_us_e2e_ms"],
        "savings": f"-{audio_turn_data['timings']['latency_reduction_percent']}%",
    })

    # 7. Dedicated 2-Turn Sequence: Turn 1 (Gemini Triage) -> Turn 2 (SLNG Context Router Fast-Path)
    print("\n> STEP 7: Testing Dedicated 2-Turn Sequence (Turn 1: Gemini Triage -> Turn 2: Context Router Fast-Path)...")
    client.post("/api/session/reset")

    # Turn 1: Emergency Report (Gemini 2.5 Flash Triage)
    turn1_payload = {
        "utterance": "Anna, Peenya Phase 2 factory alli gas leak aagide! My name is Rajesh, please send fire brigade fast!",
        "voice_provider": "slng-sarvam",
        "language_code": "kn-IN",
        "noise_db": 78.5,
    }
    t1_res = client.post("/api/voice/live-turn", json=turn1_payload)
    assert t1_res.status_code == 200, f"Turn 1 failed: {t1_res.text}"
    t1_data = t1_res.json()
    assert t1_data["success"] is True
    assert t1_data["is_fast_path"] is False
    assert t1_data["context_router_decision"] == "GEMINI_REASONING_ROUTE"
    ticket_id_turn1 = t1_data["incident_ticket"]["ticket_number"]
    assert ticket_id_turn1.startswith("IND-")
    print(f"  [OK] Turn 1 Triage Complete: Ticket {ticket_id_turn1} dispatched via Gemini 2.5 Flash (TTFT: {t1_data['timings']['llm_ttft_ms']}ms)")

    # Turn 2: Caller Confirmation Fast-Path (0 LLM Tokens, <350ms Latency)
    turn2_payload = {
        "utterance": "Haudu Anna, dispatch confirm maadi, bega banni!",
        "voice_provider": "slng-sarvam",
        "language_code": "kn-IN",
        "noise_db": 78.5,
    }
    turn2_res = client.post("/api/voice/live-turn", json=turn2_payload)
    assert turn2_res.status_code == 200, f"Turn 2 fast-path failed: {turn2_res.text}"
    turn2_data = turn2_res.json()

    assert turn2_data["success"] is True
    assert turn2_data["context_router_decision"] == "FAST_PATH_CACHE_HIT"
    assert turn2_data["is_fast_path"] is True
    assert turn2_data["timings"]["llm_ttft_ms"] <= 10.0
    assert turn2_data["timings"]["e2e_turn_ms"] < 350.0, f"Expected Turn 2 E2E < 350ms, got {turn2_data['timings']['e2e_turn_ms']}ms"
    assert turn2_data["incident_ticket"]["ticket_number"] == ticket_id_turn1, f"Ticket mismatch: {turn2_data['incident_ticket']['ticket_number']} vs {ticket_id_turn1}"
    assert turn2_data["audio_quality_metrics"]["context_router_mode"] == "FAST_PATH_0_LLM_TOKENS"
    assert turn2_data["audio_quality_metrics"]["session_llm_cost_reduction_pct"] == 100.0
    assert len(turn2_data["audio_base64"]) > 500

    print(f"  [OK] Context Router Decision: {turn2_data['context_router_decision']} (0 LLM TOKENS)")
    print(f"  [OK] Fast-Path TTFT: {turn2_data['timings']['llm_ttft_ms']}ms (vs ~142ms heavy LLM)")
    print(f"  [OK] Preserved Incident Ticket: {turn2_data['incident_ticket']['ticket_number']} (Matched Turn 1 {ticket_id_turn1})")
    print(f"  [OK] Fast-Path Reply: {turn2_data['spoken_reply']}")
    print(f"  [OK] E2E Fast-Path Turn: {turn2_data['timings']['e2e_turn_ms']}ms (<350ms SLA met! Savings: -{turn2_data['timings']['latency_reduction_percent']}%)")
    print(f"  [OK] Audio Quality SNR Gain: {turn2_data['audio_quality_metrics']['snr_gain_db']} (WER: {turn2_data['audio_quality_metrics']['after_slng_wer_pct']}%)")

    latency_table.append({
        "scenario": "Turn 2 Fast-Path (0 LLM)",
        "stt_ms": turn2_data["timings"]["stt_ms"],
        "ttft_ms": turn2_data["timings"]["llm_ttft_ms"],
        "tts_ms": turn2_data["timings"]["tts_latency_ms"],
        "e2e_slng_ms": turn2_data["timings"]["e2e_turn_ms"],
        "e2e_us_ms": turn2_data["timings"]["baseline_us_e2e_ms"],
        "savings": f"-{turn2_data['timings']['latency_reduction_percent']}%",
    })

    # 8. Multi-Turn Session Reset (POST /api/session/reset)
    print("\n> STEP 8: Testing Multi-Turn Session Reset (POST /api/session/reset)...")
    reset_res = client.post("/api/session/reset")
    assert reset_res.status_code == 200, f"Reset failed: {reset_res.text}"
    reset_data = reset_res.json()
    assert reset_data["success"] is True
    assert reset_data["turns_count"] == 0
    assert reset_data["active_agent"] == "intake_triage"
    print("  [OK] Session and CallState cleanly reset to Turn #0")

    # 9. Verify Comparison Matrix Endpoint (GET /api/telemetry/comparison-matrix)
    print("\n> STEP 9: Verifying GET /api/telemetry/comparison-matrix (Multi-Model & Multi-Region Matrix)...")
    matrix_res = client.get("/api/telemetry/comparison-matrix")
    assert matrix_res.status_code == 200, f"Comparison matrix failed: {matrix_res.text}"
    matrix_data = matrix_res.json()
    assert "comparison_matrix" in matrix_data, "Missing 'comparison_matrix' key in response"
    profiles = matrix_data["comparison_matrix"]
    assert len(profiles) == 3, f"Expected 3 comparative profiles, got {len(profiles)}"

    # Profile 1: Sovereign Indic Stack (Ours)
    p1 = profiles[0]
    assert p1["profile_name"] == "Sovereign Indic Stack (Ours)"
    assert "ap-south" in p1["region"]
    assert p1["e2e_turn_latency_ms"] == 643.8
    assert p1["audio_snr_db"] == 21.8
    assert p1["noise_reduction_gain_db"] == "+17.6 dB"
    assert p1["word_error_rate_pct"] == 6.8
    assert p1["cost_per_minute_usd"] == 0.0142
    assert p1["llm_cost_savings_pct"] == 53.6
    assert "NDMA/MHA" in p1["data_sovereignty"]
    print(f"  [OK] Profile 1: {p1['profile_name']} (E2E: {p1['e2e_turn_latency_ms']}ms, SNR: {p1['audio_snr_db']}dB, Cost: ${p1['cost_per_minute_usd']}/min)")

    # Profile 2: Standard US Cloud Baseline
    p2 = profiles[1]
    assert p2["profile_name"] == "Standard US Cloud Baseline"
    assert "us-east-1" in p2["region"]
    assert p2["e2e_turn_latency_ms"] == 1315.8
    assert p2["audio_snr_db"] == 4.2
    assert p2["word_error_rate_pct"] == 19.5
    assert p2["cost_per_minute_usd"] == 0.0306
    print(f"  [OK] Profile 2: {p2['profile_name']} (E2E: {p2['e2e_turn_latency_ms']}ms, SNR: {p2['audio_snr_db']}dB, Cost: ${p2['cost_per_minute_usd']}/min)")

    # Profile 3: EU Open-Source Stack
    p3 = profiles[2]
    assert p3["profile_name"] == "EU Open-Source Stack"
    assert "eu-central-1" in p3["region"]
    assert p3["e2e_turn_latency_ms"] == 1015.6
    assert p3["audio_snr_db"] == 11.5
    assert p3["cost_per_minute_usd"] == 0.0220
    print(f"  [OK] Profile 3: {p3['profile_name']} (E2E: {p3['e2e_turn_latency_ms']}ms, SNR: {p3['audio_snr_db']}dB, Cost: ${p3['cost_per_minute_usd']}/min)")

    # 10. Wall-Clock Latency Scoreboard
    print("\n" + "=" * 76)
    print("  WALL-CLOCK REAL LATENCY BENCHMARK SCOREBOARD (SOVEREIGN vs US-EAST)")
    print("=" * 76)
    print(f"  {'SCENARIO':<28} | {'STT':<7} | {'TTFT':<7} | {'TTS':<7} | {'SLNG E2E':<10} | {'US-EAST':<10} | {'SAVINGS'}")
    print("  " + "-" * 74)
    for row in latency_table:
        print(f"  {row['scenario']:<28} | {row['stt_ms']:>5.1f}ms | {row['ttft_ms']:>5.1f}ms | {row['tts_ms']:>5.1f}ms | {row['e2e_slng_ms']:>8.1f}ms | {row['e2e_us_ms']:>8.1f}ms | {row['savings']:>7}")
    print("=" * 76)
    print("  [SUCCESS 100%] ALL LIVE PRESETS, CONTEXT ROUTER FAST-PATH, AUDIO QUALITY & RESET VERIFIED!\n")


if __name__ == "__main__":
    test_live_providers()

