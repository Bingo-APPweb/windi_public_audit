# WINDI Verifier Integration Guide

**Guia de Integração do Verificador WINDI para Bancos e Estabelecimentos**

Este guia explica como integrar o verificador de autenticidade WINDI ao fluxo operacional de pagamentos e validação documental.

---

## O que o Verificador WINDI faz

O verificador WINDI permite:

- Confirmar que um documento não foi alterado
- Confirmar que o emissor é conhecido e confiável
- Aplicar regras de risco (ex: valor alto, IBAN divergente)
- Receber uma decisão clara: `ALLOW` / `HOLD` / `BLOCK`

---

## Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────────┐
│                     SEU AMBIENTE                                │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────┐   │
│  │ Documento │───►│ Reader SDK  │───►│ Hash + ProofSet      │   │
│  │ (PDF/XML) │    │ (local)     │    │ (documento fica aqui)│   │
│  └──────────┘    └─────────────┘    └──────────┬───────────┘   │
│                                                 │               │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │ Apenas hash
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WINDI CLOUD / NODE                          │
│  ┌───────────────────┐    ┌─────────────────┐                  │
│  │ Verification API  │───►│ Policy Engine   │                  │
│  │ /verify           │    │ + Issuer Registry│                  │
│  └───────────────────┘    └────────┬────────┘                  │
│                                    │                            │
│                    ┌───────────────┴───────────────┐           │
│                    │ decision: ALLOW/HOLD/BLOCK    │           │
│                    │ trust_level: LOW/MEDIUM/HIGH  │           │
│                    │ reason_codes: [...]           │           │
│                    └───────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fluxo Operacional

### 1. Documento recebido

Sua instituição recebe um documento (fatura, ordem de pagamento, nota fiscal).

**O documento permanece dentro do seu ambiente.**

### 2. Gerar hash local

```javascript
const { createHash } = require("crypto");
const fs = require("fs");

const file = fs.readFileSync("invoice.pdf");
const hash = createHash("sha256").update(file).digest("hex");
```

### 3. Chamar a API WINDI

```bash
POST https://api.windi.systems/verify
Content-Type: application/json
```

**Payload:**

```json
{
  "document_hash": "abc123def456...",
  "proof": {
    "issuer_id": "bank-xyz",
    "signature": "base64...",
    "signed_at": "2026-02-08T10:00:00Z",
    "public_key_id": "key-2026-001"
  },
  "context": {
    "transaction_value": 150000,
    "currency": "EUR",
    "iban": "DE89370400440532013000"
  },
  "locale": "pt"
}
```

### 4. Receber resposta

```json
{
  "decision": "HOLD",
  "trust_level": "MEDIUM",
  "reason_codes": ["HIGH_VALUE_LOW_TRUST"],
  "reasons": ["Transação de alto valor com nível de confiança insuficiente."],
  "issuer": {
    "id": "bank-xyz",
    "status": "REGISTERED",
    "trust_level": "MEDIUM"
  },
  "verification": {
    "signature_valid": true,
    "hash_match": true,
    "timestamp_valid": true
  },
  "request_id": "req_abc123",
  "verified_at": "2026-02-08T10:00:05Z"
}
```

---

## Interpretação da Decisão

| Decision | Significado | Ação Recomendada |
|----------|-------------|------------------|
| `ALLOW` | Documento autêntico e risco aceitável | Prosseguir com pagamento |
| `HOLD` | Documento válido, mas risco adicional | Revisão manual |
| `BLOCK` | Documento suspeito ou inválido | **Não pagar** |

---

## Trust Levels

| Nível | Significado | Status do Emissor |
|-------|-------------|-------------------|
| `LOW` | Problema de integridade ou emissor desconhecido | APPLIED / UNKNOWN |
| `MEDIUM` | Assinatura válida, emissor registrado | REGISTERED |
| `HIGH` | Assinatura válida, emissor confiável | TRUSTED |

---

## Reason Codes Comuns

| Código | Descrição |
|--------|-----------|
| `SIGNATURE_INVALID` | Assinatura criptográfica inválida |
| `ISSUER_UNKNOWN` | Emissor não encontrado no registry |
| `ISSUER_SUSPENDED` | Emissor temporariamente suspenso |
| `ISSUER_REVOKED` | Emissor teve registro revogado |
| `HASH_MISMATCH` | Hash do documento não confere |
| `HIGH_VALUE_LOW_TRUST` | Valor alto com confiança insuficiente |
| `IBAN_MISMATCH` | IBAN difere do registrado |
| `TIMESTAMP_EXPIRED` | Assinatura expirada |

---

## Exemplo: Integração Node.js

```javascript
const crypto = require("crypto");
const fs = require("fs");

const WINDI_API = process.env.WINDI_API_URL || "https://api.windi.systems";
const WINDI_API_KEY = process.env.WINDI_API_KEY;

async function verifyDocument(filePath, proofSet, context = {}) {
  // 1. Gerar hash local
  const file = fs.readFileSync(filePath);
  const documentHash = crypto.createHash("sha256").update(file).digest("hex");

  // 2. Chamar API WINDI
  const response = await fetch(`${WINDI_API}/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${WINDI_API_KEY}`
    },
    body: JSON.stringify({
      document_hash: documentHash,
      proof: proofSet,
      context,
      locale: "pt"
    })
  });

  if (!response.ok) {
    throw new Error(`WINDI API error: ${response.status}`);
  }

  return response.json();
}

// Uso
async function processPayment(invoicePath, proofSet, amount) {
  const result = await verifyDocument(invoicePath, proofSet, {
    transaction_value: amount,
    currency: "EUR"
  });

  switch (result.decision) {
    case "ALLOW":
      console.log("Pagamento aprovado automaticamente");
      return executePayment();

    case "HOLD":
      console.log("Pagamento requer revisão manual");
      console.log("Motivos:", result.reasons.join(", "));
      return queueForReview(result);

    case "BLOCK":
      console.log("Pagamento bloqueado");
      console.log("Motivos:", result.reasons.join(", "));
      return rejectPayment(result);
  }
}
```

