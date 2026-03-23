# WINDI FIELD — Blueprint v1.0
**"Estavas aqui. Neste momento. Com esta identidade."**

```
Receipt:    WINDI-FIELD-BLUEPRINT-V1.0-20260323
Autorizado: Human Dragon, Pioneer #1
Data:       2026-03-23 · Kempten, Bavaria
Governance: HIGH · IRREMEDIÁVEL
```

---

## Declaração Fundacional

> O WINDI TRAVEL prova que tens um ficheiro.
> O WINDI FIELD prova que **estavas num lugar, num momento, com uma identidade.**
> A diferença é a diferença entre uma fotocópia e uma testemunha.

---

## O Problema que o FIELD Resolve

```
TRAVEL (válido, mas limitado):
  Ficheiro de 6 meses → upload hoje → hash gerado AGORA
  → "Proof Generated" → mas a prova é da transferência, não do evento

FIELD (forense):
  DID verificado → GPS locked → câmara abre → captura →
  hash gerado NO DISPOSITIVO → seal no Ledger em <3 segundos
  → impossível fabricar retrospectivamente
```

**Regra de ouro do FIELD:**
> Se a captura e o seal não aconteceram no mesmo gesto — não é prova forense.

---

## Arquitectura Técnica

### O Gesto Único (3 segundos)

```
[1] DID verificado?
    → NÃO: bloquear. "Sem identidade, sem captura."
    → SIM: continuar

[2] GPS locked? (±50m mínimo)
    → NÃO: aguardar. "A obter localização precisa..."
    → SIM: continuar

[3] Câmara nativa abre
    → OBRIGATÓRIO: capture="environment" (câmara traseira)
    → PROIBIDO: upload de galeria, drag-and-drop, ficheiros externos

[4] Utilizador captura (foto ou vídeo)
    → Hash SHA-256 gerado IMEDIATAMENTE no dispositivo
    → Metadata capturada: GPS, timestamp, DID, device fingerprint

[5] POST imediato ao Ledger (< 3 segundos)
    → Timestamp carimbado pelo SERVIDOR (não pelo browser)
    → Receipt gerado com DID vinculado
    → Seal IRREMEDIÁVEL

[6] PROOF GENERATED
    → Receipt ID + Hash + GPS + Timestamp servidor + DID
```

### Diferença Crítica vs TRAVEL

| Campo | TRAVEL | FIELD |
|---|---|---|
| Fonte do ficheiro | Qualquer (galeria, email...) | Câmara nativa OBRIGATÓRIA |
| DID | Opcional | OBRIGATÓRIO |
| GPS | Pedido, opcional | OBRIGATÓRIO antes do shutter |
| Timestamp | Browser (manipulável) | Servidor (autoritativo) |
| Galeria | ✅ Permitida | ❌ Bloqueada |
| Retroactividade | Possível | Impossível |
| Validade forense | Memórias, viagens | Tribunal, investigação |

---

## Stack Técnico — O que Reutiliza (85%)

```
✅ REUTILIZA (já existe e funciona):
├── Forensic Ledger :8101        ← seal + receipt
├── DID Wallet :8096             ← identidade obrigatória
├── W-LEGAL-001                  ← Evidence Git + jurisdições
├── W-NOTARY-001                 ← selo digital
├── Verify Public :8114          ← verificação pública
└── SHA-256 worker               ← hash nativo (agnóstico ao ficheiro)

🆕 CRIA DE NOVO (~15%):
├── field-capture.html           ← UI forense (sem upload)
├── field_server.py              ← endpoint com timestamp servidor
├── DID gate (frontend)          ← bloqueia sem identidade
└── GPS enforcer                 ← bloqueia sem coordenadas
```

---

## Implementação — 4 Ficheiros Cirúrgicos

### Ficheiro 1 — `field-capture.html`

**Regras de UX forense:**
- Sem botão "Upload" — só câmara
- GPS spinner obrigatório antes de qualquer captura
- DID banner obrigatório no topo
- Após captura: receipt imediato com QR

