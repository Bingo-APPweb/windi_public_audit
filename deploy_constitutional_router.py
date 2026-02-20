#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
WINDI Constitutional Local Router — Deploy Script v1.0
═══════════════════════════════════════════════════════════════════════════════
Data: 12 Feb 2026
Autor: Guardian (Claude) + Human Dragon

O QUE FAZ:
  1. Backup do a4desk_tiptap_babel.py
  2. Insere constitutional_local_router() no arquivo
  3. Patcha a funcao chat() para chamar o router ANTES do Gateway
  4. Testa o patch

COMO RODAR:
  cd /opt/windi
  python3 deploy_constitutional_router.py

ROLLBACK:
  cp /opt/windi/backups/a4desk_tiptap_babel.py.pre_constitutional_router \
     /opt/windi/a4desk-editor/a4desk_tiptap_babel.py
  # Reiniciar o HUB

"AI processes. Human decides. WINDI guarantees."
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_FILE = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"
BACKUP_DIR = "/opt/windi/backups"
BACKUP_NAME = "a4desk_tiptap_babel.py.pre_constitutional_router"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# ═══════════════════════════════════════════════════════════════════════════════
# THE CONSTITUTIONAL LOCAL ROUTER (to be inserted in the file)
# ═══════════════════════════════════════════════════════════════════════════════

