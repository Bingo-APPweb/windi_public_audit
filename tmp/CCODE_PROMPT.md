## MISSÃO: Deploy WINDI Drive In — Video Background para Palette

### O QUE É
Um vídeo épico de dragões voando numa floresta mágica, tocando em LOOP atrás da Palette
a 5% de opacidade. Cria uma textura subliminal "viva". Um slider 🐉 no canto inferior
direito permite ao usuário revelar de 0% a 100%.

### PASSO 1: Upload dos arquivos para o servidor

No PowerShell do Windows:

```powershell
cd "PASTA_ONDE_BAIXOU_OS_ARQUIVOS"

# Upload do vídeo otimizado (15MB, faststart, H.264)
scp dragons-forest.mp4 windi@87.106.29.233:/opt/windi/desktop/static/dragons-forest.mp4

# Upload do módulo JavaScript
scp windi-drivein.js windi@87.106.29.233:/opt/windi/desktop/static/windi-drivein.js
```

### PASSO 2: Verificar no servidor

```bash
ssh windi@87.106.29.233

# Confirmar arquivos
ls -lh /opt/windi/desktop/static/dragons-forest.mp4
ls -lh /opt/windi/desktop/static/windi-drivein.js

# Testar se Palette serve static
curl -s -o /dev/null -w "%{http_code}" http://localhost:8108/static/dragons-forest.mp4
```

### PASSO 3: CCode Prompt

Enviar este prompt exato para o CCode:

---

```
TAREFA: Injetar WINDI Drive In na Palette UNIFIED.

O arquivo /opt/windi/desktop/static/windi-drivein.js já está no servidor.
O vídeo /opt/windi/desktop/static/dragons-forest.mp4 já está no servidor.

AÇÃO ÚNICA: Adicionar esta linha ANTES do </body> no HTML da Palette UNIFIED:

<script src="/palette/static/windi-drivein.js"></script>

VERIFICAÇÃO ADICIONAL: Garantir que o container principal da Palette tem
position: relative e z-index: 1 ou superior (para ficar acima do vídeo
que fica em z-index: 0).

NÃO alterar nenhum outro código. NÃO tocar em nginx. NÃO tocar em endpoints.
O módulo é 100% autossuficiente.

TESTE: Abrir a Palette no browser. Verificar slider 🐉 no canto inferior direito.
```

---

### PASSO 4: Verificação visual

1. Abrir https://admin.windia4desk.tech/palette/
2. Olhar para o canto inferior direito → slider 🐉 deve estar visível
3. A 5%: movimento muito sutil por trás do conteúdo
4. Arrastar para 50%: floresta e dragões claramente visíveis
5. Arrastar para 100%: imersão total
6. Toggle KLAR ↔ NOIR: slider adapta-se
7. Refresh: opacidade mantém-se (localStorage)
