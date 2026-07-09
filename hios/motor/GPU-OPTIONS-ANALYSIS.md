# W-MOTOR-001 — Análise de Opções GPU
## Para Geração de Imagem/Vídeo Soberana

**Data:** 2026-07-09
**Liga IA+H:** Human Dragon (I9) · CCode (Opus 4.5)
**Objectivo:** Escolher infra GPU para W-HIOS Production

---

## TL;DR — Recomendação Rápida

```
┌─────────────────────────────────────────────────────────────────┐
│  CENÁRIO                        │  RECOMENDAÇÃO                 │
├─────────────────────────────────┼───────────────────────────────┤
│  Produção ocasional (<10h/mês)  │  RunPod On-Demand             │
│  Produção regular (10-50h/mês)  │  RunPod + Spot Instances      │
│  Produção intensiva (>50h/mês)  │  Hetzner GEX44 Dedicado       │
│  Máxima soberania + volume      │  Hetzner GEX130 Dedicado      │
└─────────────────────────────────┴───────────────────────────────┘
```

---

## 1. OPÇÕES CLOUD ON-DEMAND (Pay-per-hour)

### 1.1 RunPod

| GPU | VRAM | Preço/hora | Ideal Para |
|-----|------|------------|------------|
| RTX 4090 | 24GB | ~$0.44 | FLUX básico |
| RTX A6000 | 48GB | ~$0.79 | FLUX 2K |
| A100 PCIe | 40GB | ~$1.64 | Batch generation |
| A100 SXM | 80GB | ~$1.89 | Video/FLUX.2 |
| L40 | 48GB | ~$0.86 | FLUX produção |
| H100 | 80GB | ~$2.39 | Máximo desempenho |

**Vantagens:**
- ✅ Sem compromisso mínimo
- ✅ Facturação por segundo
- ✅ Sem fees de ingress/egress
- ✅ Spot instances (60% desconto)
- ✅ Templates FLUX pré-configurados

**Desvantagens:**
- ❌ Disponibilidade variável
- ❌ Latência de startup (~30s)
- ❌ Dados não persistentes

**Custo Estimado WINDI:**
```
10 gerações FLUX/dia × 30 dias = 300 gerações/mês
~10 segundos/geração × 300 = 3000 segundos = 0.83 horas
RTX A6000: 0.83h × $0.79 = ~$0.66/mês

100 gerações/dia = ~$6.60/mês
1000 gerações/dia = ~$66/mês
```

