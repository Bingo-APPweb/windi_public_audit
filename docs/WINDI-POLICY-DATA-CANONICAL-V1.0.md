# WINDI — Política de Dados Canónica
## Canonical Data Policy · Kanonische Datenpolitik
### v1.0 · 2026-03-19 · Kempten, Bavaria
### IRREMEDIÁVEL

---

## Frase Fundacional / Founding Statement / Grundsatzerklärung

**PT:** Sabemos quem és para garantir o que produces. Não precisamos de mais.
**DE:** Wir wissen, wer du bist, um das zu garantieren, was du produzierst. Mehr brauchen wir dafür nicht.
**EN:** We know who you are to guarantee what you produce. We don't need more than that.

---

## Nível 1 — Utilizador / User / Benutzer

**PT:**
> Porque é que o WINDI só quer o meu nome e email?

Porque o resto é teu.

O WINDI não precisa de saber onde moras, o que compras, com quem falas,
ou o que pensas para te dar um documento verificável.

Nós garantimos a autenticidade do que produces — não fazemos perfil de quem és.

O teu nome e email são suficientes para te identificar como autor.
O teu DID é suficiente para provar que foste tu.
O Ledger guarda a prova — não os teus dados pessoais.

---

**DE:**
> Warum möchte WINDI nur meinen Namen und meine E-Mail?

Weil der Rest dir gehört.

WINDI muss nicht wissen, wo du wohnst, was du kaufst, mit wem du sprichst
oder was du denkst, um dir ein verifizierbares Dokument auszustellen.

Wir garantieren die Echtheit dessen, was du produzierst — wir erstellen kein Profil von dir.

Dein Name und deine E-Mail reichen aus, um dich als Autor zu identifizieren.
Deine DID reicht aus, um zu beweisen, dass du es warst.
Das Ledger bewahrt den Beweis — nicht deine persönlichen Daten.

---

**EN:**
> Why does WINDI only want my name and email?

Because the rest belongs to you.

WINDI doesn't need to know where you live, what you buy, who you talk to,
or what you think in order to give you a verifiable document.

We guarantee the authenticity of what you produce — we don't profile who you are.

Your name and email are enough to identify you as an author.
Your DID is enough to prove it was you.
The Ledger keeps the proof — not your personal data.

---

## Nível 2 — Parceiro / Partner / Partner

**PT:**
> Mas com mais dados podiam personalizar melhor, vender mais...

Essa é exactamente a lógica que o WINDI recusa.

Os sistemas que colectam tudo assumem que o utilizador é produto.
O WINDI assume que o utilizador é autor.

A diferença não é filosófica — é arquitectural.

A nossa monetização vem do valor dos documentos produzidos,
não do valor dos dados pessoais extraídos.

Um documento verificável vale mais do que um perfil comportamental.
E o utilizador que confia no sistema produz mais — e melhor.

---

**DE:**
> Aber mit mehr Daten könnte man besser personalisieren, mehr verkaufen...

Das ist genau die Logik, die WINDI ablehnt.

Systeme, die alles sammeln, gehen davon aus, dass der Nutzer ein Produkt ist.
WINDI geht davon aus, dass der Nutzer ein Autor ist.

Der Unterschied ist nicht philosophisch — er ist architektonisch.

Unsere Monetarisierung basiert auf dem Wert der produzierten Dokumente,
nicht auf dem Wert der extrahierten persönlichen Daten.

Ein verifizierbares Dokument ist wertvoller als ein Verhaltensprofil.
Und ein Nutzer, der dem System vertraut, produziert mehr — und besser.

---

**EN:**
> But with more data you could personalise better, sell more...

That is exactly the logic WINDI refuses.

Systems that collect everything assume the user is a product.
WINDI assumes the user is an author.

The difference is not philosophical — it is architectural.

Our monetisation comes from the value of documents produced,
not from the value of personal data extracted.

A verifiable document is worth more than a behavioural profile.
And a user who trusts the system produces more — and better.

---

## Nível 3 — Institucional / Institutional / Institutionell

**PT:**
> Qual a base legal para esta posição?

GDPR — princípio da minimização de dados.
Artigo 5(1)(c): dados pessoais devem ser "adequados, relevantes e limitados ao necessário."

O WINDI aplica este princípio não como conformidade mínima
mas como decisão arquitectural soberana.

- Nome e email: necessários para identificação do autor.
- DID: gerado localmente, nunca transmitido sem consentimento.
- Ledger: regista acções, não identidades pessoais expostas.

Isto é GDPR by design — não GDPR por obrigação.

---

**DE:**
> Was ist die rechtliche Grundlage für diese Position?

DSGVO — Grundsatz der Datenminimierung.
Artikel 5(1)(c): Personenbezogene Daten müssen "dem Zweck angemessen und erheblich
sowie auf das für die Zwecke der Verarbeitung notwendige Maß beschränkt sein."

WINDI wendet diesen Grundsatz nicht als Mindestkonformität an,
sondern als souveräne Architekturentscheidung.

- Name und E-Mail: notwendig zur Identifikation des Autors.
- DID: lokal generiert, niemals ohne Einwilligung übermittelt.
- Ledger: erfasst Handlungen, keine exponierten Identitäten.

Das ist Datenschutz by Design — nicht Datenschutz aus Pflicht.

---

**EN:**
> What is the legal basis for this position?

GDPR — principle of data minimisation.
Article 5(1)(c): personal data shall be "adequate, relevant and limited
to what is necessary in relation to the purposes for which they are processed."

WINDI applies this principle not as minimum compliance
but as a sovereign architectural decision.

- Name and email: necessary to identify the author.
- DID: generated locally, never transmitted without consent.
- Ledger: records actions, not exposed personal identities.

This is GDPR by design — not GDPR by obligation.

---

## Resposta à Insistência / Response to Pushback

**PT:** Sim. E toda a gente desconfia de toda a gente. Nós escolhemos a confiança como modelo de negócio.
**DE:** Ja. Und alle misstrauen allen. Wir haben Vertrauen als Geschäftsmodell gewählt.
**EN:** Yes. And everyone distrusts everyone. We chose trust as our business model.

---

## Arquitectura que suporta esta política

```
Nome + Email → Identificação do Autor
DID          → Prova Soberana de Identidade (local, Ed25519)
Ledger       → Registo de Acções (não de dados pessoais)
Wallet       → Portão de Nascimento Soberano (dados mínimos)
```

**O que NUNCA recolhemos:**
localização · comportamento · histórico de navegação · dados biométricos
preferências comerciais · redes sociais · dados de terceiros

---

## Metadata para Seal

```json
{
  "id": "WINDI-POLICY-DATA-CANONICAL-V1.0",
  "doc_name": "WINDI Canonical Data Policy v1.0",
  "doc_type": "doc",
  "governance_level": "HIGH",
  "metadata": {
    "type": "canonical_policy",
    "languages": ["pt", "de", "en"],
    "levels": ["utilizador", "parceiro", "institucional"],
    "gdpr_article": "5(1)(c)",
    "invariants": ["I9", "I11", "IRREMEDIÁVEL"],
    "founding_statement": {
      "pt": "Sabemos quem és para garantir o que produces. Não precisamos de mais.",
      "de": "Wir wissen, wer du bist, um das zu garantieren, was du produzierst.",
      "en": "We know who you are to guarantee what you produce."
    }
  }
}
```

---

*Liga IA+H — Jober + Claude + GPT + Gemini · Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