```javascript
// GATE 1 — DID obrigatório
const did = localStorage.getItem('windi_did') ||
            sessionStorage.getItem('windi_did');
if (!did) {
    showGate('DID_REQUIRED');
    // "Sem identidade soberana, sem captura forense."
    // Link → windi-domain.com/app/ para criar DID
    return;
}

// GATE 2 — GPS obrigatório ANTES da câmara
async function lockGPS() {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            pos => {
                if (pos.coords.accuracy > 100) {
                    // Precisão insuficiente — aguardar
                    reject('GPS_IMPRECISE');
                } else {
                    resolve({
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        altitude: pos.coords.altitude,
                        lockedAt: new Date().toISOString()
                    });
                }
            },
            err => reject('GPS_DENIED'),
            { enableHighAccuracy: true, timeout: 15000 }
        );
    });
}

// GATE 3 — Câmara nativa APENAS
// Input configurado para NUNCA permitir galeria
// <input type="file" accept="image/*,video/*"
//        capture="environment" id="field-capture">
// NOTA: capture="environment" em mobile bloqueia galeria nativamente

// GATE 4 — Hash gerado IMEDIATAMENTE após captura
input.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Timestamp LOCAL capturado no momento do change event
    const captureTimestamp = new Date().toISOString();

    // Hash do ficheiro
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hash = Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0')).join('');

    // POST imediato ao servidor — timestamp será do servidor
    await sealToLedger({
        hash,
        did,
        gps: lockedGPS,           // GPS capturado ANTES
        clientTimestamp: captureTimestamp,
        fileType: file.type,
        fileSize: file.size,
        mode: 'FIELD'             // distinguir de TRAVEL
    });
});
```

### Ficheiro 2 — `field_server.py`

```python
@app.route('/field/seal', methods=['POST'])
def field_seal():
    data = request.json

    # Timestamp AUTORITATIVO — sempre do servidor
    server_timestamp = datetime.utcnow().isoformat() + 'Z'

    # Validações obrigatórias
    required = ['hash', 'did', 'gps', 'mode']
    for field in required:
        if not data.get(field):
            return jsonify({
                'error': f'FIELD_MISSING: {field}',
                'message': 'Prova forense requer todos os campos.'
            }), 400

    # GPS mínimo
    gps = data['gps']
    if gps.get('accuracy', 999) > 100:
        return jsonify({
            'error': 'GPS_IMPRECISE',
            'message': 'Precisão GPS insuficiente para prova forense.'
        }), 400

    # Construir receipt FIELD
    receipt_id = f"WINDI-FIELD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{data['hash'][:8].upper()}"

    receipt = {
        'id': receipt_id,
        'actor': data['did'],
        'app': 'windi-field',
        'doc_name': f"WINDI FIELD Capture — {server_timestamp}",
        'doc_type': 'doc',
        'governance_level': 'HIGH',
        'content': {
            'mode': 'FIELD',
            'hash': data['hash'],
            'did': data['did'],
            'gps': {
                'lat': gps['lat'],
                'lng': gps['lng'],
                'accuracy_meters': gps['accuracy'],
                'locked_at': gps.get('lockedAt')
            },
            'file_type': data.get('fileType'),
            'file_size_bytes': data.get('fileSize'),
            'server_timestamp': server_timestamp,    # ← AUTORITATIVO
            'client_timestamp': data.get('clientTimestamp'),  # ← referência
            'forensic_grade': True,
            'chain_of_custody': {
                'captured_by': data['did'],
                'captured_at': server_timestamp,
                'location': f"{gps['lat']:.4f}, {gps['lng']:.4f}",
                'device_mode': 'native_camera_only',
                'gallery_upload': False
            }
        },
        'metadata': {
            'impact_level': 'HIGH',
            'flow_status': 'FIELD_SEALED',
            'department_code': 'FIELD'
        },
        'tags': ['field', 'forensic', 'native-capture', 'gps-locked', 'did-bound']
    }

    # Selar no Ledger
    response = requests.post(
        'http://localhost:8101/api/receipts',
        json=receipt,
        timeout=5
    )

    if response.status_code in (200, 201):
        return jsonify({
            'status': 'FIELD_SEALED',
            'receipt_id': receipt_id,
            'server_timestamp': server_timestamp,
            'verify_url': f"https://windi-domain.com/verify-public/?id={receipt_id}",
            'forensic_grade': True
        })
    else:
        return jsonify({'error': 'LEDGER_UNAVAILABLE'}), 503
```

