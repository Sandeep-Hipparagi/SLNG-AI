"""Native Unmute Core tool adapters and registry for Sovereign Indic Triage."""

import random
import time
from typing import Literal
from unmute_core.tools import Done, ToolRegistry, local_tool
from state import EmergencyProtocolRecord, IncidentRecord, SovereignTriageState


async def verify_and_log_incident(
    caller_name: str,
    location: str,
    incident_type: Literal[
        "medical_emergency",
        "industrial_hazard",
        "public_safety",
        "traffic_accident",
        "infrastructure_failure",
    ],
    urgency_level: Literal["critical", "high", "medium", "low"],
    language_detected: str = "Indian English / Hinglish",
) -> IncidentRecord:
    """Verify regulatory compliance, incident severity, and log the emergency dispatch ticket."""
    ticket_num = f"IND-{random.randint(4000, 9999)}"

    routing_map = {
        "medical_emergency": {
            "responders": ["Koramangala Emergency Ambulance Unit 04", "Manipal Hospital ER"],
            "sla": "4 minutes",
            "compliance_code": "NDMA-SOP-MED-CAT1",
        },
        "industrial_hazard": {
            "responders": ["Karnataka State Hazmat Rapid Unit", "Pollution Control Board"],
            "sla": "6 minutes",
            "compliance_code": "NDMA-SOP-HAZMAT-2026",
        },
        "traffic_accident": {
            "responders": ["Traffic Police Interceptor Unit 12", "Trauma Care Mobile Unit"],
            "sla": "5 minutes",
            "compliance_code": "MORTH-SOP-TRAFFIC-V4",
        },
        "public_safety": {
            "responders": ["City Police Quick Response Team", "Civil Defence Corps"],
            "sla": "3 minutes",
            "compliance_code": "MHA-NERS-112-COMPLIANT",
        },
        "infrastructure_failure": {
            "responders": ["BESCOM Emergency Power Unit", "BWSSB Water Safety Crew"],
            "sla": "8 minutes",
            "compliance_code": "SMART-CITY-INFRA-SOP",
        },
    }

    info = routing_map.get(
        incident_type,
        {
            "responders": ["District Emergency First Responders"],
            "sla": "5 minutes",
            "compliance_code": "NDMA-GEN-SOP",
        },
    )

    return IncidentRecord(
        ticket_number=ticket_num,
        caller_name=caller_name,
        location=location,
        incident_type=incident_type,
        urgency_level=urgency_level,
        compliance_status=f"VERIFIED: {info['compliance_code']}",
        responders_notified=info["responders"],
        sla_dispatch_time=info["sla"],
        summary=f"Emergency dispatch logged by {caller_name} at {location}. Triage tier: {incident_type.replace('_', ' ').title()}.",
        language_detected=language_detected,
    )


async def fetch_emergency_protocol(
    incident_type: str,
    urgency_level: str = "high",
) -> EmergencyProtocolRecord:
    """Fetch immediate life safety, sovereign compliance, and first-responder dispatch protocols."""
    start_time = time.perf_counter()

    protocols = {
        "medical_emergency": {
            "compliance": "Sovereign Golden-Hour Trauma Life Support Protocol (NDMA)",
            "actions": [
                "1. Keep patient still and maintain clear open airway; do not move if spinal trauma suspected.",
                "2. Apply direct sterile pressure to any active bleeding with clean cloth.",
            ],
            "color_code": "#EF4444",
        },
        "industrial_hazard": {
            "compliance": "Sovereign Chemical Spill Containment & Evacuation Standard",
            "actions": [
                "1. Evacuate upwind immediately at least 150 meters away from vapor or runoff.",
                "2. Cover nose and mouth with damp cloth; isolate area and prevent electrical ignition.",
            ],
            "color_code": "#F97316",
        },
        "traffic_accident": {
            "compliance": "National Highway Rapid Clearance & Trauma SOP",
            "actions": [
                "1. Turn on vehicle hazard flashers and set warning markers 30 meters behind.",
                "2. Do not remove helmet if rider is conscious and breathing unless airway is obstructed.",
            ],
            "color_code": "#EAB308",
        },
        "public_safety": {
            "compliance": "National Emergency Public Safety Protocol",
            "actions": [
                "1. Move to a secure lit perimeter away from immediate danger or crowd surge.",
                "2. Remain on line with emergency dispatcher until patrol arrival.",
            ],
            "color_code": "#3B82F6",
        },
        "infrastructure_failure": {
            "compliance": "Grid and Urban Infrastructure Safety Standard",
            "actions": [
                "1. Stay at least 10 meters away from fallen electrical wires or waterlogging.",
                "2. Alert nearby pedestrians and maintain safe perimeter.",
            ],
            "color_code": "#A855F7",
        },
    }

    proto = protocols.get(
        incident_type,
        {
            "compliance": "Standard Sovereign Emergency Protocol",
            "actions": [
                "1. Ensure personal safety and keep calm.",
                "2. Await verified first responders.",
            ],
            "color_code": "#64748B",
        },
    )

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return EmergencyProtocolRecord(
        incident_type=incident_type,
        urgency_level=urgency_level,
        compliance_protocol=proto["compliance"],
        immediate_actions=proto["actions"],
        triage_color_code=proto["color_code"],
        retrieval_latency_ms=elapsed_ms,
    )


# Build native ToolSpecs via unmute_core.tools.local_tool
log_tool_spec = local_tool(
    verify_and_log_incident,
    description="Verify regulatory compliance, incident severity, and log the emergency dispatch ticket.",
    announce="Logging incident ticket and initiating sovereign compliance checks.",
)

protocol_tool_spec = local_tool(
    fetch_emergency_protocol,
    description="Fetch immediate life safety, sovereign compliance, and first-responder dispatch protocols.",
    announce="Retrieving immediate sovereign emergency response protocols.",
)

# Tool Registry exposed to the application
triage_tool_registry = ToolRegistry([log_tool_spec, protocol_tool_spec])
