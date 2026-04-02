"""
W-PRESENCE-002 — Reverse Geocoding Module
==========================================
WINDI Publishing House · Kempten, Bavaria
Created: 02 Apr 2026

"Coordenadas provam. Nomes contam."

Transforma coordenadas GPS em nomes de lugares legíveis.
Usa Nominatim (OpenStreetMap) como fonte primária — 100% soberano.

Filosofia:
    - GPS continua fonte primária (prova)
    - Nome é enriquecimento, não substituição
    - Ledger guarda ambos (lat/lng + label)
    - Rate limit respeitado (1 req/sec)

Invariantes:
    I14 — Presence Integrity (coordenadas = prova)
    I12 — Language Sovereign (resposta na língua pedida)
"""

import httpx
import logging
from typing import Optional, Dict, Any
from functools import lru_cache
import time

log = logging.getLogger("w-presence-geocode")

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

# Nominatim (OpenStreetMap) — FREE, Sovereign
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_TIMEOUT = 5.0  # segundos

# User-Agent obrigatório para Nominatim
USER_AGENT = "WINDI-Travel/1.0 (sovereign presence system; contact@windi-domain.com)"

# Rate limiting
_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 1.1  # segundos (Nominatim pede ~1 req/sec)


# ==============================================================================
# CACHE (evita rate limit)
# ==============================================================================

@lru_cache(maxsize=256)
def _cached_geocode(lat_rounded: float, lng_rounded: float, lang: str) -> Dict[str, Any]:
    """
    Cache interno com coordenadas arredondadas.

    Arredondamos a 4 casas decimais (~11m precisão) para maximizar cache hits.
    """
    return _do_reverse_geocode(lat_rounded, lng_rounded, lang)


# ==============================================================================
# CORE FUNCTION
# ==============================================================================

def _do_reverse_geocode(lat: float, lng: float, lang: str) -> Dict[str, Any]:
    """
    Executa reverse geocoding real via Nominatim.

    Args:
        lat: Latitude
        lng: Longitude
        lang: Código de língua (de, en, pt)

    Returns:
        Dict com label, city, state, country, source
    """
    global _last_request_time

    # Rate limiting
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)

    try:
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "accept-language": lang.lower(),
            "zoom": 14,  # Nível de detalhe (10=cidade, 14=rua, 18=edifício)
        }

        headers = {
            "User-Agent": USER_AGENT,
        }

        with httpx.Client(timeout=NOMINATIM_TIMEOUT) as client:
            _last_request_time = time.time()
            response = client.get(NOMINATIM_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        address = data.get("address", {})

        # Extrair campos relevantes
        city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("municipality")
        )
        state = address.get("state") or address.get("region")
        country = address.get("country")

        # Construir label compacto (não usar display_name completo)
        label_parts = [p for p in [city, state, country] if p]
        label = " · ".join(label_parts) if label_parts else data.get("display_name", "")

        log.info(f"[W-PRESENCE-002] Geocoded {lat:.4f},{lng:.4f} → {label}")

        return {
            "label": label,
            "city": city,
            "state": state,
            "country": country,
            "country_code": address.get("country_code", "").upper(),
            "source": "nominatim",
            "success": True,
        }

    except httpx.TimeoutException:
        log.warning(f"[W-PRESENCE-002] Timeout for {lat},{lng}")
        return {"label": None, "source": "timeout", "success": False}

    except httpx.HTTPStatusError as e:
        log.warning(f"[W-PRESENCE-002] HTTP {e.response.status_code} for {lat},{lng}")
        return {"label": None, "source": "http_error", "success": False}

    except Exception as e:
        log.error(f"[W-PRESENCE-002] Error: {e}")
        return {"label": None, "source": "error", "success": False}


# ==============================================================================
# PUBLIC API
# ==============================================================================

