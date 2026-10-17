"""The agents and the task steps they delegate to, with their tools."""

from __future__ import annotations

import os
from collections.abc import AsyncIterable
from typing import Annotated, Literal

import httpx
from livekit import rtc
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    ChatContext,
    FlushSentinel,
    ModelSettings,
    NotGivenOr,
    RunContext,
    function_tool,
    llm,
)
from livekit.agents.beta.tools import EndCallTool
from livekit.agents.llm import ChatChunk, Tool
from pydantic import Field

from prompts import COMPLIANCE_SPECIALIST_PROMPT, INTAKE_TRIAGE_PROMPT
from utils import dev_metrics
from utils.dev_metrics import dev_llm_node, dev_say

# --- agents ----------------------------------------------------------------


class ComplianceSpecialist(Agent):
    """The compliance_specialist agent, compiled from its entry in agent.yaml."""

    def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Synthesize speech through the dev feed's wrapper.

        Args:
            text: The text to speak.
            model_settings: The framework's per-turn model settings.

        Returns:
            The synthesized audio frames.
        """
        return dev_metrics.dev_tts_node(self, text, model_settings)

    def llm_node(
        self, chat_ctx: ChatContext, tools: list[Tool], model_settings: ModelSettings
    ) -> AsyncIterable[ChatChunk | str | FlushSentinel]:
        """Ask the model, through the dev feed's wrapper.

        Args:
            chat_ctx: The conversation to send.
            tools: The tools the model may call.
            model_settings: The framework's per-turn model settings.

        Returns:
            The model's chunks.
        """
        return dev_llm_node(
            self, Agent.default.llm_node, chat_ctx, tools, model_settings
        )

    def __init__(self, chat_ctx: NotGivenOr[llm.ChatContext] = NOT_GIVEN) -> None:
        """Build the agent.

        Args:
            chat_ctx: The conversation a handoff carries in.
        """
        super().__init__(
            instructions=COMPLIANCE_SPECIALIST_PROMPT,
            chat_ctx=chat_ctx,
            tools=[
                *EndCallTool(
                    extra_description="End the call when the caller is finished or says goodbye."
                ).tools
            ],
        )
        if isinstance(chat_ctx, llm.ChatContext):
            self._chat_ctx = chat_ctx.copy()

    async def on_enter(self) -> None:
        """Open this agent's turn as it takes over the call."""
        # This agent took over via handoff; let its own instructions drive the
        # opening (the prompt already says not to re-greet).
        self.session.generate_reply()

    @function_tool
    async def verify_and_log_incident(
        self,
        ctx: RunContext,
        caller_name: Annotated[str, Field(description="Name of the reporting caller")],
        incident_type: Annotated[
            Literal[
                "medical_emergency",
                "industrial_hazard",
                "public_safety",
                "traffic_accident",
                "infrastructure_failure",
            ],
            Field(description="Category of the incident"),
        ],
        language_detected: Annotated[
            str,
            Field(
                description="Spoken dialect or language (e.g., English, Hindi, Hinglish, Kannada)"
            ),
        ],
        location: Annotated[
            str,
            Field(
                description="City, district, or landmark in India (e.g., Koramangala Bengaluru, Mumbai, Delhi)"
            ),
        ],
        urgency_level: Annotated[
            Literal["critical", "high", "medium", "low"],
            Field(description="Assessed urgency and triage tier"),
        ],
    ) -> dict:
        """Verify regulatory compliance, incident severity, and log the emergency dispatch ticket. Call this immediately once incident details and location are confirmed."""
        # Cover the wait: say() returns a SpeechHandle, so speech starts and the
        # request goes out behind it. Deliberately not awaited: awaiting the
        # handle holds the tool until playout finishes, which is the delay this
        # line exists to hide. Announced after any refusal, so a refused call
        # stays silent.
        dev_say(
            self.session,
            "Logging incident ticket and initiating sovereign compliance checks.",
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                os.environ["FASTAPI_BACKEND_URL"].rstrip("/")
                + "/api/tools/log-incident",
                json={
                    "caller_name": caller_name,
                    "incident_type": incident_type,
                    "language_detected": language_detected,
                    "location": location,
                    "urgency_level": urgency_level,
                },
            )
            resp.raise_for_status()
            return resp.json()

    @function_tool
    async def fetch_emergency_protocol(
        self,
        ctx: RunContext,
        incident_type: Annotated[
            Literal[
                "medical_emergency",
                "industrial_hazard",
                "public_safety",
                "traffic_accident",
                "infrastructure_failure",
            ],
            Field(description="Category of incident"),
        ],
        urgency_level: Annotated[
            Literal["critical", "high", "medium", "low"],
            Field(description="Priority level of incident"),
        ],
    ) -> dict:
        """Fetch immediate life safety, sovereign compliance, and first-responder dispatch protocols. Returns actionable first-aid and safety instructions to read back to the caller in under 50ms."""
        # Cover the wait: say() returns a SpeechHandle, so speech starts and the
        # request goes out behind it. Deliberately not awaited: awaiting the
        # handle holds the tool until playout finishes, which is the delay this
        # line exists to hide. Announced after any refusal, so a refused call
        # stays silent.
        dev_say(
            self.session, "Retrieving immediate sovereign emergency response protocols."
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                os.environ["FASTAPI_BACKEND_URL"].rstrip("/")
                + "/api/tools/fetch-protocol",
                json={"incident_type": incident_type, "urgency_level": urgency_level},
            )
            resp.raise_for_status()
            return resp.json()


