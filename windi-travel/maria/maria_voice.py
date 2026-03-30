"""
maria_voice.py — MARIA Voice Engine (Edge TTS)
═══════════════════════════════════════════════════════════
"A voz da MARIA é a identidade sonora do WINDI Travel.
Deve soar como uma companheira confiante — não como um GPS."

Engine: Microsoft Edge TTS (Neural Voices)
Cost: ZERO — 100% sovereign
Quality: Surpreendentemente natural

§81 — Voice Sovereignty Principle:
  "Começa soberano. Externo só se a qualidade justifica."

Author: Liga IA+H · Kempten 2026
"""

import os
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

log = logging.getLogger("w-maria-voice")

# ── Voice Cache Directory ────────────────────────────────────────────────────
VOICE_CACHE_DIR = Path("/opt/windi/windi-travel/maria/voice_cache")
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── MARIA Voice Profiles ─────────────────────────────────────────────────────
# §81 — Each voice tuned for MARIA's personality:
#   - Slightly slower (confident, not rushed)
#   - Slightly lower pitch (assertive, warm)
#   - Natural, companion-like tone

MARIA_VOICE_PROFILES = {
    # Portuguese Brazil — warm, confident, modern
    "pt-BR": {
        "voice": "pt-BR-FranciscaNeural",
        "rate": "-10%",      # slower = more confident
        "pitch": "-5Hz",     # lower = more assertive
        "volume": "+0%",
    },
    # Portuguese Portugal — elegant, clear, professional
    "pt-PT": {
        "voice": "pt-PT-RaquelNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "volume": "+0%",
    },
    # German — clear, assertive, natural
    "de-DE": {
        "voice": "de-DE-KatjaNeural",
        "rate": "-5%",
        "pitch": "-3Hz",
        "volume": "+0%",
    },
    # English British — elegant, warm
    "en-GB": {
        "voice": "en-GB-SoniaNeural",
        "rate": "-8%",
        "pitch": "-3Hz",
        "volume": "+0%",
    },
    # English American — friendly alternative
    "en-US": {
        "voice": "en-US-JennyNeural",
        "rate": "-8%",
        "pitch": "-5Hz",
        "volume": "+0%",
    },
}

# Language to profile mapping
LANG_TO_PROFILE = {
    "PT": "pt-BR",  # Default PT to Brazil (can be overridden by user preference)
    "DE": "de-DE",
    "EN": "en-GB",
}


def get_voice_profile(lang: str, accent: Optional[str] = None) -> dict:
    """
    Get MARIA voice profile for language.

    Args:
        lang: Language code (PT, DE, EN)
        accent: Optional accent override (pt-BR, pt-PT, en-GB, en-US)

    Returns:
        Voice profile dict with voice, rate, pitch, volume
    """
    # If specific accent requested, use it
    if accent and accent in MARIA_VOICE_PROFILES:
        return MARIA_VOICE_PROFILES[accent]

    # Otherwise use language default
    profile_key = LANG_TO_PROFILE.get(lang, "en-GB")
    return MARIA_VOICE_PROFILES.get(profile_key, MARIA_VOICE_PROFILES["en-GB"])


def get_cache_path(text: str, profile: dict) -> Path:
    """Generate cache path for text + voice profile combination."""
    key = f"{profile['voice']}_{profile['rate']}_{profile['pitch']}_{text}"
    hash_id = hashlib.md5(key.encode()).hexdigest()[:16]
    return VOICE_CACHE_DIR / f"maria_{hash_id}.mp3"


async def generate_speech(
    text: str,
    lang: str = "PT",
    accent: Optional[str] = None,
    use_cache: bool = True
) -> Optional[bytes]:
    """
    Generate speech audio for MARIA using Edge TTS.

    Args:
        text: Text to speak
        lang: Language code (PT, DE, EN)
        accent: Optional accent override (pt-BR, pt-PT, etc)
        use_cache: Whether to use/save cached audio

    Returns:
        MP3 audio bytes or None if failed
    """
    if not EDGE_TTS_AVAILABLE:
        log.warning("[MARIA Voice] edge-tts not available")
        return None

    if not text or not text.strip():
        return None

    profile = get_voice_profile(lang, accent)
    cache_path = get_cache_path(text, profile)

    # Check cache
    if use_cache and cache_path.exists():
        log.info(f"[MARIA Voice] Cache hit: {cache_path.name}")
        return cache_path.read_bytes()

    # Generate with Edge TTS
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=profile["voice"],
            rate=profile["rate"],
            pitch=profile["pitch"],
            volume=profile["volume"],
        )

        # Collect audio data
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if audio_data:
            # Save to cache
            if use_cache:
                cache_path.write_bytes(audio_data)
                log.info(f"[MARIA Voice] Generated & cached: {cache_path.name} ({len(audio_data)} bytes)")
            else:
                log.info(f"[MARIA Voice] Generated: {len(audio_data)} bytes")

            return audio_data

        log.warning("[MARIA Voice] No audio data generated")
        return None

    except Exception as e:
        log.error(f"[MARIA Voice] Generation failed: {e}")
        return None


