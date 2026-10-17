"""Configuration and environment variable loader for Sovereign Indic Voice Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search and load .env from project root and backend directory
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Load in order: root .env, then backend/.env (if present)
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.example")  # Fallback to defaults

# Normalized Provider API Keys
SLNG_API_KEY: str = os.getenv("SLNG_API_KEY", "").strip()
SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "").strip()
GNANI_API_KEY: str = (os.getenv("GNANI_API_KEY") or os.getenv("GNANI-API-KEY", "")).strip()
GEMINI_API_KEY: str = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")).strip()

# Service configuration
FASTAPI_BACKEND_URL: str = os.getenv("FASTAPI_BACKEND_URL", "http://localhost:8000").strip()
PORT: int = int(os.getenv("PORT", "8000"))
SLNG_WORLD_PART: str = "in"
SLNG_SOVEREIGN_ROUTER: str = "https://in.api.slng.ai"


def get_providers_status() -> dict:
    """Returns safe readiness booleans and model labels for all integrated providers."""
    return {
        "status": "online",
        "sovereign_region": "ap-south / in.api.slng.ai (Bengaluru Hub)",
        "providers": {
            "slng": {
                "name": "SLNG Sovereign Execution Layer",
                "endpoint": "https://in.api.slng.ai",
                "ready": bool(SLNG_API_KEY),
                "features": ["In-Region Gateway", "Context Router Caching (53% savings)", "Pre-STT Noise Cleanup"],
            },
            "sarvam": {
                "name": "Sarvam AI Indic Voice Engine",
                "endpoint": "https://api.sarvam.ai",
                "ready": bool(SARVAM_API_KEY),
                "models": ["bulbul:v3", "bulbul:v4-flash", "saaras:v3"],
                "features": ["10+ Indic Languages", "Native Script Synthesis", "24kHz High Fidelity"],
            },
            "gnani": {
                "name": "Gnani.ai Sovereign Speech Engine",
                "endpoint": "https://in.api.slng.ai/v1/gnani",
                "ready": bool(GNANI_API_KEY),
                "models": ["Timbre v2.5", "Prisma v2.5 (8kHz Telephony)", "Indic NER"],
                "features": ["Aadhaar/PAN/Location NER", "Noisy Call-Center Telephony ASR", "Sub-100ms Turnaround"],
            },
            "gemini": {
                "name": "Google Gemini 2.5 Flash",
                "endpoint": "https://generativelanguage.googleapis.com",
                "ready": bool(GEMINI_API_KEY),
                "models": ["gemini-2.5-flash", "gemini-flash-latest"],
                "features": ["Low TTFT (<150ms)", "Structured Tool Calling", "Bilingual Hinglish/Kannada Triage"],
            },
        },
    }
