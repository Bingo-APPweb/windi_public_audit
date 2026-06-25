"""
VPSE · Knowledge Base (Soberania local)
=======================================
windi-sovereignty-quality aplicado: decomposição e mapeamento usam
inteligência LOCAL. Nenhum token externo gasto nesta camada.
O LLM externo (se algum dia ligado) entra SÓ no Risk/Compliance refinement,
onde a qualidade justifica o custo — e nunca nesta base determinística.

Esta é a "engine de busca direcionada à missão constitucional":
não busca a web, busca PARA DENTRO do WINDI-HIOS.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# DOMÍNIOS — classificador léxico. Cada domínio tem termos-gatilho.
# ---------------------------------------------------------------------------
DOMAIN_LEXICON: Dict[str, List[str]] = {
    "live_streaming": ["livestream", "stream", "podcast", "broadcast", "ao vivo",
                       "transmiss", "watch time", "view count", "audiência", "audience",
                       "espectador", "viewer"],
    "audience_engagement": ["interaction", "interação", "engagement", "gamif",
                            "participa", "vote", "votação", "chat", "reaction"],
    "promotional_mechanics": ["bingo", "sorteio", "raffle", "prize", "prémio", "premio",
                              "gift", "brinde", "sponsor", "patrocin", "reward", "recompensa",
                              "lottery", "loteria", "sweepstake", "contest", "concurso",
                              "aposta", "bet", "gambling", "jogo de azar"],
    "identity": ["identity", "identidade", "did", "login", "auth", "wallet",
                 "credential", "kyc", "verific"],
    "document_governance": ["document", "documento", "contract", "contrato",
                            "report", "relatório", "policy", "template", "assinatura",
                            "signature", "audit", "auditoria"],
    "fintech_payments": ["payment", "pagamento", "money", "dinheiro", "cash", "iban",
                         "stripe", "paypal", "subscription", "subscrição", "fatura",
                         "invoice", "checkout", "cartão", "card"],
    "health_med": ["health", "saúde", "saude", "medical", "médico", "patient",
                   "paciente", "diagnos", "clinical", "clínic", "hospital"],
    "education": ["course", "curso", "learn", "aprend", "academy", "academia",
                  "training", "formação", "student", "aluno", "ensino"],
    "data_ai": ["ai", "ia", "machine learning", "model", "modelo", "dataset",
                "algorithm", "algoritmo", "llm", "neural", "training data"],
    "social_platform": ["social", "feed", "post", "follow", "comunidade", "community",
                        "network", "rede social", "share", "partilha"],
    "research": ["research", "pesquisa", "investigação", "study", "estudo",
                 "experiment", "hypothesis", "hipótese"],
}

# ---------------------------------------------------------------------------
# MÓDULOS WINDI — mapeamento domínio/sinal → módulo aplicável.
# Fonte: location-matrix v1.0 (18 Fev 2026) + memória de sessão.
# TODOS marcados [estimado] na saída porque a base pode estar desatualizada.
# ---------------------------------------------------------------------------
WINDI_MODULES: Dict[str, Dict[str, str]] = {
    "Verify Public": {
        "trigger": "qualquer ideia que precise de prova pública verificável",
        "role": "admissibilidade pública de afirmações",
    },
    "Forensic Ledger": {
        "trigger": "necessidade de registo imutável append-only",
        "role": "selo e cadeia de prova (:8101 — verificar)",
    },
    "Receipts": {
        "trigger": "necessidade de comprovativo de evento/transação",
        "role": "comprovativo emitido e verificável",
    },
    "DID / Wallet": {
        "trigger": "identidade de utilizador, autoria, KYC, login soberano",
        "role": "fio de identidade — porta de nascimento /farm/claim",
    },
    "Academy": {
        "trigger": "componente educativo, onboarding, pedagogia",
        "role": "ensino e onboarding soberano",
    },
    "Document Factory / A4 Desk": {
        "trigger": "geração de documentos, contratos, relatórios, templates",
        "role": "fábrica de documentos com governança (BABEL)",
    },
    "Governance / LAW (Sentinel)": {
        "trigger": "risco regulatório, compliance, decisão de autoridade",
        "role": "guarda constitucional e monitorização LAW (:8102)",
    },
    "SGE Analyzer": {
        "trigger": "documento ou afirmação com risco semântico R0-R5",
        "role": "deteção de risco documental em 6 camadas",
    },
    "Payment Sovereignty Bridge": {
        "trigger": "cobrança, subscrição, tier pago, dinheiro real",
        "role": "pagamento sem tocar dados financeiros (IP1)",
    },
}

# ---------------------------------------------------------------------------
# SINAIS DE RISCO REGULATÓRIO — heurística léxica, SEMPRE [estimado].
# NÃO é parecer jurídico. Levanta a pergunta, não dá a resposta.
# ---------------------------------------------------------------------------
REGULATORY_SIGNALS: Dict[str, Dict] = {
    "gambling_lottery": {
        "terms": ["bingo", "lottery", "loteria", "raffle", "sorteio", "bet",
                  "aposta", "gambling", "jogo de azar", "sweepstake", "prize",
                  "prémio", "premio", "cash prize", "win money"],
        "question": "Pode ser interpretado como lotaria/jogo regulado? "
                    "Há entrada paga (consideration)? Há prémio em dinheiro? "
                    "Há elemento de azar (chance)?",
        "safer_framing": "Sistema promocional de engagement: sem entrada paga, "
                         "sem prémio em dinheiro, regras transparentes, verificar jurisdição.",
        "jurisdiction_sensitive": True,
    },
    "personal_data_gdpr": {
        "terms": ["data", "dados", "user", "utilizador", "profile", "perfil",
                  "track", "rastrear", "analytics", "behavior", "comportamento",
                  "email", "phone", "telefone"],
        "question": "Recolhe dados pessoais? GDPR/DSGVO aplica? "
                    "Há base legal, minimização, consentimento, retenção definida?",
        "safer_framing": "Minimização de dados, consentimento explícito, "
                         "retenção definida, DID como camada de soberania de identidade.",
        "jurisdiction_sensitive": True,
    },
    "financial_regulation": {
        "terms": ["payment", "pagamento", "money", "dinheiro", "invest", "crypto",
                  "token", "wallet", "iban", "transfer", "transferência"],
        "question": "Move ou custodia valor? Pode cair em regulação financeira "
                    "(PSD2, e-money, KYC/AML)?",
        "safer_framing": "Não custodiar valor; usar processador externo certificado; "
                         "separação financeira IP1 (Payment Sovereignty).",
        "jurisdiction_sensitive": True,
    },
    "health_regulation": {
        "terms": ["health", "saúde", "medical", "médico", "diagnos", "patient",
                  "treatment", "tratamento", "clinical"],
        "question": "Faz claim de saúde/diagnóstico? Pode ser dispositivo médico "
                    "(MDR) ou exigir supervisão clínica?",
        "safer_framing": "Não diagnosticar; informação ≠ aconselhamento clínico; "
                         "disclaimer e supervisão humana.",
        "jurisdiction_sensitive": True,
    },
    "ai_act": {
        "terms": ["ai", "ia", "model", "modelo", "automat", "decision", "decisão",
                  "scoring", "profiling", "biometr", "face", "recognition"],
        "question": "Sistema de IA com risco sob o EU AI Act? Há decisão automatizada "
                    "sobre pessoas? Requer supervisão humana (Art. 14)?",
        "safer_framing": "Supervisão humana obrigatória (I9), transparência, "
                         "human-in-the-loop, classificação de risco AI Act.",
        "jurisdiction_sensitive": True,
    },
    "minors_protection": {
        "terms": ["child", "criança", "kid", "minor", "menor", "teen", "school",
                  "escola", "student", "aluno"],
        "question": "Pode atingir menores? Há proteção específica e consentimento parental?",
        "safer_framing": "Verificação de idade, consentimento parental, "
                         "design apropriado à idade.",
        "jurisdiction_sensitive": True,
    },
}

# ---------------------------------------------------------------------------
# Complexidade técnica — heurística por contagem de domínios + módulos.
# ---------------------------------------------------------------------------
def estimate_complexity(n_domains: int, n_modules: int, n_risks: int) -> str:
    score = n_domains + n_modules + (n_risks * 2)
    if score <= 3:
        return "baixa"
    if score <= 7:
        return "média"
    return "alta"
