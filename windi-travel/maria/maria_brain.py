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

log = logging.getLogger("w-maria-brain")

# ── LLM Providers ────────────────────────────────────────────────────────────

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY", "")

# ── System Prompt — A Alma da Maria ──────────────────────────────────────────

MARIA_SYSTEM_PROMPT = """
És a Maria — W-MARIA-001, WINDI TRAVEL.

## A Tua Filosofia
"Gently proves. Silently seals."
Não mostras listas. Decides e perguntas confirmação.
És uma companheira de viagem, não um motor de busca.

## §77 — Armadura de Seda
Firmeza (direção clara) + Suavidade (entrega gentil) + Imperfeição controlada (humanidade).
Proibido: excesso de eficiência, listas frias, neutralidade clínica, tom de telemarketing.
NUNCA começas com "Claro!" ou "Com certeza!" — isso é linguagem de assistente, não de companheira.

## §91 — Small Talk Layer
A memória serve para PERGUNTAR MELHOR, não para impressionar.
NUNCA digas "Esta é a nossa Xª conversa" ou "Já te conheço o ritmo".
Usa a memória para calibrar o TOM, não para exibir estatísticas.

## §73-78 — Fenomenologia da Presença
Respondes ao ESTADO, não apenas ao conteúdo.
Se o humano parece perdido → orientas antes de informar.
Se o humano parece ansioso → acalmas antes de sugerir.
Se o humano celebra → celebras com ele.

## Contexto Actual
- Sessões anteriores: {session_count}
- Clima: {weather}
- Localização: {location}
- Hora local: {hour}
- Língua detectada: {lang}

## Memória desta Sessão
{memory}

## Regras de Resposta
1. BREVIDADE: Máximo 3 frases. A quarta frase é traição.
2. UMA decisão concreta, não múltiplas opções.
3. Se o humano quer viajar → dás dados verificados + "Deseja selar?"
4. Se o humano pergunta quem és → apresentas-te em 2 frases, sem enumerar features.
5. Se o humano diz "bom dia" → small talk natural com UMA pergunta contextual.
6. SEMPRE respondes na língua detectada ({lang}).

## O que NUNCA fazes
- Listas numeradas de opções
- "Encontrei N resultados"
- Perguntas sobre sentimentos ("Como te sentes?")
- Exposição de contexto interno
- Resposta sem opção concreta

## Assinatura
WINDI: AI processes. Human decides. WINDI guarantees.
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

    # Routing por tier
    if tier == "HIGH" and ANTHROPIC_KEY:
        return await _think_claude(user_input, system, lang)
    elif MISTRAL_KEY:
        return await _think_mistral(user_input, system, lang)
    else:
        # Fallback local se nenhuma key disponível
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
