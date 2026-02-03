#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Secure Fetcher
=============================================
Download seguro de páginas institucionais.
28 Janeiro 2026 - Three Dragons Protocol

Guardrail G7: Fail-Closed - qualquer erro = rejeitar
"""

import requests
from typing import Tuple, Optional
from domains import is_allowed, get_domain_category

VERSION = "1.0.0"

# Limites de segurança
MAX_TIMEOUT = 15
MAX_BYTES = 2_000_000  # 2MB máximo
USER_AGENT = "WINDI-StyleResearch/1.0 (Institutional Document Analysis)"

ALLOWED_CONTENT_TYPES = [
    "text/html",
    "application/xhtml+xml",
]


class FetchError(Exception):
    """Erro durante fetch - fail-closed."""
    pass


def fetch_html(url: str, timeout: int = MAX_TIMEOUT) -> Tuple[str, dict]:
    """
    Faz download seguro de página HTML.
    
    Args:
        url: URL para buscar (deve estar na whitelist)
        timeout: Timeout em segundos
        
    Returns:
        Tuple[str, dict]: (html_content, metadata)
        
    Raises:
        FetchError: Qualquer problema = falha segura
    """
    # 1. Validar domínio ANTES de qualquer request
    allowed, reason = is_allowed(url)
    if not allowed:
        raise FetchError(f"Domínio não permitido: {reason}")
    
    metadata = {
        "url": url,
        "domain_category": get_domain_category(url),
        "fetched": False,
    }
    
    try:
        # 2. Fazer request com proteções
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "de,en;q=0.9",
            },
            allow_redirects=True,
            stream=True  # Para verificar tamanho antes de baixar tudo
        )
        
        response.raise_for_status()
        
        # 3. Verificar Content-Type
        content_type = response.headers.get("Content-Type", "").lower()
        if not any(ct in content_type for ct in ALLOWED_CONTENT_TYPES):
            raise FetchError(f"Content-Type não suportado: {content_type}")
        
        # 4. Verificar tamanho
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_BYTES:
            raise FetchError(f"Arquivo muito grande: {content_length} bytes")
        
        # 5. Baixar com limite
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_BYTES:
                raise FetchError(f"Conteúdo excede limite de {MAX_BYTES} bytes")
        
        # 6. Decodificar
        encoding = response.encoding or "utf-8"
        html = content.decode(encoding, errors="replace")
        
        metadata.update({
            "fetched": True,
            "status_code": response.status_code,
            "content_type": content_type,
            "size_bytes": len(content),
            "encoding": encoding,
        })
        
        return html, metadata
        
    except requests.exceptions.Timeout:
        raise FetchError(f"Timeout após {timeout}s")
    except requests.exceptions.SSLError as e:
        raise FetchError(f"Erro SSL: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        raise FetchError(f"Erro de conexão: {str(e)}")
    except requests.exceptions.HTTPError as e:
        raise FetchError(f"Erro HTTP: {str(e)}")
    except Exception as e:
        raise FetchError(f"Erro inesperado: {str(e)}")


def safe_fetch(url: str) -> Optional[Tuple[str, dict]]:
    """
    Versão que retorna None em vez de exceção.
    Útil para batch processing.
    """
    try:
        return fetch_html(url)
    except FetchError as e:
        print(f"[WINDI Fetch] ❌ {url}: {e}")
        return None


if __name__ == "__main__":
    print("WINDI Secure Fetcher Test")
    print("=" * 50)
    
    # Teste com URL permitida (pode falhar por rede)
    test_url = "https://europa.eu/european-union/index_en"
    print(f"Testando: {test_url}")
    
    try:
        html, meta = fetch_html(test_url)
        print(f"✅ Sucesso!")
        print(f"   Categoria: {meta['domain_category']}")
        print(f"   Tamanho: {meta['size_bytes']} bytes")
        print(f"   Primeiros 200 chars: {html[:200]}...")
    except FetchError as e:
        print(f"❌ Erro (esperado se sem rede): {e}")
    
    # Teste com URL bloqueada
    print("\nTestando URL bloqueada...")
    blocked = "https://medium.com/article"
    result = safe_fetch(blocked)
    print(f"Resultado: {'None (correto!)' if result is None else 'ERRO - deveria bloquear!'}")