**Links:**
- [RunPod Pricing](https://www.runpod.io/pricing)
- [RunPod FLUX Guide](https://www.runpod.io/articles/guides/deploying-flux-1-for-high-resolution-image-generation-with-gpu-infrastructure)

---

### 1.2 Lambda Labs

| GPU | VRAM | Preço/hora | Ideal Para |
|-----|------|------------|------------|
| A6000 | 48GB | $0.80 | FLUX produção |
| A100 PCIe | 40GB | $1.29 | Batch |
| A100 SXM | 80GB | $1.99-2.79 | Video |
| H100 PCIe | 80GB | $2.99 | Alto volume |
| H100 SXM (8x) | 80GB×8 | $3.99/GPU | Clusters |

**Vantagens:**
- ✅ Sem fees de egress
- ✅ Reserva 1-3 anos (desconto)
- ✅ 1-Click Clusters
- ✅ Boa reputação ML/AI

**Desvantagens:**
- ❌ Disponibilidade limitada
- ❌ H100 SXM só em bundles de 8

**Links:**
- [Lambda Pricing](https://lambda.ai/pricing)

---

## 2. SERVIDOR DEDICADO (Monthly)

### 2.1 Hetzner GPU Servers

| Modelo | GPU | VRAM | CPU | RAM | Preço/mês |
|--------|-----|------|-----|-----|-----------|
| **GEX44** | RTX 4000 SFF | 20GB | i5-13500 | 64GB | **€184** |
| **GEX130** | RTX 6000 Ada | 48GB | Xeon Gold | 128GB | **€838** |
| **GEX131** | RTX PRO 6000 Blackwell | 96GB | Xeon | 256GB | ~€1200+ |

**Hetzner GEX44 (RECOMENDADO para WINDI):**
```
GPU:     NVIDIA RTX 4000 SFF Ada (20GB GDDR6 ECC)
CPU:     Intel Core i5-13500 (6P + 8E cores)
RAM:     64GB DDR4
Storage: 2× 1.92TB NVMe Gen3
Rede:    1 Gbit/s
Setup:   €79 (único)
Mensal:  €184

Total 1º mês: €263
Total/ano:    €2287 (~€191/mês)
```

**Vantagens:**
- ✅ **Soberania total** — servidor é teu
- ✅ Disponibilidade 24/7
- ✅ Dados persistentes
- ✅ Localização Alemanha (GDPR)
- ✅ Sem limites de uso
- ✅ IP fixo para integração WINDI

**Desvantagens:**
- ❌ Custo fixo mesmo sem usar
- ❌ RTX 4000 SFF (20GB) limitado para modelos grandes
- ❌ Manutenção é tua responsabilidade

**Links:**
- [Hetzner GEX44](https://www.hetzner.com/dedicated-rootserver/gex44/)
- [Hetzner GEX130](https://www.hetzner.com/dedicated-rootserver/gex130/)

---

## 3. COMPARAÇÃO DE CUSTOS

### Cenário A: Produção Leve (100 gerações/mês)

| Opção | Custo/mês | Custo/geração |
|-------|-----------|---------------|
| IONOS API | ~€2-5 | ~€0.02-0.05 |
| RunPod A6000 | ~€1 | ~€0.01 |
| Hetzner GEX44 | €184 | €1.84 |

**Veredicto:** IONOS ou RunPod

---

### Cenário B: Produção Média (1000 gerações/mês)

| Opção | Custo/mês | Custo/geração |
|-------|-----------|---------------|
| IONOS API | ~€20-50 | ~€0.02-0.05 |
| RunPod A6000 | ~€7 | ~€0.007 |
| Hetzner GEX44 | €184 | €0.18 |

**Veredicto:** RunPod (melhor custo/geração)

---

### Cenário C: Produção Intensiva (10000 gerações/mês)

| Opção | Custo/mês | Custo/geração |
|-------|-----------|---------------|
| IONOS API | ~€200-500 | ~€0.02-0.05 |
| RunPod A6000 | ~€66 | ~€0.0066 |
| Hetzner GEX44 | €184 | €0.018 |

**Veredicto:** RunPod ainda mais barato, mas Hetzner oferece **soberania**

---

### Cenário D: Produção 24/7 + Vídeo

| Opção | Custo/mês | Notas |
|-------|-----------|-------|
| RunPod H100 (8h/dia) | ~€574 | 8h × 30d × $2.39 |
| Hetzner GEX130 | €838 | 24/7, 48GB VRAM |

**Veredicto:** Hetzner para uso intensivo contínuo

---

## 4. ARQUITECTURA PROPOSTA

### Fase 1: Híbrido Conservador (Agora)
```
STRATO (coordena)
    ├── IONOS API (imagens simples) ← JÁ LIVE
    └── RunPod On-Demand (quando precisar)
```
**Custo:** ~€5-50/mês (pay-as-you-go)

### Fase 2: RunPod Optimizado (Volume médio)
```
STRATO (coordena)
    ├── IONOS API (fallback)
    └── RunPod Serverless (FLUX endpoint) ← IMPLEMENTAR
```
**Custo:** ~€20-100/mês

### Fase 3: Soberania Parcial (Volume alto)
```
STRATO (coordena)
    ├── Hetzner GEX44 (FLUX self-hosted) ← GPU DEDICADA
    ├── RunPod (overflow/video)
    └── IONOS (fallback)
```
**Custo:** €184/mês + overflow

### Fase 4: Soberania Total (Produção cinema)
```
STRATO (coordena)
    ├── Hetzner GEX130 (FLUX + Video) ← GPU PRINCIPAL
    └── RunPod (burst capacity)
```
**Custo:** €838/mês + burst

---

## 5. REQUISITOS TÉCNICOS POR MODELO

| Modelo | VRAM Mínimo | VRAM Recomendado | Tempo/imagem |
|--------|-------------|------------------|--------------|
| FLUX.1-schnell | 12GB | 16GB+ | ~5-10s |
| FLUX.1-dev | 16GB | 24GB+ | ~15-30s |
| FLUX.2-klein | 12GB | 16GB+ | ~5s |
| Stable Diffusion XL | 8GB | 12GB+ | ~3-5s |
| CogVideoX (vídeo) | 24GB | 48GB+ | ~60-120s |

**Hetzner GEX44 (20GB):** ✅ FLUX.1, SDXL ❌ CogVideoX
**Hetzner GEX130 (48GB):** ✅ Tudo incluindo vídeo

---

## 6. DECISÃO — PERGUNTAS CHAVE

```
1. Quantas gerações/mês prevês?
   [ ] <100     → IONOS/RunPod
   [ ] 100-1000 → RunPod Spot
   [ ] >1000    → Hetzner GEX44
   [ ] >10000   → Hetzner GEX130

2. Precisas de vídeo (CogVideoX, etc)?
   [ ] Não → GEX44 suficiente
   [ ] Sim → GEX130 necessário

3. Soberania é prioridade?
   [ ] Não → RunPod (mais barato)
   [ ] Sim → Hetzner (servidor teu)

4. Orçamento mensal GPU?
   [ ] <€50   → RunPod On-Demand
   [ ] €50-200 → Hetzner GEX44
   [ ] >€500  → Hetzner GEX130
```

---

## 7. PRÓXIMOS PASSOS CONCRETOS

### Opção A: Começar com RunPod
```bash
# 1. Criar conta RunPod
# 2. Adicionar ao .env
WHIOS_RUNPOD_API_KEY=...

# 3. Implementar RunPodProvider
# 4. Testar com FLUX endpoint
```
**Tempo:** ~2-4 horas
**Custo inicial:** $0 (pay-as-you-go)

### Opção B: Encomendar Hetzner GEX44
```bash
# 1. Encomendar em hetzner.com/dedicated-rootserver/gex44/
# 2. Aguardar setup (~24-48h)
# 3. Configurar CUDA + PyTorch
# 4. Instalar diffusers + FLUX
# 5. Integrar com W-MOTOR
```
**Tempo:** ~1-2 dias
**Custo inicial:** €263 (setup + 1º mês)

---

## 8. FONTES

- [Hetzner GPU Servers](https://www.hetzner.com/dedicated-rootserver/matrix-gpu/)
- [Hetzner GEX44](https://www.hetzner.com/dedicated-rootserver/gex44/)
- [RunPod Pricing](https://www.runpod.io/pricing)
- [RunPod FLUX Guide](https://www.runpod.io/articles/guides/deploying-flux-1-for-high-resolution-image-generation-with-gpu-infrastructure)
- [Lambda Labs Pricing](https://lambda.ai/pricing)
- [GPU Price Comparison 2026](https://altstreet.investments/tools/gpu/gpu-price-comparison)

---

*Liga IA+H · WINDI Publishing House · 2026-07-09*
*"O motor coordena em casa. O músculo gráfico pode ser alugado ou comprado."*
