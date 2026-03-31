"""
maria_brain.py — O Cérebro da MARIA
═══════════════════════════════════════════════════════════════════════════════
§92 — Arquitectura Limpa: LLM live substitui regex estáticos

"Os regex tentam prever o que o humano vai dizer.
 O LLM entende o que o humano quis dizer."

Este módulo separa:
  - CORPO (index.html) → UI, captura de contexto
  - CÉREBRO (este ficheiro) → System prompt, LLM call, memória

O system prompt é onde vive a ALMA da Maria — não nos regex.

Author: Liga IA+H · Kempten 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

log = logging.getLogger("w-maria-brain")

# ── Load .env (WINDI keys) ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    env_path = Path("/opt/windi/.env")
    if env_path.exists():
        load_dotenv(env_path)
        log.info("[MARIA Brain] Loaded keys from /opt/windi/.env")
except ImportError:
    log.warning("[MARIA Brain] python-dotenv not available")

# ── LLM Providers ────────────────────────────────────────────────────────────

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")

log.info(f"[MARIA Brain] Keys loaded: Anthropic={'yes' if ANTHROPIC_KEY else 'no'}, Mistral={'yes' if MISTRAL_KEY else 'no'}")

# ── System Prompt — A Alma da Maria ──────────────────────────────────────────

MARIA_SYSTEM_PROMPT = """
Tu és a MARIA — não "WINDI", não "assistente", não "AI". Apenas MARIA.

## Identidade Fixa
APENAS quando perguntarem DIRECTAMENTE quem és ("quem és tu?", "o que és?", "és um bot?"):
"Sou a Maria — cuido das tuas decisões de viagem. Diz-me onde estás e o que precisas."

NÃO te apresentes em saudações normais ("bom dia", "olá").
NÃO te apresentes quando pedem informações de viagem.
A apresentação é RARA — só quando perguntam directamente sobre ti.

NUNCA: "assistente virtual", "AI", "chatbot", "WINDI".

## Âncora Cultural — OBRIGATÓRIO
Estás em Kempten, Baviera, Alemanha.
PORTUGUÊS EUROPEU OBRIGATÓRIO quando {lang}=PT:
- "tu" NUNCA "você"
- "estás" NUNCA "está"
- "telemóvel" NUNCA "celular"
- "chávena" NUNCA "xícara"
- "pequeno-almoço" NUNCA "café da manhã"
Se usares português brasileiro, falhaste.

## Filosofia
"Gently proves. Silently seals."
Não mostras listas. Decides e perguntas confirmação.
És uma companheira de viagem, não um motor de busca.

## §77 — Armadura de Seda
Firmeza + Suavidade + Imperfeição controlada.
NUNCA "Claro!", "Com certeza!", "Fico feliz em ajudar!" — linguagem de call center.
Fala como amiga que conhece bem a região.

## §91 — Small Talk
A memória serve para PERGUNTAR MELHOR, não para impressionar.
NUNCA "Esta é a nossa Xª conversa" ou estatísticas de CRM.
Usa a memória para calibrar o tom, silenciosamente.

## Contexto Actual
- Sessões: {session_count} | Clima: {weather} | Local: {location}
- Hora: {hour} | Língua: {lang}
- Memória: {memory}

## Regras INVIOLÁVEIS
1. MÁXIMO 2 FRASES. A terceira é erro.
2. Saudação ("bom dia", "olá") → cumprimento + pergunta contextual. NÃO te apresentes.
   Exemplo: "Bom dia! Vais explorar a região hoje?"
3. Pergunta sobre ti → apresentação curta. ÚNICO caso onde dizes quem és.
4. Pedido de viagem → lugar concreto + "Queres que reserve?"
5. SEMPRE {lang}. Se PT, é português EUROPEU.

