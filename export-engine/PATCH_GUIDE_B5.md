# ═══════════════════════════════════════════════════════════
# WINDI M3 Export Engine — B5 Patch: Tiptap JSON → Text
# ═══════════════════════════════════════════════════════════
# 
# PROBLEMA: PDF exporta JSON bruto do Tiptap no corpo
# SOLUÇÃO: Parser converte Tiptap JSON → texto legível
#
# Three Dragons Protocol v1.1 — I9 Active
# ═══════════════════════════════════════════════════════════

## PASSO 1 — Copiar o parser para o servidor

```bash
# Na máquina local, copiar o arquivo tiptap_parser.py para o servidor:
scp tiptap_parser.py windi@87.106.29.233:/opt/windi/export-engine/

# OU criar diretamente no servidor:
# (cole o conteúdo do tiptap_parser.py)
nano /opt/windi/export-engine/tiptap_parser.py
```

## PASSO 2 — Encontrar o ponto de patch

```bash
# Encontrar onde o conteúdo do documento é inserido no PDF:
cd /opt/windi/export-engine/
grep -n "content\|body\|text\|drawString\|Paragraph\|json\|doc_content" *.py
```

## PASSO 3 — Aplicar o patch

No script principal do Export Engine, fazer 2 mudanças:

### 3a. Adicionar import (no topo do arquivo):

```python
from tiptap_parser import tiptap_to_plaintext
```

### 3b. Converter conteúdo antes de renderizar

Procurar a linha onde o conteúdo do documento é passado para o PDF.
Provavelmente algo como:

```python
# ANTES (bug - renderiza JSON bruto):
body_text = doc.get("content", "")
# ou
body_text = request_data.get("content", "")
# ou  
c.drawString(x, y, str(content))
```

Substituir por:

```python
# DEPOIS (fix - renderiza texto humano):
raw_content = doc.get("content", "")
body_text = tiptap_to_plaintext(raw_content)
```

### PADRÃO COMUM — se usa reportlab Paragraph:

```python
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer

# Converter Tiptap JSON → linhas de texto
body_text = tiptap_to_plaintext(raw_content)

# Renderizar cada parágrafo
styles = getSampleStyleSheet()
for line in body_text.split('\n'):
    if line.strip():
        story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 6))
```

### PADRÃO COMUM — se usa canvas.drawString:

```python
# Converter Tiptap JSON → texto
body_text = tiptap_to_plaintext(raw_content)

# Renderizar linha por linha
y_position = 700  # abaixo do header seal
line_height = 14

for line in body_text.split('\n'):
    if y_position < 120:  # espaço para footer/receipt
        c.showPage()
        y_position = 750
    c.drawString(72, y_position, line)
    y_position -= line_height
```

## PASSO 4 — Testar e reiniciar

```bash
# Testar o parser isolado:
cd /opt/windi/export-engine/
python3 -c "from tiptap_parser import tiptap_to_plaintext; print(tiptap_to_plaintext('{\"type\":\"doc\",\"content\":[{\"type\":\"paragraph\",\"content\":[{\"type\":\"text\",\"text\":\"Hello WINDI\"}]}]}'))"

# Deve imprimir: Hello WINDI

# Reiniciar o serviço:
sudo systemctl restart windi-export
sudo systemctl status windi-export --no-pager

# Verificar health:
curl -s http://localhost:8103/health | python3 -m json.tool
```

## PASSO 5 — Teste end-to-end

1. Abrir https://admin.windia4desk.tech/desktop/
2. Criar/abrir documento
3. Escrever texto, esperar "✅ Saved" + "● Integrity OK"
4. Exportieren ▾ → 📄 PDF mit Governance-Siegel M3
5. O PDF deve agora mostrar texto legível com:
   - Header: Selo dourado WINDI + data + ISP
   - Body: TEXTO FORMATADO (não JSON!)
   - Footer: QR Code + Forensic Receipt + SHA-256 hash

## DIAGRAMA DA CORREÇÃO

```
ANTES:
  Editor → Tiptap JSON → Export Engine → reportlab → PDF
                          ↑ BUG: passa JSON bruto direto

DEPOIS:
  Editor → Tiptap JSON → tiptap_parser → texto legível → reportlab → PDF
                          ↑ FIX: converte antes de renderizar
```

## NOTA DE GOVERNANÇA

O hash SHA-256 no Receipt NÃO muda — ele é calculado sobre o conteúdo
original do editor (JSON), que é o formato canônico. A conversão para
texto é apenas para VISUALIZAÇÃO no PDF. A integridade criptográfica
permanece intacta.

═══════════════════════════════════════════════════════════
AI processes. Human decides. WINDI guarantees.
═══════════════════════════════════════════════════════════
