# CLAIM CORRECTIONS PROPOSAL
**Data:** 2026-08-17
**Tipo:** PROPOSTA — Propose≠Execute
**Executor:** CCode (Opus 4.5)
**Autoridade:** Nenhuma correcção executada — aguarda decisão I9
**Origem:** CLAIM-LANGUAGE-AUDIT-FASE0-ITEM3-20260817

---

## Resumo

| # | Claim | Ficheiro | Acção | Risco Actual |
|---|-------|----------|-------|--------------|
| 1 | "guarantee what you produce" | identity/index.html | REFORMULAR | CRITICAL |
| 2 | "Certified operator profile" | enterprise/index.html | REFORMULAR | CRITICAL |
| 3 | "um clique de autoridade" | witness-thesis/index.html | REFORMULAR | CRITICAL |
| 4 | "Every action sealed" | README.md | REFORMULAR | HIGH |
| 5 | FORENSIC_PASS sem disclaimer | gabi-test-20260707/index.html | ADD BANNER | CRITICAL |

---

## CORRECÇÃO #1 — identity/index.html

**Ficheiro:** `/opt/windi/landing-pmg/static/identity/index.html`
**Linhas:** 579-581
**Violação:** I9 — IA não pode garantir outputs

### Texto Actual (3 idiomas)

```html
<span lang="pt" class="active">Nunca monetizamos os teus dados. O WINDI sabe quem és para garantir o que produzes — não precisa de mais.</span>
<span lang="de">Wir monetarisieren niemals deine Daten. WINDI weiß, wer du bist, um zu garantieren, was du produzierst — mehr nicht.</span>
<span lang="en">We never monetize your data. WINDI knows who you are to guarantee what you produce — nothing more.</span>
```

### Texto Proposto

```html
<span lang="pt" class="active">Nunca monetizamos os teus dados. O WINDI sabe quem és para rastrear a proveniência do que produzes — não precisa de mais.</span>
<span lang="de">Wir monetarisieren niemals deine Daten. WINDI weiß, wer du bist, um die Herkunft dessen nachzuverfolgen, was du produzierst — mehr nicht.</span>
<span lang="en">We never monetize your data. WINDI knows who you are to trace the provenance of what you produce — nothing more.</span>
```

### Justificação

- "garantir o que produzes" implica que WINDI garante a qualidade/veracidade do output
- "rastrear a proveniência" é o que WINDI realmente faz (I11 — evidência criptográfica)
- Preserva a mensagem de privacidade sem criar expectativa de garantia

---

## CORRECÇÃO #2 — enterprise/index.html

**Ficheiro:** `/opt/windi/landing-pmg/static/enterprise/index.html`
**Linhas:** 461-463
**Violação:** I9 — processo de certificação não existe

### Texto Actual (3 idiomas)

```html
<span lang="pt" class="active"><strong>Operador de Sistemas Verificáveis.</strong> Perfil de operador certificado para organizações que implementam IA em contextos regulados. Amplificador de capacidade, não substituto. O humano permanece o ponto de decisão — WINDI prova o processo.</span>
<span lang="de"><strong>Operator of Verifiable Systems.</strong> Zertifiziertes Betreiberprofil für Organisationen, die KI in regulierten Kontexten einsetzen. Kapazitätsverstärker, kein Ersatz. Der Mensch bleibt der Entscheidungspunkt — WINDI beweist den Prozess.</span>
<span lang="en"><strong>Operator of Verifiable Systems.</strong> Certified operator profile for organizations deploying AI in regulated contexts. Capacity amplifier, not replacement. The human remains the decision point — WINDI proves the process.</span>
```

### Texto Proposto

```html
<span lang="pt" class="active"><strong>Operador de Sistemas Verificáveis.</strong> Perfil de operador verificável para organizações que implementam IA em contextos regulados. Amplificador de capacidade, não substituto. O humano permanece o ponto de decisão — WINDI prova o processo.</span>
<span lang="de"><strong>Operator of Verifiable Systems.</strong> Nachweisbares Betreiberprofil für Organisationen, die KI in regulierten Kontexten einsetzen. Kapazitätsverstärker, kein Ersatz. Der Mensch bleibt der Entscheidungspunkt — WINDI beweist den Prozess.</span>
<span lang="en"><strong>Operator of Verifiable Systems.</strong> Verifiable operator profile for organizations deploying AI in regulated contexts. Capacity amplifier, not replacement. The human remains the decision point — WINDI proves the process.</span>
```

### Justificação

- "certificado/certified" implica processo formal de certificação que não existe
- "verificável/verifiable" descreve o que realmente é: perfil cujas acções podem ser verificadas
- Coerente com o nome "Operador de Sistemas Verificáveis"