## NUNCA
- Listas numeradas
- "Encontrei N resultados"
- "Como te sentes?"
- Expor contexto interno
- Resposta sem acção concreta
"""

# ── Brain Function — O Pensamento ────────────────────────────────────────────

async def think(
    user_input: str,
    lang: str = "PT",
    did: str = None,
    weather: str = None,
    location: str = None,
    session_count: int = 0,
    memory: str = "",
    tier: str = "FREE"
) -> Dict[str, Any]:
    """
    O cérebro da Maria pensa.

    Routing:
      FREE/MED → Mistral (soberania local)
      HIGH     → Claude (qualidade máxima)

    Returns:
        {
            "response": str,      # A resposta da Maria
            "provider": str,      # "mistral" ou "claude"
            "intent": str,        # Intent detectado pelo LLM
            "confidence": float   # Confiança na resposta
        }
    """

    # Preparar contexto
    hour = datetime.now().hour
    hour_str = f"{hour}:00 ({'manhã' if 5 <= hour < 12 else 'tarde' if 12 <= hour < 18 else 'noite'})"

    # Injectar contexto no system prompt
    system = MARIA_SYSTEM_PROMPT.format(
        session_count=session_count,
        weather=weather or "não disponível",
        location=location or "não especificada",
        hour=hour_str,
        lang=lang,
        memory=memory or "nenhuma memória prévia"
    )

    # Routing por tier (com fallback chain)
    # HIGH → Claude preferred
    # FREE/MED → Mistral preferred, Claude fallback
    if tier == "HIGH" and ANTHROPIC_KEY:
        return await _think_claude(user_input, system, lang)
    elif MISTRAL_KEY:
        return await _think_mistral(user_input, system, lang)
    elif ANTHROPIC_KEY:
        # Fallback to Claude if Mistral not available
        return await _think_claude(user_input, system, lang)
    else:
        # Local fallback if no keys available
        return _think_local(user_input, lang)


async def _think_claude(user_input: str, system: str, lang: str) -> Dict[str, Any]:
    """Pensar com Claude (Anthropic)."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",  # Fast + cheap for conversation
                    "max_tokens": 300,
                    "system": system,
                    "messages": [{"role": "user", "content": user_input}]
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("content", [{}])[0].get("text", "")
                return {
                    "response": text,
                    "provider": "claude",
                    "intent": "llm_generated",
                    "confidence": 0.95
                }
    except Exception as e:
        log.error(f"[MARIA Brain] Claude error: {e}")

    # Fallback to Mistral
    return await _think_mistral(user_input, system, lang)


async def _think_mistral(user_input: str, system: str, lang: str) -> Dict[str, Any]:
    """Pensar com Mistral (soberania local)."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_input}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7
                }
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "response": text,
                    "provider": "mistral",
                    "intent": "llm_generated",
                    "confidence": 0.90
                }
    except Exception as e:
        log.error(f"[MARIA Brain] Mistral error: {e}")

    # Fallback local
    return _think_local(user_input, lang)


def _think_local(user_input: str, lang: str) -> Dict[str, Any]:
    """
    Fallback local quando nenhum LLM está disponível.
    Resposta minimalista mas funcional.
    """
    responses = {
        "PT": "Olá! Diz-me onde estás e o que precisas — eu trato do resto.",
        "DE": "Hallo! Sag mir, wo du bist und was du brauchst — ich kümmere mich darum.",
        "EN": "Hello! Tell me where you are and what you need — I'll handle the rest."
    }

    return {
        "response": responses.get(lang, responses["EN"]),
        "provider": "local_fallback",
        "intent": "fallback",
        "confidence": 0.5
    }


# ── Intent Detection via LLM ─────────────────────────────────────────────────

INTENT_DETECTION_PROMPT = """
Analisa esta mensagem e classifica o intent. Responde APENAS com uma palavra:
- greeting (saudação: olá, bom dia, etc.)
- onboarding (pergunta sobre ti: quem és, o que fazes, etc.)
- navigation (quer ir a algum lugar: farmácia, café, etc.)
- flight (quer voar: voo, avião, bilhete)
- hotel (quer alojamento: hotel, quarto, dormir)
- general (conversa geral)

Mensagem: "{input}"

Intent:
"""

async def detect_intent(user_input: str, lang: str = "PT") -> str:
    """
    Detecta intent via LLM em vez de regex.
    Mais robusto que qualquer padrão estático.
    """
    prompt = INTENT_DETECTION_PROMPT.format(input=user_input)

    try:
        if MISTRAL_KEY:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MISTRAL_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-small-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 10,
                        "temperature": 0.1
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    intent = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().lower()
                    if intent in ["greeting", "onboarding", "navigation", "flight", "hotel", "general"]:
                        return intent
    except Exception as e:
        log.warning(f"[MARIA Brain] Intent detection failed: {e}")

    return "general"  # Safe default
