# §297 — Lei da Proveniência Inseparável

**Status:** SEALED · **Invariant:** I19 · **Date:** 2026-06-01
**Invariants Connected:** I11 (Permanência), I14 (Falha Explícita), I9 (Aprovação Humana)

> **"A pele cresce com a carne; não se cose depois."**
> — Guardian · 01 Jun 2026

---

## Ratio Decidendi

Em 01 Jun 2026, durante a preparação do Multi-Anchor Test para "O Peso do Eco",
foi descoberto que os anchor videos (`helena_anchor_scene_v3.mp4` e
`marcus_anchor_scene_v2.mp4`) perderam a sua assinatura de gerador durante
processamento FFmpeg. A metadata `encoder: Google` foi substituída por
`encoder: Lavf58.29.100`, tornando a proveniência de elo não-verificável.

O CCode caçou evidência por ordem do Guardian:
- Logs de geração: não encontrados
- Receipts no Ledger: não encontrados para estes artefactos
- Metadados ffprobe: assinatura apagada pelo FFmpeg
- Bash history: vazio para comandos relevantes

**Veredicto:** Proveniência genuinamente não-verificável.

**Causa raiz:** A operação de geração e o registo dessa operação eram dois
actos separados. Sob pressão operacional, o segundo foi omitido. O FFmpeg
correu entre a geração e um possível registo, destruindo a assinatura.

**Solução estrutural:** Tornar geração e registo **atómicos** — um único acto
indivisível. A proveniência nasce com o artefacto, não é cosida depois.

---

## Texto da Lei

> **Lei da Proveniência Inseparável (I19):** Toda operação geradora ou
> transformadora numa cadeia forense escreve o seu rasto no mesmo acto,
> antes de qualquer processamento posterior. Um artefacto cuja cadeia de
> elo não é reconstruível a partir do disco é tratado como tendo
> proveniência desconhecida, qualquer que seja o seu score interno.

---

## Três Camadas de Implementação

### Camada 1 — Atomicidade de Geração

O rasto nasce no mesmo acto da geração, não depois. Nenhuma chamada ao
gerador produz um ficheiro "nu". O output é sempre um par:

```
(artefacto.mp4, artefacto.provenance.json)
```

Se o sidecar falha, a geração não conta. Atómico.

**Implementação:** `provenance.py` com `ProvenanceWriter` context manager.

### Camada 2 — Hash Antes de Transformação

O hash ancora antes do FFmpeg tocar. A regra: selar o hash do output
bruto ANTES de qualquer trim, recode ou crop. Cada transformação
posterior regista-se como um elo na cadeia:

```
bruto_veo.mp4 (hash A) → trim_ffmpeg → trimmed.mp4 (hash B)
```

O sidecar preserva toda a cadeia. A assinatura do gerador nunca se
perde porque vive na cadeia, não no metadado do ficheiro.

**Implementação:** `TransformationRecorder.record()` em `provenance.py`.

### Camada 3 — Gate de Proveniência Obrigatório

A proveniência vira pré-condição de uso, não rótulo opcional. Um anchor
sem cadeia de elo verificável não pode entrar numa medição cross-elo.
Não por convenção — por bloqueio.

**Dois gates separados, ambos obrigatórios:**
1. Gate Forense (score ≥ 0.75) — estabilidade interna
2. Gate de Proveniência — coerência de elo verificável

**Implementação:** `check_anchor_provenance()` em `spine.py`.

---

## Schema de Proveniência (v1.0.0)

```json
{
  "schema_version": "1.0.0",
  "provenance_id": "WINDI-PROV-YYYYMMDDHHMMSS-HASH8",
  "generator": "veo|runway|sora|...",
  "model": "veo-3.1-generate-preview",
  "elo": {
    "number": 2,
    "type": "generated_video",
    "parent_provenance_id": null
  },
  "prompt_hash": "sha256:...",
  "output_hash_raw": "sha256:...",
  "created_at": "ISO8601",
  "transformations": [
    {
      "tool": "ffmpeg",
      "operation": "trim",
      "input_hash": "sha256:...",
      "output_hash": "sha256:...",
      "timestamp": "ISO8601"
    }
  ]
}
```

---

## Corolários

### C1 — Score 5/5 ≠ Proveniência Válida

Um anchor pode ter score forense 5/5 (estabilidade interna excelente) e
ainda assim ser inválido para medição cross-elo se a proveniência não
for verificável. São duas propriedades distintas.

### C2 — Proveniência Desconhecida = Anchor Inválido

Anchor sem proveniência de elo documentada é tratado como inválido para
medição cross-elo, independentemente do seu score interno.

### C3 — Reextração Como Único Caminho

Se a proveniência foi perdida, o único caminho válido é reextrair o
anchor do elo onde a medição vai ocorrer. Não há atalhos.

### C4 — Não-Retroactividade

Esta lei aplica-se a artefactos gerados a partir de 01 Jun 2026. Artefactos
anteriores sem proveniência podem ser usados com `ENFORCE_PROVENANCE_GATE=False`,
mas devem ser migrados quando regenerados.

---

## Ficheiros

| Ficheiro | Função |
|----------|--------|
| `/opt/windi/hios/visual/producer/provenance.py` | Módulo de proveniência |
| `/opt/windi/hios/visual/producer/schemas/provenance-v1.schema.json` | JSON Schema |
| `/opt/windi/hios/visual/producer/veo_producer.py` | Veo com proveniência atómica |
| `/opt/windi/hios/visual/producer/hybrid-pipeline/b4/spine.py` | Gate de proveniência |

---

## Genealogia Constitucional

Esta lei estende I11 (Permanência de Evidência Criptográfica) ao momento
da criação: não basta que a evidência seja permanente depois de criada —
a própria criação deve ser evidenciada no mesmo acto.

Liga também a I14 (Falha Explícita): um artefacto sem proveniência não
mascara a ausência com um score interno alto. A falha é explícita.

---

## Aprovação

**Human Dragon:** Opção B aprovada em 01 Jun 2026 — invariante constitucional
para toda a forja WINDI-HIOS, não apenas CASE-001.

**Trigger:** "Opção B" — decisão do único decisor humano.

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*"A pele cresce com a carne; não se cose depois."*
