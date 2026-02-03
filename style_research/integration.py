#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Generator Integration
====================================================
Ponte entre Style Research e os geradores WINDI.
28 Janeiro 2026 - Three Dragons Protocol

"AI processes. Human decides. WINDI guarantees."
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from pipeline import (
    detect_style_request,
    research_style,
    get_style_for_generator,
    list_available_styles,
)
from profiler import load_profile, StyleProfile

VERSION = "1.0.0"


class StyleEngine:
    """
    Interface principal para uso nos geradores WINDI.
    
    Uso:
        engine = StyleEngine()
        style = engine.get_style("eu_official")
        # Usar style['sections'], style['tone'], etc. no gerador
    """
    
    def __init__(self, styles_dir: str = "/opt/windi/data/styles"):
        self.styles_dir = styles_dir
        self._cache: Dict[str, Dict] = {}
    
    def detect_from_message(self, user_message: str) -> Optional[str]:
        """
        Detecta estilo a partir da mensagem do usuário.
        
        Args:
            user_message: Texto do usuário
            
        Returns:
            style_key ou None
        """
        return detect_style_request(user_message)
    
    def get_style(self, style_key: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Obtém perfil de estilo para uso no gerador.
        
        Args:
            style_key: Chave do estilo (ex: "eu_official")
            force_refresh: Forçar nova pesquisa
            
        Returns:
            Dict com configurações de estilo ou None
        """
        # Cache em memória
        if not force_refresh and style_key in self._cache:
            return self._cache[style_key]
        
        style = get_style_for_generator(style_key)
        
        if style:
            self._cache[style_key] = style
        
        return style
    
    def list_styles(self) -> List[Dict[str, str]]:
        """Lista todos os estilos disponíveis."""
        return list_available_styles()
    
    def apply_style_to_document(
        self,
        document_data: Dict[str, Any],
        style_key: str
    ) -> Dict[str, Any]:
        """
        Aplica estilo a dados de documento.
        
        Modifica estrutura e formatação baseado no perfil de estilo,
        MAS NÃO ALTERA campos Nur Mensch ou conteúdo de governança.
        
        Args:
            document_data: Dados do documento
            style_key: Estilo a aplicar
            
        Returns:
            document_data modificado
        """
        style = self.get_style(style_key)
        
        if not style:
            print(f"[WINDI Style] ⚠️ Estilo não encontrado: {style_key}")
            return document_data
        
        # Aplicar metadados de estilo
        document_data["_style"] = {
            "style_id": style["style_id"],
            "style_name": style["style_name"],
            "applied": True,
        }
        
        # Sugerir seções se documento não tiver
        if not document_data.get("sections") and style.get("sections"):
            document_data["_suggested_sections"] = style["sections"]
        
        # Aplicar hints de formatação
        document_data["_format_hints"] = {
            "heading_style": style.get("heading_style", "numbered"),
            "tone": style.get("tone", "formal"),
            "voice": style.get("voice", "passive"),
            "density": style.get("density", "medium"),
            "avg_paragraph_length": style.get("avg_paragraph_length", 200),
        }
        
        print(f"[WINDI Style] ✅ Estilo '{style['style_name']}' aplicado")
        
        return document_data


def get_style_hints_for_llm(style_key: str) -> str:
    """
    Gera instruções de estilo para o LLM Adapter.
    
    Usado pelo llm_document_generator para orientar a geração.
    """
    engine = StyleEngine()
    style = engine.get_style(style_key)
    
    if not style:
        return ""
    
    hints = []
    
    # Tom
    tone_map = {
        "highly_formal": "Use linguagem extremamente formal e técnica.",
        "formal": "Use linguagem formal e profissional.",
        "neutral": "Use linguagem clara e objetiva.",
        "informal": "Use linguagem acessível mas profissional.",
    }
    hints.append(tone_map.get(style["tone"], ""))
    
    # Voz
    voice_map = {
        "passive": "Prefira voz passiva (ex: 'foi analisado', 'werden geprüft').",
        "active": "Use voz ativa quando possível.",
        "mixed": "Balance entre voz ativa e passiva.",
    }
    hints.append(voice_map.get(style["voice"], ""))
    
    # Densidade
    if style["density"] == "dense":
        hints.append(f"Escreva parágrafos densos (~{style['avg_paragraph_length']} caracteres).")
    elif style["density"] == "light":
        hints.append("Use parágrafos curtos e diretos.")
    
    # Estrutura
    if style.get("heading_style") == "numbered":
        hints.append("Use headings numerados (1., 1.1, 2., etc.).")
    
    # Seções
    if style.get("sections"):
        sections_str = ", ".join(style["sections"])
        hints.append(f"Estruture com seções: {sections_str}.")
    
    return " ".join(filter(None, hints))


# =============================================================================
# FUNÇÃO DE CONVENIÊNCIA PARA CHAT INTEGRATION
# =============================================================================

def process_style_request(user_message: str) -> Dict[str, Any]:
    """
    Processa mensagem do usuário e retorna informações de estilo.
    
    Usado pelo chat_integration.py para detectar e aplicar estilos.
    
    Returns:
        {
            "detected": bool,
            "style_key": str or None,
            "style_name": str or None,
            "hints": str,
            "error": str or None
        }
    """
    engine = StyleEngine()
    
    result = {
        "detected": False,
        "style_key": None,
        "style_name": None,
        "hints": "",
        "error": None,
    }
    
    # Detectar estilo na mensagem
    style_key = engine.detect_from_message(user_message)
    
    if not style_key:
        return result
    
    result["detected"] = True
    result["style_key"] = style_key
    
    # Obter estilo
    style = engine.get_style(style_key)
    
    if style:
        result["style_name"] = style["style_name"]
        result["hints"] = get_style_hints_for_llm(style_key)
    else:
        result["error"] = f"Não foi possível carregar estilo: {style_key}"
    
    return result


if __name__ == "__main__":
    print("WINDI Style Engine Integration Test")
    print("=" * 50)
    
    engine = StyleEngine()
    
    # Teste 1: Listar estilos
    print("\n📚 ESTILOS DISPONÍVEIS:")
    for s in engine.list_styles():
        print(f"   • {s['key']}: {s['name']}")
    
    # Teste 2: Detectar e obter estilo
    print("\n🔍 TESTE DE DETECÇÃO E APLICAÇÃO:")
    test_message = "Crie um relatório técnico no formato da União Europeia"
    
    style_key = engine.detect_from_message(test_message)
    print(f"   Mensagem: '{test_message}'")
    print(f"   Estilo detectado: {style_key}")
    
    if style_key:
        style = engine.get_style(style_key)
        if style:
            print(f"   Nome: {style['style_name']}")
            print(f"   Tom: {style['tone']}")
            print(f"   Voz: {style['voice']}")
    
    # Teste 3: Hints para LLM
    print("\n📝 HINTS PARA LLM:")
    if style_key:
        hints = get_style_hints_for_llm(style_key)
        print(f"   {hints}")
    
    # Teste 4: Função de chat integration
    print("\n💬 TESTE CHAT INTEGRATION:")
    result = process_style_request("Documento estilo BMBF para pesquisa")
    print(f"   Detectado: {result['detected']}")
    print(f"   Estilo: {result['style_name']}")
    print(f"   Hints: {result['hints'][:100]}...")
    
    print("\n" + "=" * 50)
    print("✅ Integration funcionando!")