---

## Exemplo: Integração Java

```java
import java.net.http.*;
import java.security.MessageDigest;
import java.nio.file.*;

public class WindiVerifier {
    private static final String WINDI_API = System.getenv("WINDI_API_URL");
    private static final String WINDI_API_KEY = System.getenv("WINDI_API_KEY");

    public VerificationResult verify(Path filePath, ProofSet proof) throws Exception {
        // 1. Gerar hash local
        byte[] fileBytes = Files.readAllBytes(filePath);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        String hash = bytesToHex(digest.digest(fileBytes));

        // 2. Chamar API WINDI
        String payload = String.format("""
            {
                "document_hash": "%s",
                "proof": %s,
                "locale": "pt"
            }
            """, hash, proof.toJson());

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(WINDI_API + "/verify"))
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + WINDI_API_KEY)
            .POST(HttpRequest.BodyPublishers.ofString(payload))
            .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
            .send(request, HttpResponse.BodyHandlers.ofString());

        return VerificationResult.fromJson(response.body());
    }
}
```

---

## Exemplo: Integração Python

```python
import hashlib
import requests
import os

WINDI_API = os.getenv("WINDI_API_URL", "https://api.windi.systems")
WINDI_API_KEY = os.getenv("WINDI_API_KEY")

def verify_document(file_path: str, proof_set: dict, context: dict = None) -> dict:
    # 1. Gerar hash local
    with open(file_path, "rb") as f:
        document_hash = hashlib.sha256(f.read()).hexdigest()

    # 2. Chamar API WINDI
    response = requests.post(
        f"{WINDI_API}/verify",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WINDI_API_KEY}"
        },
        json={
            "document_hash": document_hash,
            "proof": proof_set,
            "context": context or {},
            "locale": "pt"
        }
    )

    response.raise_for_status()
    return response.json()

# Uso
result = verify_document(
    "invoice.pdf",
    proof_set={"issuer_id": "bank-xyz", "signature": "..."},
    context={"transaction_value": 150000, "currency": "EUR"}
)

if result["decision"] == "ALLOW":
    print("Pagamento autorizado")
elif result["decision"] == "HOLD":
    print(f"Revisão necessária: {result['reasons']}")
else:
    print(f"Pagamento bloqueado: {result['reasons']}")
```

---

## Boas Práticas

### Segurança

- **Nunca envie o documento inteiro** — apenas o hash
- Use HTTPS para todas as chamadas à API
- Proteja sua API key em variáveis de ambiente
- Rotacione API keys periodicamente

### Operacional

- Armazene a resposta da API junto ao processo de pagamento
- Em casos de `HOLD`, mantenha o bundle WCAF para auditoria futura
- Use o campo `locale` para mensagens no idioma do operador
- Implemente retry com backoff para falhas de rede

### Auditoria

- Registre todas as decisões em log de auditoria
- Armazene o `request_id` para rastreabilidade
- Em disputas, gere o WCAF bundle para prova forense

---

## Prova Posterior (Auditoria)

Se houver disputa futura sobre uma transação:

### 1. Solicitar WCAF Bundle

```bash
GET /forensics/bundle/{document_id}
```

### 2. Gerar Relatório de Auditoria

```bash
POST /audit-report/report
{
  "bundle": { ... WCAF bundle ... }
}
```

### 3. Fornecer ao Auditor

- `report.pdf` — Relatório assinado
- `report.sig` — Assinatura do relatório
- `bundle.json` — Bundle WCAF completo

### 4. Auditor Verifica Independentemente

```bash
wcaf verify-pdf report.pdf report.sig windi-public.pem bundle.json
```

---

## Segurança e Privacidade

| Aspecto | Garantia WINDI |
|---------|----------------|
| Dados sensíveis | Documento nunca sai do seu ambiente |
| Hash apenas | WINDI recebe apenas hash SHA-256 |
| Reprodutibilidade | Todas as decisões são auditáveis |
| Transparência | Âncoras públicas verificáveis |

---

## Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/verify` | POST | Verificar documento |
| `/health` | GET | Status da API |
| `/issuers/{id}` | GET | Consultar emissor |
| `/issuers/{id}/keys` | GET | Chaves públicas do emissor |

---

## Rate Limits

| Plano | Requests/min | Requests/dia |
|-------|--------------|--------------|
| Starter | 100 | 10.000 |
| Business | 1.000 | 100.000 |
| Enterprise | Ilimitado | Ilimitado |

---

## Suporte

- Documentação: https://docs.windi.systems
- Status: https://status.windi.systems
- Suporte: support@windi.systems

---

## Resumo

Integrar o verificador WINDI permite que sua instituição:

- Reduza fraude documental
- Automatize decisões de pagamento
- Tenha prova técnica e institucional das decisões
- Cumpra requisitos de auditoria e compliance

**Um documento verificado pelo WINDI é:**
- Autêntico (não foi alterado)
- Atribuível (emissor conhecido)
- Auditável (decisão registrada)
- Verificável (prova pública)