class IntakeTriage(Agent):
    """The intake_triage agent, compiled from its entry in agent.yaml."""

    def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Synthesize speech through the dev feed's wrapper.

        Args:
            text: The text to speak.
            model_settings: The framework's per-turn model settings.

        Returns:
            The synthesized audio frames.
        """
        return dev_metrics.dev_tts_node(self, text, model_settings)

    def llm_node(
        self, chat_ctx: ChatContext, tools: list[Tool], model_settings: ModelSettings
    ) -> AsyncIterable[ChatChunk | str | FlushSentinel]:
        """Ask the model, through the dev feed's wrapper.

        Args:
            chat_ctx: The conversation to send.
            tools: The tools the model may call.
            model_settings: The framework's per-turn model settings.

        Returns:
            The model's chunks.
        """
        return dev_llm_node(
            self, Agent.default.llm_node, chat_ctx, tools, model_settings
        )

    def __init__(
        self, chat_ctx: NotGivenOr[llm.ChatContext] = NOT_GIVEN, initial: bool = False
    ) -> None:
        """Build the agent.

        Args:
            chat_ctx: The conversation a handoff carries in.
            initial: True for the call's first agent, which greets the caller.
        """
        self._initial = initial
        super().__init__(
            instructions=INTAKE_TRIAGE_PROMPT,
            chat_ctx=chat_ctx,
        )
        if isinstance(chat_ctx, llm.ChatContext):
            self._chat_ctx = chat_ctx.copy()

    async def on_enter(self) -> None:
        """Open this agent's turn as it takes over the call."""
        if not self._initial:
            # This opening turn withholds the agent's own handoffs (B3: an agent that can
            # hand the call back before it has said anything ping-pongs). The framework's
            # on-enter tool flag would hide them for the rest of the call instead, because
            # its filter follows the context of everything this reply starts: a live call
            # offered one specialist nothing but its delegate for ten turns while the
            # caller asked for another one (B: salon handoffs, 2026-08-20).
            self.session.generate_reply(
                tools=[t.id for t in self.tools if t.id != "to_compliance_specialist"]
            )
            return
        await dev_say(
            self.session,
            "Namaste. Sovereign Emergency and Compliance Dispatch. Please state your name, location, and what happened.",
        )

    @function_tool
    async def to_compliance_specialist(self, ctx: RunContext) -> Agent:
        """The caller has provided their name, location/city, and incident summary, and is ready for compliance assessment and emergency dispatch."""
        await dev_say(
            ctx.session,
            "Connecting you now with our Sovereign Compliance Specialist for verification and dispatch.",
            allow_interruptions=False,
        )
        return ComplianceSpecialist(
            chat_ctx=self.chat_ctx.copy(
                exclude_instructions=True,
                exclude_config_update=True,
                exclude_handoff=True,
            )
        )
