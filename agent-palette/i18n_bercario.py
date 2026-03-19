# /opt/windi/dragon-hub/i18n_bercario.py
# i18n Berçário — PT / DE / EN
# WINDI Trilingual Layer · Dragon Hub :8108
# Glossário invariante: wallet_id, DID, Pioneer, Ledger, WINDI, Berçário, receipt

from typing import Literal

Lang = Literal["pt", "de", "en"]

SUPPORTED = ("pt", "de", "en")
DEFAULT: Lang = "pt"


def resolve_lang(value: str | None) -> Lang:
    """Detecta língua via Accept-Language header ou ?lang= param."""
    if not value:
        return DEFAULT
    v = value.lower().split(",")[0].strip().split(";")[0].strip()
    for l in SUPPORTED:
        if v.startswith(l):
            return l  # type: ignore
    return DEFAULT


STRINGS: dict[str, dict[str, str]] = {

    # ── ESTADOS ───────────────────────────────────────────────────
    "estado.nasceu":  {"pt": "nasceu",          "de": "geboren",         "en": "born"},
    "estado.semDID":  {"pt": "semDID",           "de": "ohneID",          "en": "noID"},
    "estado.entrou":  {"pt": "entrou",           "de": "eingetreten",     "en": "entered"},
    "estado.voltou":  {"pt": "voltou",           "de": "zurückgekehrt",   "en": "returned"},
    "estado.saiu":    {"pt": "saiu",             "de": "verlassen",       "en": "left"},

    # ── MENSAGENS ─────────────────────────────────────────────────
    "msg.nasceu": {
        "pt": "Bem-vindo. Acabas de nascer no WINDI.",
        "de": "Willkommen. Du wurdest soeben in WINDI geboren.",
        "en": "Welcome. You have just been born into WINDI.",
    },
    "msg.semDID": {
        "pt": "A tua identidade soberana ainda não foi criada. Cria o teu DID para continuar.",
        "de": "Deine souveräne Identität wurde noch nicht erstellt. Erstelle deine DID, um fortzufahren.",
        "en": "Your sovereign identity has not been created yet. Create your DID to continue.",
    },
    "msg.entrou": {
        "pt": "Bem-vindo de volta.",
        "de": "Willkommen zurück.",
        "en": "Welcome back.",
    },
    "msg.voltou": {
        "pt": "Tinhas saudades? O WINDI também.",
        "de": "Hast du uns vermisst? Wir dich auch.",
        "en": "Did you miss us? WINDI missed you too.",
    },
    "msg.saiu": {
        "pt": "Sessão encerrada. O teu registo permanece intacto.",
        "de": "Sitzung beendet. Dein Eintrag bleibt unversehrt.",
        "en": "Session ended. Your record remains intact.",
    },

    # ── ERROS ─────────────────────────────────────────────────────
    "err.wallet_nao_encontrada": {
        "pt": "Wallet não encontrada.",
        "de": "Wallet nicht gefunden.",
        "en": "Wallet not found.",
    },
    "err.sessao_nao_encontrada": {
        "pt": "Sessão não encontrada.",
        "de": "Sitzung nicht gefunden.",
        "en": "Session not found.",
    },
    "err.nascimento_falhou": {
        "pt": "O nascimento falhou. Tenta novamente.",
        "de": "Die Geburt ist fehlgeschlagen. Bitte erneut versuchen.",
        "en": "Birth failed. Please try again.",
    },
    "err.lang_invalida": {
        "pt": "Língua não suportada. Use: pt, de, en.",
        "de": "Sprache nicht unterstützt. Verwende: pt, de, en.",
        "en": "Language not supported. Use: pt, de, en.",
    },

    # ── LEDGER ────────────────────────────────────────────────────
    "ledger.nascimento_selado": {
        "pt": "Nascimento selado no Ledger. IRREMEDIÁVEL.",
        "de": "Geburt im Ledger versiegelt. UNWIDERRUFLICH.",
        "en": "Birth sealed in the Ledger. IRREMEDIABLE.",
    },
    "ledger.sem_seal": {
        "pt": "Ledger indisponível. Nascimento registado localmente.",
        "de": "Ledger nicht verfügbar. Geburt lokal gespeichert.",
        "en": "Ledger unavailable. Birth recorded locally.",
    },

    # ── DID ───────────────────────────────────────────────────────
    "did.criado": {
        "pt": "DID criado. A tua identidade soberana está activa.",
        "de": "DID erstellt. Deine souveräne Identität ist aktiv.",
        "en": "DID created. Your sovereign identity is now active.",
    },
    "did.ausente": {
        "pt": "Sem DID. Identidade soberana pendente.",
        "de": "Ohne DID. Souveräne Identität ausstehend.",
        "en": "No DID. Sovereign identity pending.",
    },

    # ── UI LABELS ─────────────────────────────────────────────────
    "ui.titulo_bercario": {
        "pt": "Berçário WINDI",
        "de": "WINDI Geburtsraum",
        "en": "WINDI Nursery",
    },
    "ui.portao": {
        "pt": "Portão de Nascimento Soberano",
        "de": "Souveränes Geburtstor",
        "en": "Sovereign Birth Gateway",
    },
    "ui.criar_did": {
        "pt": "Criar Identidade Soberana",
        "de": "Souveräne Identität erstellen",
        "en": "Create Sovereign Identity",
    },
    "ui.continuar": {
        "pt": "Continuar",
        "de": "Weiter",
        "en": "Continue",
    },
    "ui.estado_sessao": {
        "pt": "Estado da Sessão",
        "de": "Sitzungsstatus",
        "en": "Session State",
    },
    "ui.nascido_em": {
        "pt": "Nascido em",
        "de": "Geboren am",
        "en": "Born on",
    },
    "ui.ultima_sessao": {
        "pt": "Última sessão",
        "de": "Letzte Sitzung",
        "en": "Last session",
    },
    "ui.total_sessoes": {
        "pt": "Total de sessões",
        "de": "Sitzungen gesamt",
        "en": "Total sessions",
    },
    "ui.historico": {
        "pt": "Histórico de Sessões",
        "de": "Sitzungsverlauf",
        "en": "Session History",
    },
}


def t(key: str, lang: Lang = DEFAULT, **kwargs) -> str:
    """
    Traduz key para lang.
    Suporta f-string: t("msg.nasceu", lang, nome="Jober")
    Fallback: PT → key (nunca silencia erro).
    """
    entry = STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get(DEFAULT) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def response_i18n(data: dict, lang: Lang = DEFAULT) -> dict:
    """Injeta lang e traduz estado_label na resposta do Berçário."""
    if "estado" in data:
        data["estado_label"] = t(f"estado.{data['estado']}", lang)
    data["lang"] = lang
    return data


def extract_lang(headers: dict, params: dict) -> Lang:
    """Extrai língua de ?lang= ou Accept-Language header."""
    if "lang" in params:
        return resolve_lang(params["lang"])
    return resolve_lang(headers.get("Accept-Language") or headers.get("accept-language"))