def reverse_geocode(
    lat: float,
    lng: float,
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Converte coordenadas GPS em nome de lugar.

    Usa cache interno para evitar rate limit do Nominatim.
    Coordenadas são arredondadas a 4 casas decimais (~11m) para cache.

    Args:
        lat: Latitude (ex: 47.7267)
        lng: Longitude (ex: 10.3139)
        lang: Código de língua ISO (de, en, pt)

    Returns:
        Dict com:
            label: str — Nome completo (ex: "Kempten · Bavaria · Germany")
            city: str — Cidade
            state: str — Estado/Região
            country: str — País
            country_code: str — Código ISO (DE, PT, etc)
            source: str — "nominatim" | "cache" | "error"
            success: bool — Se obteve resultado

    Exemplo:
        >>> reverse_geocode(47.7267, 10.3139, "de")
        {
            "label": "Kempten · Bayern · Deutschland",
            "city": "Kempten",
            "state": "Bayern",
            "country": "Deutschland",
            "country_code": "DE",
            "source": "nominatim",
            "success": True
        }

    Nota:
        Nominatim tem rate limit de ~1 req/seg.
        Este módulo implementa cache + throttling automático.
    """
    if lat is None or lng is None:
        return {"label": None, "source": "no_coords", "success": False}

    # Arredondar para cache (4 casas = ~11m precisão)
    lat_r = round(lat, 4)
    lng_r = round(lng, 4)
    lang_l = lang.lower()[:2] if lang else "de"

    return _cached_geocode(lat_r, lng_r, lang_l)


def reverse_geocode_async(
    lat: float,
    lng: float,
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Versão síncrona (mesmo que reverse_geocode).

    Nota: Para integração assíncrona real, usar httpx.AsyncClient.
    Esta função existe para compatibilidade de API.
    """
    return reverse_geocode(lat, lng, lang)


def clear_cache():
    """Limpa cache interno (útil para testes)."""
    _cached_geocode.cache_clear()
    log.info("[W-PRESENCE-002] Cache cleared")


# ==============================================================================
# FORMATAÇÃO PARA UI
# ==============================================================================

def format_location_label(
    lat: float,
    lng: float,
    lang: str = "de",
    include_coords: bool = False
) -> str:
    """
    Formata localização para exibição na UI.

    Args:
        lat: Latitude
        lng: Longitude
        lang: Código de língua
        include_coords: Se True, adiciona coordenadas ao fim

    Returns:
        String formatada para UI

    Exemplo:
        >>> format_location_label(47.7267, 10.3139, "de")
        "Kempten · Bayern · Deutschland"

        >>> format_location_label(47.7267, 10.3139, "de", include_coords=True)
        "Kempten · Bayern · Deutschland (47.7267, 10.3139)"
    """
    result = reverse_geocode(lat, lng, lang)

    if result.get("success") and result.get("label"):
        label = result["label"]
        if include_coords:
            label += f" ({lat:.4f}, {lng:.4f})"
        return label
    else:
        # Fallback: só coordenadas
        return f"{lat:.4f}, {lng:.4f}"


# ==============================================================================
# MODULE INFO
# ==============================================================================

__version__ = "1.0.0"
__module__ = "W-PRESENCE-002"
__author__ = "WINDI Publishing House"
__dependencies__ = ["httpx"]


# ==============================================================================
# CLI TEST
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("W-PRESENCE-002 — Reverse Geocoding Test")
    print("=" * 60)

    # Kempten, Bavaria
    test_coords = [
        (47.7267, 10.3139, "de"),
        (47.7267, 10.3139, "en"),
        (47.7267, 10.3139, "pt"),
        # Lisboa
        (38.7223, -9.1393, "pt"),
        # Berlin
        (52.5200, 13.4050, "de"),
    ]

    for lat, lng, lang in test_coords:
        result = reverse_geocode(lat, lng, lang)
        print(f"\n📍 {lat}, {lng} [{lang}]")
        print(f"   → {result.get('label', 'N/A')}")
        print(f"   → source: {result.get('source')}")

    print("\n" + "=" * 60)
    print("✅ Test complete")
