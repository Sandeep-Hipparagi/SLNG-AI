"""Pydantic data models for the Sovereign Indic Triage Voice Agent."""

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class IncidentLogRequest(BaseModel):
    caller_name: str = Field(..., description="Full name of caller")
    location: str = Field(..., description="Location, landmark, or city in India")
    incident_type: Literal[
        "medical_emergency",
        "industrial_hazard",
        "public_safety",
        "traffic_accident",
        "infrastructure_failure",
    ] = Field(..., description="Category of incident")
    urgency_level: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Assessed triage urgency level"
    )
    language_detected: str = Field(
        default="Indian English / Hinglish",
        description="Spoken dialect or language detected",
    )


class IncidentLogResponse(BaseModel):
    status: str = "success"
    ticket_number: str
    compliance_status: str
    responders_notified: list[str]
    sla_dispatch_time: str
    summary: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ProtocolRequest(BaseModel):
    incident_type: str
    urgency_level: str = "high"


class ProtocolResponse(BaseModel):
    status: str = "success"
    incident_type: str
    urgency_level: str
    compliance_protocol: str
    immediate_actions: list[str]
    triage_color_code: str
    retrieval_latency_ms: float


class BenchmarkResult(BaseModel):
    scenario: str
    audio_file: str
    slng_sovereign_stt_ms: float
    baseline_us_stt_ms: float
    slng_sovereign_tts_ms: float
    baseline_us_tts_ms: float
    slng_e2e_turn_ms: float
    baseline_us_e2e_turn_ms: float
    latency_reduction_percent: float
    tokens_saved_percent: float
    cost_reduction_percent: float
    wer_noisy_audio_slng: float
    wer_noisy_audio_baseline: float
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
