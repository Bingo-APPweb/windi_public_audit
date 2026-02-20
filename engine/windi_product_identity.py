"""
WINDI Product Identity Module
Handles product questions with pre-defined answers
"""

def is_product_question(text: str) -> bool:
    """Detect questions about WINDI product, pricing, privacy"""
    text_lower = text.lower()
    
    product_triggers = [
        # Pricing
        'kostet', 'preis', 'pricing', 'bezahlen', 'geld', 'kosten',
        'gratis', 'free', 'kostenlos', 'umsonst', 'tarif', 'abo',
        # Privacy
        'daten', 'data', 'privacy', 'datenschutz', 'dsgvo',
        'privat', 'sicher', 'sicherheit', 'lgpd',
        # Ads
        'werbung', 'ads', 'anzeige', 'werbefrei',
        # Business
        'geschäftsmodell', 'business model', 'verdient', 'revenue',
        # Trust
        'vertrauen', 'trust', 'garantie', 'guarantee',
        # Product
        'was ist windi', 'what is windi', 'o que é windi',
        'windi funktioniert', 'how windi works', 'como funciona'
    ]
    
    return any(trigger in text_lower for trigger in product_triggers)


def get_product_answer(message: str, lang: str = 'de') -> str:
    """Get pre-defined answer for product questions"""
    message_lower = message.lower()
    
    # Detect question type
    if any(w in message_lower for w in ['werbung', 'ads', 'anzeige']):
        return _get_ads_answer(lang)
    
    elif any(w in message_lower for w in ['daten', 'data', 'privacy', 'datenschutz']):
        return _get_privacy_answer(lang)
    
    elif any(w in message_lower for w in ['kostet', 'preis', 'pricing', 'kosten', 'tarif']):
        return _get_pricing_answer(lang)
    
    elif any(w in message_lower for w in ['was ist windi', 'what is windi', 'o que é']):
        return _get_what_is_windi(lang)
    
    elif any(w in message_lower for w in ['geschäftsmodell', 'business model', 'verdient']):
        return _get_business_model(lang)
    
    else:
        # Generic product answer
        return _get_generic_product(lang)


def _get_ads_answer(lang: str) -> str:
    """Answer about ads/advertising"""
    answers = {
        'de': """Nein. WINDI zeigt keine Werbung. Niemals.

Unser Geschäftsmodell basiert auf Governance-Instrumenten, nicht auf Werbung oder Datenverkauf.

**Bei uns sind Sie nicht das Produkt — bei uns sind Sie der Souverän.**

Human decides. I structure.""",
        
        'en': """No. WINDI shows no advertising. Never.

Our business model is based on governance instruments, not on advertising or data sales.

**With us, you are not the product — with us, you are the sovereign.**

Human decides. I structure.""",
        
        'pt': """Não. WINDI não exibe publicidade. Nunca.

Nosso modelo de negócio se baseia em instrumentos de governança, não em publicidade ou venda de dados.

**Conosco, você não é o produto — conosco, você é o soberano.**

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])


def _get_privacy_answer(lang: str) -> str:
    """Answer about data privacy"""
    answers = {
        'de': """Ihre Daten bleiben auf Ihrem Gerät. WINDI speichert keine sensiblen Inhalte.

**Zero-Knowledge-Architektur:**
- SGE (Semantic Governance Engine) läuft lokal auf Ihrem Gerät
- WINDI speichert NUR: Hash + Kategorien + Metadaten + Entscheidung
- KEINE sensiblen Daten werden zentral gespeichert

**Der Client bewahrt die Daten. WINDI bewahrt den BEWEIS der Tugend.**

Unsere Server stehen in Deutschland (Strato), alle Daten bleiben in der EU. DSGVO-konform, EU AI Act-ready von Anfang an.

Human decides. I structure.""",
        
        'en': """Your data stays on your device. WINDI stores no sensitive content.

**Zero-Knowledge Architecture:**
- SGE (Semantic Governance Engine) runs locally on your device
- WINDI stores ONLY: hash + categories + metadata + decision
- NO sensitive data stored centrally

**The client keeps the data. WINDI keeps the PROOF of virtue.**

Our servers are in Germany (Strato), all data stays in the EU. GDPR-compliant, EU AI Act-ready from day one.

Human decides. I structure.""",
        
        'pt': """Seus dados permanecem em seu dispositivo. WINDI não armazena conteúdo sensível.

**Arquitetura Zero-Knowledge:**
- SGE (Semantic Governance Engine) roda localmente em seu dispositivo
- WINDI armazena APENAS: hash + categorias + metadados + decisão
- NENHUM dado sensível armazenado centralmente

**O cliente guarda os dados. WINDI guarda a PROVA da virtude.**

Nossos servidores estão na Alemanha (Strato), todos os dados permanecem na UE. Conforme LGPD/GDPR, EU AI Act-ready desde o início.

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])


