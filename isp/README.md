# WINDI ISP Library
## Institutional Style Profile System

**Version:** 1.0.0 | **Date:** 2026-02-01 | **Status:** Production

---

## O que é ISP?

ISP (Institutional Style Profile) aplica identidade visual institucional em documentos WINDI. Cada instituição pode ter cores, logos, tipografia e formatação específica mantendo a governança consistente.

**Princípio:** Governança consistente, identidade visual flexível.

---

## Estrutura
```
/opt/windi/isp/
├── README.md
├── isp_loader.py
├── _base/profile.json
└── deutsche-bahn/
    ├── profile.json
    ├── styles.css
    └── assets/logo_db.svg
```

---

## Criar Novo ISP
```bash
# 1. Criar diretório
mkdir -p /opt/windi/isp/NOME/assets

# 2. Copiar templates
cp /opt/windi/isp/_base/profile.json /opt/windi/isp/NOME/
cp /opt/windi/isp/deutsche-bahn/styles.css /opt/windi/isp/NOME/

# 3. Editar profile.json (id, name, colors.primary)
# 4. Adicionar logo SVG em assets/
# 5. Ajustar styles.css com cor primária
# 6. Testar: curl http://localhost:8085/api/isp/NOME
```

---

## API Endpoints

| Endpoint | Descrição |
|----------|-----------|
| GET /api/isp/list | Lista perfis disponíveis |
| GET /api/isp/{id} | Retorna profile.json |
| GET /api/isp/{id}/css | Retorna styles.css |
| GET /api/isp/{id}/logo | Retorna logo file |

---

## Aplicar ISP a Documento
```sql
UPDATE documents 
SET metadata = '{"institutional_profile": "deutsche-bahn"}' 
WHERE id = 'DOC-ID';
```

---

## Perfis Disponíveis

| ID | Instituição | Cor | Status |
|----|-------------|-----|--------|
| deutsche-bahn | Deutsche Bahn AG | #EC0016 | ✅ Produção |

---

## Funcionalidades

- Logo institucional no header
- Cores corporativas aplicadas
- Footer com "Seite X von Y"
- Tipografia customizada
- Integração com WINDI Governance Ledger

---

*WINDI Publishing House - AI processes. Human decides. WINDI guarantees.*
