# WINDI Pioneer · Sector Turismo
## Florianópolis · Brasil · Português

---

## O Problema que o WINDI resolve para você

Você vende experiências — passeios de escuna, trilhas, mergulho.
O seu cliente compra com base em fotos e avaliações.
Mas como ele sabe que aquela foto do mar é de hoje,
e não de uma manhã azul de dois anos atrás?

**Resultado actual:** 12–18% de cancelamentos por "informação não confiável".

**Com o WINDI:** Cada foto que você envia tem um selo forense com
data e hora irrefutáveis. O cliente clica no QR e vê: VERIFICADO.

---

## Passo 1 — Obter sua API Key (30 segundos)

```bash
./shared/get_api_key.sh "Turismo Floripa" SEED
```

Ou manualmente:

```bash
curl -X POST https://windi-domain.com/api-keys/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Turismo Floripa",
    "tier": "SEED",
    "description": "Pioneer Turismo Florianópolis"
  }'
```

Guarde o valor `api_key` retornado. Começa com `wnd_live_`.

---

## Passo 2 — Atomizar uma foto do passeio

```bash
python3 atomize_turismo.py foto_escuna.jpg
```

---

## O que o seu cliente vê

Ao abrir o link verify_url, o cliente vê:

```
┌─────────────────────────────────────┐
│  WINDI · VERIFICADO                 │
│                                     │
│  Operador: Turismo Floripa          │
│  Data:     15 Mar 2026 · 14:32 UTC  │
│  Schema:   TOURISM                  │
│  Hash:     e0e95e4a...              │
│                                     │
│  Este conteúdo é autêntico          │
│  e não foi alterado.                │
└─────────────────────────────────────┘
```

---

## Casos de uso imediatos

| Situação | O que atomizar | Valor para o cliente |
|----------|---------------|---------------------|
| Condições do mar hoje | Foto do deck às 7h | "Vejo o mar real, não o do Instagram" |
| Guia certificado | Foto do guia com ID | "Sei quem me acompanha" |
| Ticket de embarque | PDF da reserva | "Meu bilhete é irrefutável" |
| Avaliação pós-passeio | Foto com cliente | "Esta avaliação é real, não comprada" |

---

## Suporte

- Email: pioneer@windi-domain.com
- Sector: TURISMO_FLORIANOPOLIS
- Tier: SEED

*"AI processes. Human decides. WINDI guarantees."*