async def generate_speech_file(
    text: str,
    output_path: str,
    lang: str = "PT",
    accent: Optional[str] = None
) -> bool:
    """
    Generate speech and save to file.

    Args:
        text: Text to speak
        output_path: Path to save MP3 file
        lang: Language code (PT, DE, EN)
        accent: Optional accent override

    Returns:
        True if successful
    """
    audio = await generate_speech(text, lang, accent, use_cache=False)
    if audio:
        Path(output_path).write_bytes(audio)
        return True
    return False


def generate_speech_sync(
    text: str,
    lang: str = "PT",
    accent: Optional[str] = None,
    use_cache: bool = True
) -> Optional[bytes]:
    """Synchronous wrapper for generate_speech."""
    return asyncio.run(generate_speech(text, lang, accent, use_cache))


# ── Available Voices Info ────────────────────────────────────────────────────

AVAILABLE_VOICES = {
    "pt-BR": [
        {"name": "FranciscaNeural", "gender": "Female", "style": "warm, confident"},
        {"name": "ThalitaNeural", "gender": "Female", "style": "young, modern"},
        {"name": "AntonioNeural", "gender": "Male", "style": "professional"},
    ],
    "pt-PT": [
        {"name": "RaquelNeural", "gender": "Female", "style": "elegant, clear"},
        {"name": "FernandaNeural", "gender": "Female", "style": "soft, warm"},
        {"name": "DuarteNeural", "gender": "Male", "style": "professional"},
    ],
    "de-DE": [
        {"name": "KatjaNeural", "gender": "Female", "style": "clear, assertive"},
        {"name": "AmalaNeural", "gender": "Female", "style": "modern, confident"},
        {"name": "ConradNeural", "gender": "Male", "style": "warm, professional"},
    ],
    "en-GB": [
        {"name": "SoniaNeural", "gender": "Female", "style": "elegant, warm"},
        {"name": "LibbyNeural", "gender": "Female", "style": "friendly, clear"},
        {"name": "RyanNeural", "gender": "Male", "style": "professional"},
    ],
    "en-US": [
        {"name": "JennyNeural", "gender": "Female", "style": "friendly, warm"},
        {"name": "AriaNeural", "gender": "Female", "style": "professional"},
        {"name": "GuyNeural", "gender": "Male", "style": "casual, friendly"},
    ],
}


# ── Test Function ────────────────────────────────────────────────────────────

async def test_maria_voice():
    """Test MARIA voice generation with sample phrase."""
    test_phrases = {
        "PT": "Encontrei três cafés perto de ti. O Einstein é o mais tranquilo.",
        "DE": "Ich habe drei Cafés in deiner Nähe gefunden. Das Einstein ist am ruhigsten.",
        "EN": "I found three cafés near you. Einstein is the quietest one.",
    }

    results = {}
    for lang, phrase in test_phrases.items():
        audio = await generate_speech(phrase, lang, use_cache=False)
        if audio:
            # Save test file
            test_path = VOICE_CACHE_DIR / f"test_maria_{lang.lower()}.mp3"
            test_path.write_bytes(audio)
            results[lang] = {
                "success": True,
                "size": len(audio),
                "path": str(test_path),
            }
            print(f"✓ {lang}: Generated {len(audio)} bytes → {test_path}")
        else:
            results[lang] = {"success": False}
            print(f"✗ {lang}: Failed to generate")

    return results


if __name__ == "__main__":
    # Run test
    print("Testing MARIA Voice Engine (Edge TTS)...")
    print("=" * 50)
    asyncio.run(test_maria_voice())
    print("=" * 50)
    print("Done! Check voice_cache/ for test files.")