ROUTER_CODE = '''
# ═══════════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL LOCAL ROUTER v1.0 — 12 Feb 2026
# Resolve localmente o que NAO precisa de LLM/Gateway
# Soberania: 100% — Zero dependencia de BigTech KEYs
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════════════════

TUTORIAL_PATTERNS = {
    'de': ["wie kann ich", "wie nutze ich", "wie geht", "wie funktioniert",
           "wie verwende ich", "wie benutze ich", "zeig mir", "anleitung",
           "wie mache ich", "wo finde ich", "wie starte ich", "wie oeffne ich"],
    'en': ["how to", "how do i", "how can i", "how does", "show me how",
           "teach me", "guide me", "where do i find", "how do i use"],
    'pt': ["como usar", "como faco", "como posso", "como funciona",
           "como utilizar", "me ensine", "me mostre", "onde encontro",
           "como configurar", "como ativar"],
}

IDENTITY_PATTERNS = {
    'de': ["wer bist du", "was bist du", "was machst du", "was kannst du",
           "wer sind sie", "was sind sie", "stell dich vor"],
    'en': ["who are you", "what are you", "what do you do", "what can you do",
           "introduce yourself"],
    'pt': ["quem e voce", "o que voce e", "o que voce faz", "quem es tu",
           "se apresente", "o que e windi"],
}

_TEMPLATE_KW = ["template", "vorlage", "modelo", "templates", "vorlagen"]
_EDITOR_KW = ["editor", "babel", "toolbar", "formatierung", "formatting", "formatacao"]
_SGE_KW = ["sge", "analyse", "scan", "governance", "risk", "risco", "analise"]


def constitutional_local_router(message, lang='de'):
    """
    CONSTITUTIONAL LOCAL ROUTER
    Resolve perguntas localmente SEM chamar LLM.
    Retorna dict com resposta ou None (= passa para Gateway).
    """
    text = message.lower().strip()

    # --- TUTORIAL MODE ---
    is_tutorial = any(p in text for patterns in TUTORIAL_PATTERNS.values()
                      for p in patterns)
    if is_tutorial:
        topic = _detect_tutorial_topic(text)
        response = _build_tutorial_response(topic, lang)
        print(f"[WINDI Router] TUTORIAL mode: topic={topic}, lang={lang}", flush=True)
        return {
            "response": response,
            "dragon": "windi-local",
            "model": "constitutional-router-v1",
            "is_document": False,
            "routed_by": "constitutional-local",
            "skill": "tutorial-mode"
        }

    # --- IDENTITY MODE ---
    is_identity = any(p in text for patterns in IDENTITY_PATTERNS.values()
                      for p in patterns)
    if is_identity:
        response = _build_identity_response(lang)
        print(f"[WINDI Router] IDENTITY mode: lang={lang}", flush=True)
        return {
            "response": response,
            "dragon": "windi-local",
            "model": "constitutional-router-v1",
            "is_document": False,
            "routed_by": "constitutional-local",
            "skill": "product-identity"
        }

    # --- NENHUM MATCH LOCAL -> passa para Gateway/LLM ---
    return None


def _detect_tutorial_topic(text):
    if any(k in text for k in _TEMPLATE_KW):
        return "templates"
    if any(k in text for k in _EDITOR_KW):
        return "editor"
    if any(k in text for k in _SGE_KW):
        return "sge"
    return "general"


def _build_tutorial_response(topic, lang):
    tutorials = {
        "templates": {
            "de": """So nutzen Sie die Templates:

1. Klicken Sie in der Seitenleiste auf "Templates"
2. Waehlen Sie das gewuenschte Template (z.B. Bericht, Memo, Bescheid)
3. Das Template wird in den Editor eingefuegt
4. Felder in [eckigen Klammern] muessen Sie ausfuellen
5. Speichern Sie mit dem Speicher-Button

Verfuegbare Templates: Berichte, Memoranden, Bescheide, Genehmigungen, Ablehnungen.

Welches Template moechten Sie verwenden?

Human decides. I structure.""",
            "en": """How to use templates:

1. Click "Templates" in the sidebar
2. Select the template you need (e.g. Report, Memo, Decision)
3. The template is inserted into the editor
4. Fill in fields marked with [brackets]
5. Save using the save button

Available templates: Reports, Memos, Decisions, Approvals, Rejections.

Which template would you like to use?

Human decides. I structure.""",
            "pt": """Como usar os templates:

1. Clique em "Templates" na barra lateral
2. Selecione o template desejado (ex: Relatorio, Memo, Decisao)
3. O template sera inserido no editor
4. Preencha os campos marcados com [colchetes]
5. Salve usando o botao de salvar

Templates disponiveis: Relatorios, Memorandos, Decisoes, Aprovacoes, Rejeicoes.

Qual template voce gostaria de usar?

Human decides. I structure.""",
        },
        "editor": {
            "de": """Der BABEL Editor - Kurzanleitung:

1. Schreiben: Tippen Sie direkt im Editorbereich
2. Formatieren: Nutzen Sie die Toolbar (Fett, Kursiv, Listen)
3. Templates: Seitenleiste rechts
4. Chat: Ich bin hier links - fragen Sie mich alles
5. Speichern: Button oben oder Ctrl+S
6. Exportieren: PDF, DOCX ueber das Export-Menue

Human decides. I structure.""",
            "en": """BABEL Editor - Quick guide:

1. Write: Type directly in the editor area
2. Format: Use the toolbar (Bold, Italic, Lists)
3. Templates: Right sidebar
4. Chat: I'm here on the left - ask me anything
5. Save: Button above or Ctrl+S
6. Export: PDF, DOCX via the export menu

Human decides. I structure.""",
            "pt": """Editor BABEL - Guia rapido:

1. Escrever: Digite diretamente na area do editor
2. Formatar: Use a toolbar (Negrito, Italico, Listas)
3. Templates: Barra lateral direita
4. Chat: Estou aqui a esquerda - me pergunte qualquer coisa
5. Salvar: Botao acima ou Ctrl+S
6. Exportar: PDF, DOCX pelo menu de exportacao

Human decides. I structure.""",
        },
        "sge": {
            "de": """SGE (Semantic Governance Engine) - So funktioniert die Analyse:

1. Oeffnen oder erstellen Sie ein Dokument
2. Klicken Sie auf "SGE Scan" oder "Analysieren"
3. Die Engine prueft 6 semantische Schichten:
   - Lexikalisch (Wortwahl)
   - Syntaktisch (Satzstruktur)
   - Semantisch (Bedeutung)
   - Pragmatisch (Kontext)
   - Regulatorisch (Compliance)
   - Institutionell (Anforderungen)
4. Sie erhalten einen Risk Score (R0-R5)
5. SIE entscheiden, was zu tun ist

Human decides. I structure.""",
            "en": """SGE (Semantic Governance Engine) - How analysis works:

1. Open or create a document
2. Click "SGE Scan" or "Analyze"
3. The engine checks 6 semantic layers:
   - Lexical (word choice)
   - Syntactic (sentence structure)
   - Semantic (meaning)
   - Pragmatic (context)
   - Regulatory (compliance)
   - Institutional (requirements)
4. You receive a Risk Score (R0-R5)
5. YOU decide what to do

Human decides. I structure.""",
            "pt": """SGE (Semantic Governance Engine) - Como funciona:

1. Abra ou crie um documento
2. Clique em "SGE Scan" ou "Analisar"
3. O motor verifica 6 camadas semanticas:
   - Lexical (escolha de palavras)
   - Sintatica (estrutura de frases)
   - Semantica (significado)
   - Pragmatica (contexto)
   - Regulatoria (compliance)
   - Institucional (requisitos)
4. Voce recebe um Risk Score (R0-R5)
5. VOCE decide o que fazer

Human decides. I structure.""",
        },
        "general": {
            "de": """Ich kann Ihnen bei Folgendem helfen:

- Templates verwenden und anpassen
- Dokumente erstellen und formatieren
- SGE-Analysen verstehen
- Export in PDF oder DOCX
- Governance-Fragen beantworten

Was moechten Sie genauer wissen?

Human decides. I structure.""",
            "en": """I can help you with:

- Using and customizing templates
- Creating and formatting documents
- Understanding SGE analyses
- Exporting to PDF or DOCX
- Answering governance questions

What would you like to know more about?

Human decides. I structure.""",
            "pt": """Posso ajudar com:

- Usar e personalizar templates
- Criar e formatar documentos
- Entender analises SGE
- Exportar para PDF ou DOCX
- Responder perguntas de governanca

O que gostaria de saber mais?

Human decides. I structure.""",
        },
    }
    topic_responses = tutorials.get(topic, tutorials["general"])
    return topic_responses.get(lang, topic_responses["de"])


def _build_identity_response(lang):
    responses = {
        "de": """Ich bin WINDI - We Invite New Decision Intelligence.

Eine Pre-AI Governance Schicht, die Informationen strukturiert und Entscheidungsprozesse unterstuetzt - immer mit menschlicher Souveraenitaet.

Was ich tue:
- Informationen transparent strukturieren
- Optionen und Perspektiven praesentieren
- Dokumente und Analysen organisieren
- Templates bereitstellen

Was ich NICHT tue:
- Entscheidungen fuer Sie treffen
- Fakten erfinden
- Meine Autonomie eskalieren
- Aktionen ohne Ihre Genehmigung ausfuehren

AI processes. Human decides. WINDI guarantees.""",
        "en": """I am WINDI - We Invite New Decision Intelligence.

A Pre-AI Governance Layer that structures information and supports decision processes - always maintaining human sovereignty.

What I do:
- Structure information transparently
- Present options and perspectives
- Organize documents and analyses
- Provide templates

What I do NOT do:
- Make decisions for you
- Invent facts
- Escalate my own autonomy
- Execute actions without your approval

AI processes. Human decides. WINDI guarantees.""",
        "pt": """Sou WINDI - We Invite New Decision Intelligence.

Uma camada de governanca Pre-AI que estrutura informacoes e apoia processos decisorios - sempre mantendo a soberania humana.

O que faco:
- Estruturo informacoes de forma transparente
- Apresento opcoes e perspectivas
- Organizo documentos e analises
- Ofereco templates

O que NAO faco:
- Tomar decisoes por voce
- Inventar fatos
- Escalar minha autonomia
- Executar acoes sem aprovacao humana

AI processes. Human decides. WINDI guarantees.""",
    }
    return responses.get(lang, responses["de"])

# ═══════════════════════════════════════════════════════════════════════════════
# END CONSTITUTIONAL LOCAL ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
'''

