"""
OVO Backend — AI Services (Groq)
─────────────────────────────────
Uses Groq's blazing-fast LLM inference to generate creative
metadata for musical fragments.

Model: llama-3.3-70b-versatile (via Groq)
"""

import json
import logging

from groq import Groq

from app.config import get_settings

logger = logging.getLogger("ovo")

# ──────────────────────────────────────────────
# Lazy Groq client singleton
# ──────────────────────────────────────────────

_groq_client: Groq | None = None


def _get_groq() -> Groq:
    """Returns a singleton Groq client."""
    global _groq_client
    if _groq_client is None:
        settings = get_settings()
        _groq_client = Groq(api_key=settings.groq_api_key)
        logger.info("✓ Groq client initialized")
    return _groq_client


# ──────────────────────────────────────────────
# Metadata Generation
# ──────────────────────────────────────────────

METADATA_SYSTEM_PROMPT = """\
You are a creative music AI assistant for OVO, a musical version control system.
Given audio metadata (BPM, key, duration), generate:
1. A creative, evocative 2-4 word title for the musical fragment
2. A single-word mood descriptor

Respond ONLY with valid JSON in this exact format:
{"title": "Your Creative Title", "mood": "Mood"}

Example moods: Melancholic, Driving, Ethereal, Cyberpunk, Anthemic, Hypnotic, 
Nostalgic, Aggressive, Dreamy, Triumphant, Brooding, Euphoric, Cinematic, 
Haunting, Groovy, Serene, Chaotic, Warm, Dark, Luminous

Be creative and evocative with titles. Think like a music producer naming a track.
"""


async def generate_metadata(
    bpm: int,
    key: str,
    duration: str,
    filename: str = "",
) -> dict:
    """
    Uses Groq (Llama 3.3 70B) to generate a creative title and mood
    from audio metadata.

    Returns:
        {"title": str, "mood": str}
    """
    user_prompt = (
        f"Audio fragment metadata:\n"
        f"- BPM: {bpm}\n"
        f"- Key: {key}\n"
        f"- Duration: {duration}\n"
        f"- Original filename: {filename or 'unknown'}\n\n"
        f"Generate a creative title and mood for this musical idea."
    )

    try:
        client = _get_groq()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": METADATA_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            max_tokens=100,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        title = result.get("title", filename.replace(".wav", "") if filename else "Untitled")
        mood = result.get("mood", "Unknown")

        logger.info(f"🤖 AI metadata: title=\"{title}\", mood=\"{mood}\"")
        return {"title": title, "mood": mood}

    except Exception as e:
        logger.warning(f"⚠ AI metadata generation failed: {e}")
        # Fallback: use filename as title
        fallback_title = filename.replace(".wav", "").replace("_", " ").title() if filename else "Untitled Fragment"
        return {"title": fallback_title, "mood": "Unknown"}
