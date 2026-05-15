# W-SITES Module Incubator

> Lugar onde ideias de módulos plugáveis para W-SITES-001 nascem,
> amadurecem e — quando maduras — são promovidas a sprint próprio.

## Categoria

W-SITES-MODULES é a categoria de capacidades activáveis pelo USER dentro
do seu próprio site W-SITES. Análogo às SKILLs do Claude: artefactos
soberanos, instaláveis, registáveis no DID do dono.

## Princípios constitucionais herdados

- Política de Dados Canónica: módulo enriquece capacidade do dono, não extrai dados
- Receipt Symmetry: cada activação gera receipt no Ledger
- DID-bound: dados do módulo vivem sob DID do utilizador
- Tier-aware: módulo declara P / M / G

## Arquitectura — Primitiva Raiz

> **w-journal é a primitiva da qual quase todos os outros módulos derivam.**

| Módulo | É um caderno verificável de… |
|--------|------------------------------|
| w-journal | …registo pessoal genérico (a primitiva nua) |
| w-travel | …encontro com lugar (registo + geo + tempo) |
| w-law-notes | …observações jurídicas pessoais (registo + contexto legal) |
| w-med-diary | …sintomas/medicação/consultas (registo + dados clínicos) |
| w-academic | …processo de investigação (registo + cadeia de evidência) |
| w-field-notes | …trabalho de campo (jornalismo, antropologia, arqueologia…) |

Cada módulo herda a Perceive de w-journal + adiciona a sua especialização.

## Maturidade (estados)

- 💭 **Idea** — anotação livre, ainda não estruturada
- 📐 **Spec** — Perceive + Define preenchidos
- 🏗️ **Blueprint** — Build rascunhado, integrações identificadas
- 🚀 **Sprint** — promovido a sprint formal (sai do incubador)

## Promoção a sprint

Um módulo sai daqui quando:
1. Os quatro estágios (Perceive → Define → Build → Scale) estão preenchidos
2. Receipt-shape definido
3. Tier decidido
4. Human Dragon assina a promoção (decisão dele, não automática)

## Índice actual

| Módulo | Maturidade | Última edição | Nota |
|--------|------------|---------------|------|
| w-journal | 📐 Spec | 2026-05-10 | **PRIMITIVA RAIZ** |
| w-travel | 📐 Spec | 2026-05-10 | Deriva de w-journal |

## Vinculação ao MANIFESTO

Cada módulo deve passar o teste do MANIFESTO §III:

> *"isto protege alguém de perder anos da sua vida em meia-verdade?"*

Se sim, está alinhado com a missão. Se não, é ornamento.