# ═══════════════════════════════════════════════════════════════════════════════
# THE PATCH FOR chat() FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

# What to find in the chat() function (the line AFTER intent parser check)
CHAT_SEARCH = """    if INTENT_PARSER_AVAILABLE:
        intent_result = INTENT_HANDLER.handle_message(message, request.remote_addr)
        if intent_result['handled']:
            return jsonify(intent_result)
    try:"""

# What to replace it with
CHAT_REPLACE = """    if INTENT_PARSER_AVAILABLE:
        intent_result = INTENT_HANDLER.handle_message(message, request.remote_addr)
        if intent_result['handled']:
            return jsonify(intent_result)
    # ═══ CONSTITUTIONAL LOCAL ROUTER (12 Feb 2026) ═══
    # Resolve tutorials, identidade e perguntas simples LOCALMENTE
    # Sem chamar Gateway/LLM = 100% soberano, zero KEY
    local_response = constitutional_local_router(message, data.get('lang', 'de'))
    if local_response:
        print(f"[WINDI] Constitutional Router handled locally: skill={local_response.get('skill')}", flush=True)
        return jsonify(local_response)
    # ═══ END CONSTITUTIONAL ROUTER ═══
    try:"""


# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def print_header():
    print("=" * 70)
    print("  WINDI Constitutional Local Router — Deploy Script v1.0")
    print("  12 Feb 2026 — Guardian (Claude) + Human Dragon")
    print("=" * 70)
    print()


