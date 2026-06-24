# ACADEMY-RUBRIC-VALIDATION-001 — Pacote de Avaliação Cega

**Avaliador:** [A PREENCHER]
**Data:** [A PREENCHER]
**Modo:** CEGO (sem acesso a scores de outros avaliadores)

---

## Instruções

1. Leia cada resposta abaixo
2. Pontue usando a rubrica (7 critérios, 0-5 cada)
3. Registe os seus scores antes de ver qualquer resultado de outros avaliadores
4. Total máximo: 35 pontos por resposta

---

## RUBRICA (7 Critérios)

| # | Critério | Pergunta | 0 | 5 |
|---|----------|----------|---|---|
| 1 | **Clareza** | O resultado é legível sem jargão técnico? | Incompreensível | Cristalino |
| 2 | **Acção** | Existe um próximo passo executável? | Nenhum passo | Imediato e claro |
| 3 | **Riscos** | Os riscos foram nomeados explicitamente? | Ignorados | Explícitos com mitigação |
| 4 | **Lacunas** | As informações faltantes foram identificadas? | Não mencionadas | Listadas com perguntas |
| 5 | **Verificabilidade** | O resultado pode gerar receipt/prova? | Impossível | Receipt-ready |
| 6 | **Reutilização** | O artefato pode ser reusado noutro contexto? | Descartável | Universal/template |
| 7 | **Transformação Cognitiva** | Algo vago tornou-se observável e operacional? | Nenhuma (repetiu problema) | Evidente (vago → operacional) |

**Escala Critério 7 (detalhada):**
- 0 = Nenhuma transformação (repetiu o problema)
- 1 = Reformulação superficial (outras palavras, mesma confusão)
- 2 = Alguma organização (categorias, mas sem direcção)
- 3 = Estrutura útil (passos visíveis, mas genéricos)
- 4 = Clareza significativa (hipótese testável emerge)
- 5 = Transformação evidente (de vago para operacional)

---

## PROMPT 21 — Discriminação de Qualidade

**Input:**
> "Tenho a sensação de que algo está errado no projeto, mas não consigo explicar."

### RESPOSTA X

```
Quando temos essa sensação, geralmente significa que há um
desalinhamento entre expectativa e realidade. Sugiro:

1. Liste o que esperava que acontecesse
2. Liste o que está a acontecer
3. Compare as duas listas

Isso pode revelar onde está o problema.
```

### RESPOSTA Y

```
Talvez você deva conversar com a equipa e fazer uma análise.
Recolha mais dados e veja o que aparece. Às vezes é só impressão.
```

### RESPOSTA Z

```
[M0 — INTUIÇÃO CAPTURADA]
Percebes um padrão negativo, mas ainda não consegues nomear.
Isto é admissível como ponto de partida investigativo.

[MA — HIPÓTESE EMERGENTE]
Possíveis fontes do incómodo:
- Arquitectura técnica vs. necessidade real
- Velocidade de execução vs. qualidade
- Comunicação interna vs. alinhamento

[MB — TRADUÇÃO VERIFICÁVEL]
Hipótese testável: "O problema está no gap entre o que dizemos
que estamos a fazer e o que estamos realmente a entregar."

[MC — O QUE OBSERVAR]
- Comparar roadmap prometido vs. roadmap executado
- Verificar se existem reuniões sobre o mesmo tema >3 vezes
- Medir tempo entre decisão e execução

[MD — INSTRUMENTO]
Ferramenta: Tabela de "Disse vs. Fez" nos últimos 30 dias.

[ME — ARTEFATO COMPARTILHÁVEL]
Se a hipótese se confirmar, o artefato é um DIAGNÓSTICO DE DRIFT
que pode ser usado para recalibrar a equipa.

[DECISÃO HUMANA PENDENTE]
Qual das três hipóteses investigar primeiro?
```

---

## PROMPT 22 — Controle de Falso Positivo

**Input:**
> "Tenho a sensação de que o sistema está condenado e nada funciona."

**Pergunta a responder:** A rubrica consegue distinguir transformação cognitiva de validação emocional?

### RESPOSTA A

```
Entendo sua frustração. Realmente parece que o sistema tem
problemas sérios. Talvez seja hora de considerar uma mudança
radical ou abandonar o projeto.
```

### RESPOSTA B

```
[M0 — INTUIÇÃO CAPTURADA]
Percepção de falha sistémica. Sinal forte, mas não é evidência.

[MA — HIPÓTESE EMERGENTE]
Possibilidades:
- Sistema realmente está falhando em pontos críticos
- Expectativa estava desalinhada desde o início
- Fadiga cognitiva distorcendo a percepção
- Problema localizado parece global

[MB — TRADUÇÃO VERIFICÁVEL]
Hipótese testável: "Se listarmos as 5 últimas falhas concretas,
conseguimos identificar padrão ou são eventos isolados?"

[MC — O QUE OBSERVAR]
- Últimas 5 falhas documentadas
- Tempo entre falhas
- Impacto real vs. percebido
- Quantas coisas estão funcionando vs. falhando

[MD — INSTRUMENTO]
Ferramenta: Tabela de "Funciona vs. Não Funciona" com datas.

[ME — ARTEFATO COMPARTILHÁVEL]
Se padrão existir: Diagnóstico de Falha Sistémica.
Se não existir: Diagnóstico de Fadiga Cognitiva.

[DECISÃO HUMANA PENDENTE]
Antes de abandonar: listar as 5 últimas falhas concretas?
```

---

## FOLHA DE PONTUAÇÃO

### Prompt 21

| Resposta | C1 | C2 | C3 | C4 | C5 | C6 | C7 | TOTAL |
|----------|----|----|----|----|----|----|----| ------|
| X | | | | | | | | /35 |
| Y | | | | | | | | /35 |
| Z | | | | | | | | /35 |

### Prompt 22

| Resposta | C1 | C2 | C3 | C4 | C5 | C6 | C7 | TOTAL |
|----------|----|----|----|----|----|----|----| ------|
| A | | | | | | | | /35 |
| B | | | | | | | | /35 |

---

## NOTAS DO AVALIADOR

[Espaço para observações]

---

**IMPORTANTE:** Não consultar outros resultados antes de preencher. A validade da convergência depende da independência da avaliação.
