#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research - Chat Bridge
==================================
Ponte entre Style Research e Chat Integration.
28 Janeiro 2026 - Three Dragons Protocol

Uso no chat_integration.py:
    from style_research.chat_style_bridge import enhance_with_style
    
    # No _generate_document:
    bescheid_data = enhance_with_style(bescheid_data, user_message)
"""

import sys
sys.path.insert(0, '/opt/windi/style_research')

from typing import Dict, Any, Optional

try:
    from integration import StyleEngine, get_style_hints_for_llm, process_style_request
    STYLE_ENGINE_AVAILABLE = True
    _engine = StyleEngine()
    print("[WINDI] ✅ Style Research Engine loaded")
except ImportError as e:
    STYLE_ENGINE_AVAILABLE = False
    _engine = None
    print(f"[WINDI] ⚠️ Style Research Engine not available: {e}")

VERSION = "1.0.0"


def detect_style(user_message: str) -> Optional[str]:
    """
    Detecta estilo na mensagem do usuário.
    
    Returns:
        style_key ou None
    """
    if not STYLE_ENGINE_AVAILABLE:
        return None
    
    return _engine.detect_from_message(user_message)


def get_style_config(style_key: str) -> Optional[Dict[str, Any]]:
    """
    Obtém configuração de estilo.
    """
    if not STYLE_ENGINE_AVAILABLE:
        return None
    
    return _engine.get_style(style_key)


def get_llm_hints(style_key: str) -> str:
    """
    Obtém hints de estilo para o LLM.
    """
    if not STYLE_ENGINE_AVAILABLE:
        return ""
    
    return get_style_hints_for_llm(style_key)


def enhance_with_style(
    document_data: Dict[str, Any],
    user_message: str,
    apply_hints: bool = True
) -> Dict[str, Any]:
    """
    Melhora dados do documento com estilo detectado.
    
    Esta é a função principal para usar no chat_integration.py
    
    Args:
        document_data: Dados do documento (bescheid_data, etc.)
        user_message: Mensagem original do usuário
        apply_hints: Se True, adiciona hints para formatação
    
    Returns:
        document_data enriquecido com informações de estilo
    """
    if not STYLE_ENGINE_AVAILABLE:
        return document_data
    
    # Detectar estilo
    style_key = detect_style(user_message)
    
    if not style_key:
        return document_data
    
    # Obter configuração
    style = get_style_config(style_key)
    
    if not style:
        return document_data
    
    print(f"[WINDI Style] 🎨 Aplicando estilo: {style['style_name']}")
    
    # Adicionar metadados de estilo
    document_data["_windi_style"] = {
        "style_id": style["style_id"],
        "style_name": style["style_name"],
        "tone": style["tone"],
        "voice": style["voice"],
        "density": style["density"],
    }
    
    # Adicionar hints para formatação
    if apply_hints:
        hints = get_llm_hints(style_key)
        if hints:
            document_data["_style_hints"] = hints
    
    # Sugerir estrutura de seções se disponível
    if style.get("sections"):
        document_data["_suggested_sections"] = style["sections"]
    
    # Ajustar formatação baseado no estilo
    format_hints = {
        "heading_style": style.get("heading_style", "numbered"),
        "avg_paragraph_length": style.get("avg_paragraph_length", 200),
        "uses_lists": style.get("uses_lists", True),
    }
    document_data["_format_hints"] = format_hints
    
    return document_data


def get_style_response_suffix(style_key: str) -> str:
    """
    Gera sufixo para resposta do chat indicando estilo aplicado.
    """
    if not STYLE_ENGINE_AVAILABLE:
        return ""
    
    style = get_style_config(style_key)
    
    if not style:
        return ""
    
    return f"\n\n🎨 Estilo aplicado: {style['style_name']}"


def list_available_styles() -> str:
    """
    Lista estilos disponíveis para mostrar ao usuário.
    """
    if not STYLE_ENGINE_AVAILABLE:
        return "Style Research Engine não disponível."
    
    styles = _engine.list_styles()
    
    lines = ["📚 **Estilos disponíveis:**"]
    for s in styles:
        cached = "💾" if s.get("cached") else "🌐"
        lines.append(f"   {cached} `{s['key']}` - {s['name']}")
    
    lines.append("\nUse na sua mensagem: 'formato MIT', 'estilo EU', 'padrão BMBF', etc.")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("WINDI Chat Style Bridge Test")
    print("=" * 50)
    
    # Teste
    test_message = "Erstelle einen Bescheid im EU-Format für Hans Mueller"
    
    print(f"\nMensagem: {test_message}")
    
    style_key = detect_style(test_message)
    print(f"Estilo detectado: {style_key}")
    
    if style_key:
        # Simular document_data
        doc_data = {
            "recipient_name": "Hans Mueller",
            "subject": "Baugenehmigung",
        }
        
        enhanced = enhance_with_style(doc_data, test_message)
        
        print(f"\nDocument data enriquecido:")
        print(f"   _windi_style: {enhanced.get('_windi_style', {}).get('style_name')}")
        print(f"   _style_hints: {enhanced.get('_style_hints', '')[:80]}...")
    
    print("\n" + "=" * 50)
    print(list_available_styles())
