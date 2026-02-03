#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Domain Whitelist
===============================================
Governança: Apenas domínios institucionais permitidos.
28 Janeiro 2026 - Three Dragons Protocol

Invariante I1: Soberania - Humano controla quais fontes são permitidas
Guardrail G1: Whitelist rígida - sem exceções
"""

from urllib.parse import urlparse
from typing import Set, Tuple

VERSION = "1.0.0"

ALLOWED_STYLE_DOMAINS: Set[str] = {
    # ACADÊMICOS
    "mit.edu",
    "stanford.edu", 
    "harvard.edu",
    "ox.ac.uk",
    "cam.ac.uk",
    "tu-muenchen.de",
    "lmu.de",
    "uni-heidelberg.de",
    "ethz.ch",
    # UNIÃO EUROPEIA
    "europa.eu",
    "eur-lex.europa.eu",
    "ec.europa.eu",
    # ALEMANHA OFICIAL
    "bundesregierung.de",
    "bmi.bund.de",
    "bmwk.de",
    "bmbf.de",
    "gesetze-im-internet.de",
    # OUTROS GOVERNOS
    "gov.uk",
    "gov.br",
    "usa.gov",
    # ORGANIZAÇÕES
    "who.int",
    "un.org",
    "oecd.org",
    "iso.org",
    "ieee.org",
    "w3.org",
    "nist.gov",
}

BLOCKED_DOMAINS: Set[str] = {
    "medium.com",
    "wordpress.com",
    "blogspot.com",
    "reddit.com",
    "twitter.com",
    "wikipedia.org",
}


def is_allowed(url: str) -> Tuple[bool, str]:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        
        if not host:
            return False, "URL inválida"
        
        for blocked in BLOCKED_DOMAINS:
            if host == blocked or host.endswith("." + blocked):
                return False, f"Domínio bloqueado: {blocked}"
        
        for allowed in ALLOWED_STYLE_DOMAINS:
            if host == allowed or host.endswith("." + allowed):
                return True, f"Domínio permitido: {allowed}"
        
        return False, f"Não está na whitelist: {host}"
        
    except Exception as e:
        return False, f"Erro: {str(e)}"


def get_domain_category(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    
    if any(d in host for d in [".edu", "uni-", "tu-", "eth"]):
        return "ACADEMIC"
    elif any(d in host for d in ["europa.eu", "bund.de", "gov."]):
        return "GOVERNMENT"
    elif any(d in host for d in [".org", ".int"]):
        return "ORGANIZATION"
    return "OTHER"


if __name__ == "__main__":
    test_urls = [
        "https://mit.edu/research",
        "https://europa.eu/style-guide",
        "https://medium.com/blog",
        "https://bmbf.de/foerderung",
    ]
    
    print("WINDI Domain Validator Test")
    print("=" * 40)
    for url in test_urls:
        ok, reason = is_allowed(url)
        print(f"{'✅' if ok else '❌'} {url}")
        print(f"   {reason}")
