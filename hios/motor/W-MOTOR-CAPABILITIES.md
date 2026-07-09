# W-MOTOR-001 — Capabilities & Limitations
## IONOS AI Model Hub Integration

**Status:** OPERATIONAL
**Created:** 2026-07-09
**Liga IA+H:** Human Dragon (I9) · CCode (Opus 4.5)
**Receipt:** Pending first production seal

---

## TL;DR — Quick Reference

```
+------------------------------------------------------------------+
|  W-MOTOR-001 IONOS/FLUX — O QUE PODE E O QUE NÃO PODE            |
+------------------------------------------------------------------+
|                                                                  |
|  ✅ PODE:                        ❌ NÃO PODE:                    |
|  • Backgrounds/cenários          • Manter identidade facial      |
|  • Props e objectos              • Gerar vídeo nativo            |
|  • Storyboards rápidos           • Continuidade entre frames     |
|  • Personagem NOVO (1ª vez)      • Replicar âncora existente     |
|  • Testes de composição          • Image-to-image                |
|  • Conceptualização              • Face reference                |
|                                                                  |
+------------------------------------------------------------------+
|  REGRA DE OURO:                                                  |
|  "IONOS cria. Runway/OpenArt mantém."                            |
+------------------------------------------------------------------+
```

---

## 1. Provider Actual

| Campo | Valor |
|-------|-------|
| Provider | IONOS AI Model Hub |
| Endpoint | `openai.inference.de-txl.ionos.com` |
| Modelos Imagem | `FLUX.1-schnell`, `FLUX.2-klein-4B` |
| Modelos Vídeo | ❌ NENHUM |
| Autenticação | JWT (expira ~1h) |
| Localização | Alemanha (DE-TXL) |
| Compliance | GDPR, dados não usados para treino |

---

## 2. Capacidades Confirmadas

### 2.1 Geração de Imagem ✅

```bash
python3 scripts/w_hios_motor.py create-image \
  --prompt "..." \
  --size "1024x1024" \
  --provider ionos
```

**Tamanhos válidos FLUX.1-schnell:**
- `1024x1024` (quadrado)
- `1024x768` / `768x1024` (4:3)
- `1280x720` / `720x1280` (16:9) — verificar disponibilidade

### 2.2 Modelos LLM Disponíveis ✅

| Modelo | Uso |
|--------|-----|
| Meta Llama 3.1/3.3 (8B-405B) | Texto, scripts, diálogos |
| Mistral Nemo/Small | Texto rápido |
| Qwen3 Coder | Código |
| GPT-OSS-120B | Texto avançado |

### 2.3 Embeddings & Vision ✅

| Modelo | Uso |
|--------|-----|
| BAAI/bge-m3 | Embeddings multilingue |
| Qwen3-VL | Vision-Language |
| LightOnOCR | OCR de documentos |

---

## 3. Limitações Críticas

### 3.1 Sem Consistência Temporal ❌

**Problema demonstrado (2026-07-09):**
Mesmo prompt executado 3 vezes gera 3 pessoas completamente diferentes.

```
Frame 1: Mulher A (rosto X, cabelo Y)
Frame 2: Mulher B (rosto diferente)
Frame 3: Mulher C (outra pessoa)
```

**Implicação:** Impossível criar vídeo por concatenação de frames.

### 3.2 Sem Image-to-Image ❌

FLUX via IONOS é text-to-image puro. Não aceita:
- Imagem de referência
- Face embedding
- ControlNet
- IP-Adapter

### 3.3 Sem Vídeo Nativo ❌

IONOS AI Model Hub não oferece modelos de vídeo (Runway, Sora, Kling, etc.).

---

## 4. Arquitectura Multi-Provider Recomendada

```
┌─────────────────────────────────────────────────────────────────┐
│                    W-HIOS Production Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRÉ-PRODUÇÃO (IONOS/FLUX)                                      │
│  ├── Conceptualização de personagens novos                      │
│  ├── Geração de backgrounds/cenários                            │
│  ├── Props e elementos de cena                                  │
│  ├── Storyboards visuais                                        │
│  └── Testes de composição e iluminação                          │
│                                                                 │
│  PRODUÇÃO (Runway Gen-4 / OpenArt)                              │
│  ├── Vídeo com referência de âncora                             │
│  ├── Continuidade facial (face swap)                            │
│  ├── Image-to-video com consistência                            │
│  └── Movimento com identidade preservada                        │
│                                                                 │
│  PÓS-PRODUÇÃO (FFmpeg / W-VD-CUT)                               │
│  ├── Composição de takes                                        │
│  ├── Colour grading                                             │
│  └── Forensic sealing                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Quando Usar Cada Provider

| Tarefa | Provider | Razão |
|--------|----------|-------|
| Criar personagem NOVO | IONOS/FLUX | Rápido, barato, primeira iteração |
| Gerar background | IONOS/FLUX | Não precisa de continuidade facial |
| Criar âncora final | Selecção manual | Humano escolhe melhor geração |
| Vídeo de personagem | Runway Gen-4 | Suporta image reference |
| Face swap | OpenArt | Mantém âncora em vídeo existente |
| Props/objectos | IONOS/FLUX | Sem faces |
| Storyboard | IONOS/FLUX | Visualização rápida |

---

## 6. Fluxo de Criação de Personagem

```
1. CONCEPTUALIZAÇÃO (IONOS)
   └── Gerar 5-10 variações do prompt

2. SELECÇÃO HUMANA (I9)
   └── Human Dragon escolhe melhor imagem

3. PROMOÇÃO A ÂNCORA
   └── Imagem vira gabi.santos.anchor.v1.png
   └── Embedding extraído para SPINE-CAST

4. PRODUÇÃO (Runway/OpenArt)
   └── Todos os vídeos usam a âncora como referência
   └── Consistência garantida por face reference
```

---

## 7. Custos e Limites

| Item | IONOS | Runway | OpenArt |
|------|-------|--------|---------|
| Modelo | Token-based | Credit-based | Credit-based |
| Imagem 1024x1024 | ~$0.01-0.02 | N/A | Varies |
| Vídeo 5s | N/A | ~$0.50 | Varies |
| Limite diário | Billing-based | Credit-based | Varies |

---

## 8. Configuração Actual

```bash
# .env (valores sensíveis omitidos)
WHIOS_IONOS_IMAGE_ENDPOINT=https://openai.inference.de-txl.ionos.com/v1/images/generations
WHIOS_IONOS_API_TOKEN=eyJ...  # JWT, expira ~1h
WHIOS_MOTOR_WORKSPACE=/opt/windi/hios/motor/workspace
```

**NOTA:** O JWT expira. Renovar em:
IONOS DCD → AI Model Hub → [Modelo] → Generate Code → Copiar novo token

---

## 9. Comandos Úteis

```bash
# Verificar estado do motor
python3 scripts/w_hios_motor.py doctor

# Criar job de imagem
python3 scripts/w_hios_motor.py create-image --prompt "..." --provider ionos

# Executar próximo job
python3 scripts/w_hios_motor.py run-next --provider ionos

# Listar todos os jobs
python3 scripts/w_hios_motor.py list
```

---

## 10. Invariantes

| ID | Descrição | Status |
|----|-----------|--------|
| I9 | Human approval antes de promoção a âncora | ACTIVE |
| I11 | Proveniência forense em cada geração | ACTIVE |
| I14 | Falha explícita se provider indisponível | ACTIVE |
| I19 | Manifest gerado atomicamente com output | ACTIVE |

---

*Liga IA+H · WINDI Publishing House · 2026-07-09*
*"IONOS cria. Runway/OpenArt mantém. WINDI garante."*