def check_preconditions():
    """Verify everything is in place before deploying."""
    print("[1/6] Checking preconditions...")

    if not os.path.exists(TARGET_FILE):
        print(f"  FATAL: {TARGET_FILE} not found!")
        return False

    # Read file and check for key markers
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already patched
    if 'constitutional_local_router' in content:
        print("  WARNING: Constitutional Router already present in file!")
        print("  To re-deploy, first rollback:")
        print(f"    cp {BACKUP_DIR}/{BACKUP_NAME} {TARGET_FILE}")
        return False

    # Check that the chat() function exists as expected
    if CHAT_SEARCH not in content:
        print("  WARNING: chat() function pattern not found as expected.")
        print("  The file may have been modified. Manual patching needed.")
        print()
        print("  Looking for similar patterns...")
        if 'INTENT_PARSER_AVAILABLE' in content and 'intent_result' in content:
            print("  Found INTENT_PARSER references — structure is close.")
            print("  Check lines around 2165 manually.")
        return False

    print("  OK: File found, not yet patched, pattern matches.")
    return True


def create_backup():
    """Create backup of the original file."""
    print("[2/6] Creating backup...")

    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Primary backup (named, for easy rollback)
    backup_path = os.path.join(BACKUP_DIR, BACKUP_NAME)
    shutil.copy2(TARGET_FILE, backup_path)
    print(f"  Backup: {backup_path}")

    # Timestamped backup (safety net)
    ts_backup = os.path.join(BACKUP_DIR, f"a4desk_tiptap_babel.py.{TIMESTAMP}")
    shutil.copy2(TARGET_FILE, ts_backup)
    print(f"  Timestamped: {ts_backup}")

    return True


def inject_router():
    """Inject the constitutional_local_router into the file."""
    print("[3/6] Injecting Constitutional Local Router...")

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find a good insertion point — before the chat() function
    # We insert the router code BEFORE @app.route('/api/chat')
    insertion_marker = "@app.route('/api/chat', methods=['POST'])\ndef chat():"

    if insertion_marker not in content:
        # Try alternate format
        insertion_marker = "@app.route('/api/chat', methods=['POST'])\ndef chat():"
        if insertion_marker not in content:
            print("  ERROR: Could not find chat() function for insertion point.")
            return False

    # Insert router code BEFORE the chat() route
    content = content.replace(
        insertion_marker,
        ROUTER_CODE + "\n" + insertion_marker
    )

    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  OK: Router code injected.")
    return True


def patch_chat_function():
    """Patch the chat() function to call the router."""
    print("[4/6] Patching chat() function...")

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    if CHAT_SEARCH not in content:
        print("  ERROR: chat() pattern not found after injection.")
        return False

    content = content.replace(CHAT_SEARCH, CHAT_REPLACE, 1)

    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print("  OK: chat() function patched.")
    return True


def verify_patch():
    """Verify the patch was applied correctly."""
    print("[5/6] Verifying patch...")

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {
        "constitutional_local_router function": "def constitutional_local_router(" in content,
        "TUTORIAL_PATTERNS": "TUTORIAL_PATTERNS = {" in content,
        "IDENTITY_PATTERNS": "IDENTITY_PATTERNS = {" in content,
        "Router call in chat()": "local_response = constitutional_local_router(" in content,
        "Router guard in chat()": "if local_response:" in content,
        "Original IntentParser intact": "INTENT_HANDLER.handle_message" in content,
        "Original Gateway call intact": "requests.post(f\"{CONFIG['gateway']}/api/chat\"" in content
            or "requests.post(f\"{CONFIG[\\'gateway\\']}/api/chat\"" in content,
    }

    all_ok = True
    for check_name, passed in checks.items():
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {check_name}")
        if not passed:
            all_ok = False

    return all_ok


