"""One call: warming the worker, building the session, and wiring the call."""

from __future__ import annotations

import os

from livekit.agents import (
    AgentSession,
    APIConnectOptions,
    JobContext,
    JobProcess,
    TurnHandlingOptions,
    inference,
    metrics,
)
from livekit.agents.voice import MetricsCollectedEvent
from livekit.agents.voice.agent_session import SessionConnectOptions
from livekit.plugins import google, silero, slng

from agents import IntakeTriage
from settings import require_env
from utils.dev_metrics import install_dev_metrics


def prewarm(proc: JobProcess) -> None:
    """Load what every call needs once, before the worker accepts a job.

    Args:
        proc: The worker process being warmed.
    """
    # The SDK gives every job process the worker's proxy, and agent.py drops
    # that proxy when NO_PROXY covers LIVEKIT_URL. Speech plugins still need it:
    # livekit.agents.utils.http_session() reads proc.http_proxy, and
    # livekit-agents 1.8.1 has no public setter for it.
    proc._http_proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    # The FLOOR: how long silence has to last before the runtime treats the
    # caller as finished. From pace: balanced.
    #
    # Always explicit. Leaving it off inherited Silero's own 0.55s, which is
    # slower than the turn detector wants and was never anybody's choice. Hard
    # floor is 0.25s; the turn detector raises at session start below it.
    #
    # Lowering this alone does not shorten a turn. The ceiling is in the session's
    # turn_handling endpointing below, and that is where a 2.5s turn came from.
    proc.userdata["vad"] = silero.VAD.load(min_silence_duration=0.3)


async def run_call(ctx: JobContext) -> None:
    """Run one call: build the session, start the entry agent and wire the call.

    Args:
        ctx: The job LiveKit dispatched for this call.
    """
    require_env()
    session = AgentSession(
        # One retry, not the framework's three. A failed completion is retried
        # four times by default with 0.1 + 2.0 + 2.0 seconds of sleep between the
        # attempts, on top of four round trips to the provider: a live call on
        # 2026-09-16 (trace 917975e9) spent 18.5 seconds in two of those and the
        # caller asked whether anybody was still there.
        #
        # A caller cannot wait that out, and a retry loop tuned for a batch job
        # is the wrong default for a conversation. One retry still covers a
        # transient fault and costs 0.1s, because the first retry is nearly
        # immediate; anything worse is better surfaced than slept through.
        #
        # ponytail: fixed, not authorable. No package would want a different
        # number, and the one that does can say so when it turns up.
        conn_options=SessionConnectOptions(
            llm_conn_options=APIConnectOptions(max_retry=1),
        ),
        stt=slng.STT(
            api_key=os.environ["SLNG_API_KEY"],
            slng_base_url="in.api.slng.ai",
            model="deepgram/nova:3",
        ),
        llm=google.LLM(api_key=os.environ["GOOGLE_API_KEY"], model="gemini-2.5-flash"),
        tts=slng.TTS(
            api_key=os.environ["SLNG_API_KEY"],
            slng_base_url="in.api.slng.ai",
            voice="sonic-english",
            model="cartesia/sonic:3",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(version="v1-mini"),
            # The CEILING, and the shortest wait the runtime will consider.
            # pace: balanced. Without this the streaming defaults apply and
            # max_delay is 2.5s, which no package could reach.
            endpointing={"mode": "dynamic", "min_delay": 0.3, "max_delay": 1.6},
            interruption={"enabled": True},
            preemptive_generation={"enabled": True},
        ),
        vad=ctx.proc.userdata["vad"],
    )

    # Inert unless the dev loop set UNMUTE_DEV_METRICS. Reads session events, so
    # it never touches the tracer provider an opt-in trace export would own.
    install_dev_metrics(session, call_id=ctx.room.name)

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        metrics.log_metrics(ev.metrics)

    await session.start(agent=IntakeTriage(initial=True), room=ctx.room)
    await ctx.connect()