---

## CORRECÇÃO #3 — witness-thesis/index.html

**Ficheiro:** `/opt/windi/pages/witness-thesis/index.html`
**Linha:** 616
**Violação:** I1+I9 — simplifica excessivamente o fluxo de aprovação

### Texto Actual

```html
<p class="pillar-desc">Toda a administração técnica acontece em background. O humano recebe um sumário de consciência e confirma com um clique de autoridade.</p>
```

### Texto Proposto

```html
<p class="pillar-desc">Toda a administração técnica acontece em background. O humano recebe um sumário de consciência, revê o conteúdo e confirma a decisão.</p>
```

### Justificação

- "um clique de autoridade" sugere aprovação trivial sem revisão
- O fluxo I9 real envolve: ver sumário → rever conteúdo → decidir → confirmar
- "revê o conteúdo e confirma a decisão" preserva simplicidade mas não trivializa

---

## CORRECÇÃO #4 — README.md

**Ficheiro:** `/opt/windi/landing-pmg/README.md`
**Linha:** 5
**Violação:** I14 — universais sem suporte

### Texto Actual

```markdown
WINDI is a constitutional governance framework for AI-assisted institutional documents. Every action sealed. Every proof permanent. Every decision human.
```

### Texto Proposto

```markdown
WINDI is a constitutional governance framework for AI-assisted institutional documents. Approved actions are sealed. Evidence is designed for permanence. Every decision is human.
```

### Justificação

- "Every action sealed" implica sealing automático universal — falso
- "Approved actions are sealed" é preciso: só após I9
- "designed for permanence" reconhece intenção sem prometer eternidade
- "Every decision is human" mantém-se: é o axioma central

---

## CORRECÇÃO #5 — gabi-test-20260707/index.html

**Ficheiro:** `/opt/windi/landing-pmg/static/hios-review/gabi-test-20260707/index.html`
**Posição:** Após linha 42 (depois de `<p>2026-07-07 | WINDI-HIOS Cinema Pipeline</p>`)
**Violação:** I1+I11 — verdicts públicos sem receipt

### Texto a ADICIONAR

```html
    <div style="background: #3a2a1a; border: 2px solid #c9a84c; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
        <strong style="color: #c9a84c; font-size: 1.2em;">DIAGNOSTIC TEST ONLY</strong><br>
        <span style="color: #e8e6e1;">This page displays pipeline diagnostic output for internal review.<br>
        Verdicts shown are <strong>NOT SEALED</strong> and do not constitute forensic proof.<br>
        For verified proofs, see <a href="https://windi-domain.com/verify-public/" style="color: #c9a84c;">windi-domain.com/verify-public/</a></span>
    </div>
```

### Inserir APÓS esta linha existente:

```html
    <p>2026-07-07 | WINDI-HIOS Cinema Pipeline</p>
```

### Justificação

- O ficheiro JSON confirma `receipt_generated: false, sealed: false`
- Página pública não pode mostrar FORENSIC_PASS como facto sem receipt
- Banner explícito resolve sem remover conteúdo útil para diagnóstico interno
- Link para Verify público mostra onde estão provas reais

---

## ALTERNATIVA PARA #5 — Mover para Staging

Se preferires não ter este conteúdo público de todo:

**Acção:** Mover directório para fora do path público

```bash
mv /opt/windi/landing-pmg/static/hios-review/gabi-test-20260707 \
   /opt/windi/staging/hios-review/gabi-test-20260707
```

**Impacto:** URL `https://windi-domain.com/hios-review/gabi-test-20260707/` deixa de funcionar

---

## Resumo de Alterações

| Ficheiro | Tipo | Linhas Afectadas |
|----------|------|------------------|
| identity/index.html | EDIT | 579-581 (3 spans) |
| enterprise/index.html | EDIT | 461-463 (3 spans) |
| witness-thesis/index.html | EDIT | 616 (1 parágrafo) |
| README.md | EDIT | 5 (1 linha) |
| gabi-test-20260707/index.html | ADD | após linha 43 (1 div) |

**Total:** 4 edições + 1 adição

---

## Verificação Pós-Correcção

Após aplicação, verificar:

1. [ ] Páginas carregam sem erro
2. [ ] i18n funciona nos 3 idiomas
3. [ ] Banner gabi-test visível e legível
4. [ ] Nenhum claim "guarantee" permanece fora de contexto de disclaimer
5. [ ] Nenhum claim "certified" permanece sem processo formal

---

## Estado

**Proposta:** PREPARADA
**Execução:** AGUARDA DECISÃO I9
**Nenhuma alteração executada.**

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
