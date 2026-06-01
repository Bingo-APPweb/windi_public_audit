# S20b Tribunal — Prova de Conceito Visual

**Status:** POC · NÃO FORENSE · Variáveis não isoladas
**Data:** 2026-06-01

## O que isto é

Primeira tentativa de coexistência Helena + Marcus numa cena de tribunal.
Visualmente aprovado: ambos personagens reconhecíveis, sem colapso de identidade.

## O que isto NÃO é

- Não é o teste multi-anchor canónico
- Não isola variáveis (distância, luz, ângulo diferentes)
- v1 não usou referência visual (Helena errada)
- v2 usou referência Helena mas pipeline ad-hoc (não veo_producer.py blindado)

## Uso permitido

- Referência visual para produção
- Prova de conceito de coexistência atmosférica
- Inspiração para diálogos/sequências

## Uso proibido

- Medição forense de bleed-over
- Comparação com baseline isolado (-0.0305)
- Selagem no Ledger como evidência de identidade

## Próximo passo

Banco de ensaio controlado:
- Fundo neutro cinza
- Mesma distância da câmara
- Mesma iluminação
- Movimento mínimo
- Pipeline veo_producer.py blindado com proveniência atómica