def _get_pricing_answer(lang: str) -> str:
    """Answer about pricing"""
    answers = {
        'de': """WINDI bietet drei Stufen:

**FREE (€0)**
- Bis zu 3 Nutzer
- Editor, Basis-SGE, 3 ISP-Beispiele
- Chat Agent, ISP Creator

**PRO (€25-40/Nutzer/Monat)**
- Volle SGE (6 Ebenen)
- Unbegrenzte ISPs
- Priority Support

**ENTERPRISE (€80-120/Nutzer/Monat)**
- Controller Dashboard
- Multi-Clone Mesh
- EU AI Act Compliance-Paket

Das kostenlose Angebot ist unsere Einladung, WINDI kennenzulernen. Keine versteckten Kosten, keine Werbung, kein Datenverkauf.

Human decides. I structure.""",
        
        'en': """WINDI offers three tiers:

**FREE (€0)**
- Up to 3 users
- Editor, Basic SGE, 3 ISP samples
- Chat Agent, ISP Creator

**PRO (€25-40/user/month)**
- Full SGE (6 layers)
- Unlimited ISPs
- Priority Support

**ENTERPRISE (€80-120/user/month)**
- Controller Dashboard
- Multi-Clone Mesh
- EU AI Act Compliance Pack

The free offering is our invitation to discover WINDI. No hidden costs, no advertising, no data sales.

Human decides. I structure.""",
        
        'pt': """WINDI oferece três níveis:

**FREE (€0)**
- Até 3 usuários
- Editor, SGE Básico, 3 exemplos de ISP
- Agente de Chat, Criador de ISP

**PRO (€25-40/usuário/mês)**
- SGE completo (6 camadas)
- ISPs ilimitados
- Suporte prioritário

**ENTERPRISE (€80-120/usuário/mês)**
- Dashboard do Controlador
- Malha Multi-Clone
- Pacote de Conformidade EU AI Act

A oferta gratuita é nosso convite para conhecer o WINDI. Sem custos ocultos, sem publicidade, sem venda de dados.

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])


def _get_what_is_windi(lang: str) -> str:
    """Answer: What is WINDI?"""
    answers = {
        'de': """WINDI — **W**e **I**nvite **N**ew **D**ecision **I**ntelligence.

Ein governance-bewusstes Document Intelligence System, das Menschen hilft, bessere Entscheidungen zu treffen — und dabei ihre Souveränität bewahrt.

**Grundprinzip:**
"KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."

**A4 Desk** ist Ihr digitaler Arbeitsplatz — wie ein intelligentes Büro, das nicht nur Dokumente erstellt, sondern auch deren Qualität und Compliance automatisch überwacht.

Human decides. I structure.""",
        
        'en': """WINDI — **W**e **I**nvite **N**ew **D**ecision **I**ntelligence.

A governance-aware Document Intelligence System that helps humans make better decisions while preserving their sovereignty.

**Core Principle:**
"AI processes. Human decides. WINDI guarantees."

**A4 Desk** is your digital workspace — like an intelligent office that not only creates documents but also automatically monitors their quality and compliance.

Human decides. I structure.""",
        
        'pt': """WINDI — **W**e **I**nvite **N**ew **D**ecision **I**ntelligence.

Um Sistema de Inteligência Documental consciente de governança que ajuda humanos a tomar melhores decisões preservando sua soberania.

**Princípio Central:**
"IA processa. Humano decide. WINDI garante."

**A4 Desk** é seu espaço de trabalho digital — como um escritório inteligente que não apenas cria documentos mas também monitora automaticamente sua qualidade e conformidade.

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])


def _get_business_model(lang: str) -> str:
    """Answer about business model"""
    answers = {
        'de': """WINDI verdient mit **geschützten Entscheidungen**, nicht mit Datenspeicherung.

**Metapher:**
- SAP = 10.000 Nutzer pro Prozess (Ressourcenverwaltung)
- WINDI = 10 Entscheider pro Entscheidung (Governance)

WINDI ersetzt SAP nicht. **WINDI GARANTIERT SAP.**

WINDI ist der ethische Schutzschalter für institutionelle Entscheidungen.

Sie bezahlen für Governance-Instrumente, nicht für Speicherplatz.

Human decides. I structure.""",
        
        'en': """WINDI earns from **protected decisions**, not from data storage.

**Metaphor:**
- SAP = 10,000 users per process (resource management)
- WINDI = 10 decision-makers per decision (governance)

WINDI doesn't replace SAP. **WINDI GUARANTEES SAP.**

WINDI is the ethical circuit breaker for institutional decisions.

You pay for governance instruments, not for storage space.

Human decides. I structure.""",
        
        'pt': """WINDI ganha com **decisões protegidas**, não com armazenamento de dados.

**Metáfora:**
- SAP = 10.000 usuários por processo (gestão de recursos)
- WINDI = 10 tomadores de decisão por decisão (governança)

WINDI não substitui SAP. **WINDI GARANTE SAP.**

WINDI é o disjuntor ético para decisões institucionais.

Você paga por instrumentos de governança, não por espaço de armazenamento.

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])


def _get_generic_product(lang: str) -> str:
    """Generic product answer"""
    answers = {
        'de': """WINDI Publishing House — Kempten (Allgäu), Bayern, Deutschland.

**Kernwerte:**
- Zero-Knowledge-Architektur (Daten bleiben beim Nutzer)
- Keine Werbung. Niemals.
- DSGVO-konform, EU AI Act-ready
- Geschäftsmodell: Governance-Instrumente, nicht Datenverkauf

Bei uns sind Sie nicht das Produkt — bei uns sind Sie der Souverän.

Human decides. I structure.""",
        
        'en': """WINDI Publishing House — Kempten (Allgäu), Bavaria, Germany.

**Core Values:**
- Zero-Knowledge Architecture (data stays with user)
- No advertising. Never.
- GDPR-compliant, EU AI Act-ready
- Business model: governance instruments, not data sales

With us, you are not the product — with us, you are the sovereign.

Human decides. I structure.""",
        
        'pt': """WINDI Publishing House — Kempten (Allgäu), Baviera, Alemanha.

**Valores Centrais:**
- Arquitetura Zero-Knowledge (dados ficam com o usuário)
- Sem publicidade. Nunca.
- Conforme LGPD/GDPR, EU AI Act-ready
- Modelo de negócio: instrumentos de governança, não venda de dados

Conosco, você não é o produto — conosco, você é o soberano.

Human decides. I structure."""
    }
    return answers.get(lang, answers['de'])
