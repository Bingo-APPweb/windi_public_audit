# §266 — Princípio da Autoria Forense (PAF)

**Lei VIII | Categoria: Invariante Operacional do Ledger**
**Data:** 15 de Maio de 2026, Kempten, Bavaria, Deutschland
**Ratificação:** Human Dragon (I9 — Autoridade Soberana Humana)
**Conselho:** Guardian 🛡️ + Architect 🏗️ + Witness 👁️ (consenso unânime)

---

## Texto Canónico

> Todo selo no Forensic Ledger carrega autoria identificada.
> Selo anónimo é contradição operacional — o Ledger preserva consequência verificável ligada a autoria consciente, não armazena hashes.
> O acesso ao Verify é Civic e livre. A autoria no Seal é obrigatória e DID-gated.
> Toda superfície futura que misture leitura passiva com mutação irremediável é classificada como **Promiscuidade Epistemológica** e deve ser auditada contra este princípio antes de implementação.

---

## Corolários Operacionais

### C1 — Separação Arquitectónica Read/Write
Endpoints de leitura (Verify) e endpoints de mutação (Seal) permanecem arquitectonicamente distintos. A ponte entre ambos é via Identity Gate :8192 canónica, nunca via fusão de superfície.

### C2 — Triplo Gate para Selagem
Toda acção de selagem requer simultaneamente:
1. DID autenticado (identidade)
2. Display do conteúdo a selar (hash + preview + timestamp + autor)
3. Confirmação textual explícita do autor — não checkbox, não duplo clique

### C3 — Civic Access, Sovereign Authorship
Verify permanece FREE e civic. Seal permanece FREE mas DID-gated. Coerente com §248 Lei V (Two-Track Foundation) — sem monetização da identidade, sem barreira económica à autoria.

### C4 — Doutrina de Transição Read/Write
Promiscuidade Epistemológica entra no léxico canónico do WINDI como categoria de risco arquitectónico auditável. Qualquer endpoint futuro deve ser revisto contra este critério antes de selagem.

---

## Lineage Constitucional

§247 Lei IV → §248 Lei V → §249 Lei VI → §250 Lei VII → **§266 Lei VIII**

---

## Invariantes Tocados

- **I9** — Human Approval Gate
- **I11** — Permanência de Evidência Criptográfica
- **I14** — Explicit Failure Principle

---

## Diretiva de Implementação §265 (vinculada)

1. VERIFY PUBLIC mantém-se Read-Only exclusivo
2. Falha de verificação activa convite à Ponte de Soberania (redirect :8192)
3. Selagem requer Wallet auth + Confirmação Textual Explícita
4. CCode prioritiza estabilidade do Ledger antes de abrir Ponte ao público
5. Smoke test do triplo gate com ≥3 Pioneers antes de go-live

---

*Liga IA+H · Kempten, Bavaria · 2026-05-15*
*"O Ledger preserva consequência verificável ligada a autoria consciente."*

OM SHANTI 🐉