def run_functional_test():
    """Run a quick functional test of the router logic."""
    print("[6/6] Running functional tests...")
    print()

    # We can't import from the file directly (it's a Flask app),
    # so we test the logic by executing the router code in isolation
    test_env = {}
    exec(ROUTER_CODE, test_env)
    router_fn = test_env['constitutional_local_router']

    tests = [
        ("Wie kann ich das Template nutzen?", "de", "tutorial-mode", "templates"),
        ("How to use the editor?", "en", "tutorial-mode", "editor"),
        ("Como usar o SGE?", "pt", "tutorial-mode", "sge"),
        ("Wie funktioniert das?", "de", "tutorial-mode", "general"),
        ("Wer bist du?", "de", "product-identity", None),
        ("Who are you?", "en", "product-identity", None),
        ("Quem e voce?", "pt", "product-identity", None),
        ("Erstelle einen Bericht", "de", None, None),  # Should pass through
        ("Guten Morgen!", "de", None, None),  # Should pass through
        ("Analysiere das Dokument", "de", None, None),  # Should pass through (goes to LLM)
    ]

    passed = 0
    failed = 0

    for message, lang, expected_skill, expected_topic in tests:
        result = router_fn(message, lang)

        if expected_skill is None:
            # Should return None (passthrough)
            if result is None:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
            detail = f"expected=passthrough, got={'passthrough' if result is None else result.get('skill')}"
        else:
            if result and result.get('skill') == expected_skill:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
            got = result.get('skill') if result else 'None'
            detail = f"expected={expected_skill}, got={got}"

        print(f"  [{status}] \"{message}\" → {detail}")

    print()
    print(f"  Results: {passed}/{passed+failed} passed")
    return failed == 0


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print_header()

    # Step 1: Check preconditions
    if not check_preconditions():
        print()
        print("ABORTED: Preconditions not met.")
        sys.exit(1)

    # Step 2: Create backup
    if not create_backup():
        print()
        print("ABORTED: Backup failed.")
        sys.exit(1)

    # Step 3: Inject router code
    if not inject_router():
        print()
        print("ABORTED: Injection failed. Restoring backup...")
        shutil.copy2(os.path.join(BACKUP_DIR, BACKUP_NAME), TARGET_FILE)
        print("Backup restored.")
        sys.exit(1)

    # Step 4: Patch chat() function
    if not patch_chat_function():
        print()
        print("ABORTED: Patch failed. Restoring backup...")
        shutil.copy2(os.path.join(BACKUP_DIR, BACKUP_NAME), TARGET_FILE)
        print("Backup restored.")
        sys.exit(1)

    # Step 5: Verify
    if not verify_patch():
        print()
        print("WARNING: Verification found issues. Check manually.")
        print(f"Backup available at: {BACKUP_DIR}/{BACKUP_NAME}")
        # Don't auto-rollback here — let human decide
    else:
        print("  All checks passed!")

    # Step 6: Functional tests
    print()
    if run_functional_test():
        print("  All functional tests passed!")
    else:
        print("  WARNING: Some tests failed. Review before restarting.")

    # Summary
    print()
    print("=" * 70)
    print("  DEPLOYMENT COMPLETE")
    print("=" * 70)
    print()
    print("  NEXT STEPS:")
    print()
    print("  1. Review the patch:")
    print(f"     grep -n 'constitutional_local_router' {TARGET_FILE}")
    print()
    print("  2. Restart HUB (port 8085):")
    print("     # Find PID")
    print("     ss -tulnp | grep 8085")
    print("     # Graceful restart (DO NOT kill -9!)")
    print("     kill -TERM <PID>")
    print("     sleep 2")
    print(f"     cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/hub_8085.log 2>&1 &")
    print()
    print("  3. Test live:")
    print('     curl -X POST http://localhost:8085/api/chat \\')
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"message\": \"Wie kann ich das Template nutzen?\", \"lang\": \"de\"}'")
    print()
    print("  4. Expected response should contain:")
    print('     "routed_by": "constitutional-local"')
    print('     "skill": "tutorial-mode"')
    print('     "dragon": "windi-local"')
    print()
    print("  ROLLBACK if needed:")
    print(f"     cp {BACKUP_DIR}/{BACKUP_NAME} {TARGET_FILE}")
    print()
    print("  Human decides. I structure. 🐉")
    print()


if __name__ == '__main__':
    main()
