"""Typed State management for Sovereign Indic Triage Voice Agent using unmute_core."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from unmute_core.state import CallState, Id, Phone, call_info


class IncidentRecord(BaseModel):
    """The structured incident and dispatch record created by the Compliance Specialist."""

    ticket_number: Id
    caller_name: str
    location: str
    incident_type: Literal[
        "medical_emergency",
        "industrial_hazard",
        "public_safety",
        "traffic_accident",
        "infrastructure_failure",
    ]
    urgency_level: Literal["critical", "high", "medium", "low"]
    compliance_status: str
    responders_notified: list[str]
    sla_dispatch_time: str
    summary: str
    language_detected: str = "Indian English / Hinglish"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EmergencyProtocolRecord(BaseModel):
    """Emergency protocol retrieved for the caller."""

    incident_type: str
    urgency_level: str
    compliance_protocol: str
    immediate_actions: list[str]
    triage_color_code: str
    retrieval_latency_ms: float


class SovereignTriageState(BaseModel):
    """Call state shared across intake_triage and compliance_specialist agents."""

    caller_name: str = Field("", description="Name of the caller reporting the incident")
    location: str = Field("", description="City, landmark, or area in India")
    incident_summary: str = Field("", description="Summary of the emergency situation")
    active_agent: str = Field("intake_triage", description="Currently active agent role")
    handoff_completed: bool = Field(False, description="Whether handoff occurred")
    incident: IncidentRecord | None = Field(None, description="Dispatched incident ticket")
    protocol: EmergencyProtocolRecord | None = Field(None, description="Retrieved emergency protocol")
    turns_count: int = Field(0, description="Number of conversation turns")


def create_call_state(caller_number: str = "+919876543210") -> CallState:
    """Instantiates a typed CallState with attached CallInfo."""
    info = call_info(
        "inbound",
        agent_id="sovereign-triage-v1",
        remote_number=caller_number,
    )
    return CallState(SovereignTriageState, call=info)
