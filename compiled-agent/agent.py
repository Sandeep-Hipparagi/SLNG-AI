"""LiveKit voice agent, compiled by Unmute from this package's agent.yaml."""

from __future__ import annotations

import os
from urllib.parse import urlparse
from urllib.request import proxy_bypass_environment

from dotenv import load_dotenv
from livekit.agents import AgentServer, JobContext

from call import prewarm, run_call
from settings import LOCAL_INIT_TIMEOUT_SECS

load_dotenv()

# livekit-agents 1.8.1 takes HTTPS_PROXY or HTTP_PROXY for the worker's own
# connection to LIVEKIT_URL and ignores NO_PROXY (worker.py:358). A proxy that
# only tunnels HTTPS answers that request with 405, and the worker never
# registers. So a LiveKit host listed in NO_PROXY is reached directly. Anything
# else gets the value the SDK would have picked itself.
WORKER_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
if proxy_bypass_environment(urlparse(os.getenv("LIVEKIT_URL", "")).hostname or ""):
    WORKER_PROXY = None

server = AgentServer(http_proxy=WORKER_PROXY)
server.setup_fnc = prewarm
if os.getenv("UNMUTE_LOCAL_RUN") == "1":
    # One browser call needs one warm spare, not one index build per CPU.
    server.update_options(
        num_idle_processes=1, initialize_process_timeout=LOCAL_INIT_TIMEOUT_SECS
    )


@server.rtc_session(agent_name="sovereign-triage-agent-livekit")
async def entrypoint(ctx: JobContext) -> None:
    """Run one call LiveKit dispatched to this worker.

    Args:
        ctx: The job LiveKit dispatched for this call.
    """
    await run_call(ctx)


# No __main__ block: this module is started through livekit-agents' supported
# CLI, `python -m livekit.agents start agent.py`, which imports it and finds the
# `server` above. The older per-script entry point goes through a CLI upstream
# has deprecated and will remove.
