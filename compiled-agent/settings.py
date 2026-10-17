"""Every fixed value this agent runs with, in one place.

Compiled from the package: names, limits, timeouts, the environment variables
each kind of session needs, and the logger every module writes to. Nothing here
reads a secret.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("sovereign-triage-agent")
logger.setLevel(logging.INFO)


# --- required environment ----------------------------------------------------
# Everything this agent needs to run: the model providers' keys, the connection
# to the orchestrator, every address and token a tool or MCP source names, and
# anything else the package declared. Derived from what the compiler knows it
# requires rather than from the author's `secrets:` block, so a package that
# declares nothing still refuses to start without them. A missing one fails the
# session before the agent answers, rather than at the first tool call.
#
# The phone route's own credentials are deliberately absent: one file serves
# every channel, and demanding carrier credentials would refuse a browser
# session on a phone package. They are listed in .env.example and the runbook.
REQUIRED_ENV = [
    "FASTAPI_BACKEND_URL",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "LIVEKIT_URL",
    "SLNG_API_KEY",
]


def require_env() -> None:
    """Refuse to start a session when a required variable is unset.

    Raises:
        RuntimeError: Naming every unset variable in REQUIRED_ENV.
    """
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


# How long a warm process may take to start, knowledge indexing included.
LOCAL_INIT_TIMEOUT_SECS = 60.0