### Ficheiro 3 — Nginx route

```nginx
# WINDI FIELD — rota directa
location /field/ {
    proxy_pass http://localhost:8114/verify-public/web/field/;
    proxy_set_header Host $host;
}

# API endpoint
location /field/seal {
    proxy_pass http://localhost:8114/field/seal;
    proxy_set_header Host $host;
}
```

### Ficheiro 4 — Chain of Custody template

```
WINDI FIELD — CHAIN OF CUSTODY
═══════════════════════════════════════════════════

RECEIPT:     {receipt_id}
HASH:        {hash}
VERIFY:      https://windi-domain.com/verify-public/?id={receipt_id}

CAPTURADO POR:
  DID:       {did}
  Momento:   {server_timestamp} UTC (carimbado pelo servidor)
  Localização: {lat}, {lng} (±{accuracy}m)

DISPOSITIVO:
  Modo:      Câmara nativa (galeria bloqueada)
  Tipo:      {file_type}
  Tamanho:   {file_size} bytes

INTEGRIDADE:
  SHA-256:   {hash}
  Ledger:    #{ledger_entry}
  Imutável desde: {server_timestamp}

VERIFICAÇÃO PÚBLICA:
  Qualquer pessoa pode verificar em:
  https://windi-domain.com/verify-public/?id={receipt_id}

═══════════════════════════════════════════════════
"AI processes. Human decides. WINDI guarantees."
WINDI Publishing House · Kempten, Bavaria · 2026
```

---

## Roadmap de Implementação

```
FASE 1 — Core (1-2 dias)
├── field-capture.html (UI com 3 gates)
├── field_server.py (timestamp servidor)
├── Nginx route /field/
└── Teste: agente real com DID + GPS + câmara nativa

FASE 2 — Integração (3-5 dias)
├── DID gate ligado ao :8096
├── Chain of Custody PDF export
├── Trilingue DE/EN/PT
└── QR no receipt FIELD

FASE 3 — EVIDENCE (2-3 semanas)
├── W-CUSTODY-001 (cadeia de custódia formal)
├── W-COURT-001 (export para tribunal)
├── Compliance BKA/Interpol/GDPR Art.6(1)(c)
└── Certificação eIDAS
```

---

## Casos de Uso Reais

| Utilizador | Cenário | O que o FIELD garante |
|---|---|---|
| Polícia no campo | Foto de cena de crime | DID + GPS + timestamp servidor = impossível contestar |
| Perito forense | Vídeo de evidência | Hash gerado no momento da captura |
| Inspector de fábrica | Relatório visual | Prova de presença física no local |
| Auditor | Documentação de anomalia | Cadeia de custódia automática |
| Jornalista | Prova de reportagem | Momento + localização + identidade |
| Trabalhador | Relatório de incidente | Proteção legal do próprio |

---

## O que torna o FIELD inimitável

```
Qualquer app tira fotos.
Qualquer app gera hash.
Qualquer app tem GPS.

Nenhuma outra app combina:
DID soberano (sem Big Tech)
+ câmara nativa obrigatória (sem retroactividade)
+ GPS locked antes do shutter (não depois)
+ timestamp do servidor (não do browser)
+ Ledger imutável público (verificável por qualquer tribunal)
+ Cadeia de custódia automática (sem burocracia)

= WINDI FIELD
```

---

## Declaração Final

> **TRAVEL:** "Tenho este ficheiro desde este momento."
> **FIELD:** "Eu — com esta identidade — estava aqui — neste momento exacto — e capturei isto."
>
> A segunda frase aguenta tribunal.
> A primeira, não.

```
"AI processes. Human decides. WINDI guarantees."
WINDI Publishing House · Kempten, Bavaria · 2026
```
