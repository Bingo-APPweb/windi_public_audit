# W-MOTOR-001 — Tutorial Multi-Provider
## Para Irmãos CCode/Claude entenderem o funcionamento

**Data:** 2026-07-09
**Liga IA+H:** Human Dragon (I9) · CCode (Opus 4.5)
**Formato:** DIFF-style para máxima clareza

---

## TL;DR — O Que Mudou

```diff
ANTES (single-provider):
- Motor só suportava IONOS
- Hardcoded no engine.py
- Sem extensibilidade

DEPOIS (multi-provider):
+ Registry de providers
+ 5 providers: ionos, runway, openart, local-gpu, dry-run
+ Extensível para novos providers
+ Cada provider declara capabilities
```

---

## 1. ARQUITECTURA MULTI-PROVIDER

```
┌─────────────────────────────────────────────────────────────────┐
│                    W-MOTOR-001 ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CLI (w_hios_motor.py)                                         │
│         │                                                       │
│         ▼                                                       │
│   ENGINE (engine.py)                                            │
│         │                                                       │
│         ▼                                                       │
│   PROVIDER REGISTRY (providers.py)                              │
│         │                                                       │
│    ┌────┴────┬────────┬──────────┬─────────────┐                │
│    ▼         ▼        ▼          ▼             ▼                │
│  IONOS   RUNWAY   OPENART   LOCAL-GPU     DRY-RUN              │
│  (LIVE)   (STUB)   (STUB)    (STUB)       (LIVE)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. DIFF — providers.py

### 2.1 Nova Estrutura de Classes

```diff
# ANTES: Uma única classe IonosImageProvider
- class IonosImageProvider:
-     """IONOS AI Model Hub image provider adapter."""
-     name = "ionos-ai-model-hub"

# DEPOIS: Hierarquia com BaseProvider + Protocol
+ class ProviderProtocol(Protocol):
+     """Interface que todos os providers implementam."""
+     name: str
+     capabilities: list[str]
+     def provenance(self) -> dict[str, Any]: ...
+     def generate(self, job, workspace) -> dict[str, Any]: ...
+
+ class BaseProvider:
+     """Classe base com utilities comuns."""
+     def _read_prompt(self, job, workspace) -> str: ...
+     def _save_image_bytes(self, ...) -> dict: ...
+     def _save_video_bytes(self, ...) -> dict: ...
+
+ class IonosImageProvider(BaseProvider):
+     capabilities = ["text-to-image"]
+
+ class RunwayVideoProvider(BaseProvider):
+     capabilities = ["image-to-video", "face-consistency"]
+
+ class OpenArtProvider(BaseProvider):
+     capabilities = ["face-swap", "face-consistency"]
+
+ class LocalGPUProvider(BaseProvider):
+     capabilities = ["text-to-image", "local"]
+
+ class DryRunProvider(BaseProvider):
+     capabilities = ["testing"]
```

### 2.2 Provider Registry

```diff
# ANTES: Não existia
# DEPOIS: Registry centralizado

+ PROVIDER_REGISTRY: dict[str, Type[BaseProvider]] = {
+     "ionos": IonosImageProvider,
+     "runway": RunwayVideoProvider,
+     "openart": OpenArtProvider,
+     "local-gpu": LocalGPUProvider,
+     "dry-run": DryRunProvider,
+ }
+
+ def get_provider(name: str) -> BaseProvider:
+     """Retorna instância do provider pelo nome."""
+     if name not in PROVIDER_REGISTRY:
+         raise ProviderError(f"Unknown provider '{name}'")
+     return PROVIDER_REGISTRY[name]()
```

### 2.3 Novas Excepções

```diff
# ANTES: Apenas ProviderError
- class ProviderError(RuntimeError): ...

# DEPOIS: Hierarquia de erros
+ class ProviderError(RuntimeError):
+     """Erro genérico de provider."""
+
+ class ProviderNotConfigured(ProviderError):
+     """Provider sem configuração necessária (API key, etc)."""
+
+ class ProviderNotImplemented(ProviderError):
+     """Provider ainda não implementado (stub)."""
```

---

## 3. DIFF — engine.py

### 3.1 run_next_job()

```diff
# ANTES: Hardcoded para IONOS
  def run_next_job(*, workspace, provider="ionos", dry_run=False):
-     if provider != "ionos":
-         raise MotorError(f"Provider '{provider}' is not implemented yet.")
-     from .providers import IonosImageProvider
-     adapter = IonosImageProvider()

# DEPOIS: Usa registry
  def run_next_job(*, workspace, provider="ionos", dry_run=False):
+     from .providers import get_provider
+
+     if dry_run:
+         adapter = get_provider("dry-run")
+     else:
+         adapter = get_provider(provider)
+
+     output = adapter.generate(job, root)
```

---

## 4. COMO ADICIONAR NOVO PROVIDER

### Passo 1: Criar Classe no providers.py

```python
class MeuNovoProvider(BaseProvider):
    """Descrição do provider."""

    name = "meu-provider"
    capabilities = ["text-to-image", "capability-2"]

    def __init__(self):
        self.api_key = os.environ.get("WHIOS_MEU_PROVIDER_API_KEY", "")
        if not self.api_key:
            raise ProviderNotConfigured("Missing API key")

    def provenance(self) -> dict[str, Any]:
        return {
            "provider": "meu-provider",
            "adapter": self.name,
            "capabilities": self.capabilities,
            # ... metadata sem secrets
        }

    def generate(self, job: dict, workspace: Path) -> dict[str, Any]:
        # Implementar geração
        # Retornar:
        # {
        #     "path": "outputs/...",
        #     "sha256": "...",
        #     "mime_type": "image/png",
        #     "kind": "image_file",
        # }
        pass
```

### Passo 2: Registar no Registry

```python
PROVIDER_REGISTRY["meu-provider"] = MeuNovoProvider
```

### Passo 3: Documentar Capabilities

```python
"""
Capabilities:
    - text-to-image: Gera imagem de texto
    - image-to-video: Gera vídeo de imagem
    - face-swap: Troca face em imagem/vídeo
    - face-consistency: Mantém identidade facial
    - local: Não faz chamadas externas
    - testing: Apenas para testes
"""
```

---

## 5. COMANDOS ÚTEIS

```bash
# Listar providers disponíveis
python3 -c "from w_hios_motor.providers import list_providers; import json; print(json.dumps(list_providers(), indent=2))"

# Testar provider específico
python3 scripts/w_hios_motor.py create-image --prompt "test" --provider ionos
python3 scripts/w_hios_motor.py run-next --provider ionos

# Dry-run (sem chamar API)
python3 scripts/w_hios_motor.py run-next --provider dry-run

# Ver capabilities de um provider
python3 -c "from w_hios_motor.providers import get_provider; p=get_provider('ionos'); print(p.capabilities)"
```

---

## 6. TABELA DE PROVIDERS

| Provider | Status | Capabilities | Uso |
|----------|--------|--------------|-----|
| `ionos` | 🟢 LIVE | text-to-image | Backgrounds, props, new characters |
| `runway` | 🔴 STUB | image-to-video, face-consistency | Video from anchor |
| `openart` | 🔴 STUB | face-swap, face-consistency | Apply anchor to content |
| `local-gpu` | 🔴 STUB | text-to-image, local | Self-hosted (needs GPU) |
| `dry-run` | 🟢 LIVE | testing | Testing pipeline |

---

## 7. ENV VARS POR PROVIDER

```bash
# IONOS (LIVE)
WHIOS_IONOS_IMAGE_ENDPOINT=https://openai.inference.de-txl.ionos.com/v1/images/generations
WHIOS_IONOS_API_TOKEN=eyJ...  # JWT, expira ~1h

# RUNWAY (STUB)
WHIOS_RUNWAY_API_KEY=...  # Quando implementar

# OPENART (STUB)
WHIOS_OPENART_API_KEY=...  # Quando implementar

# LOCAL-GPU (STUB)
WHIOS_LOCAL_GPU_MODEL=stabilityai/stable-diffusion-xl-base-1.0
WHIOS_LOCAL_GPU_DEVICE=cuda:0

# COMMON
WHIOS_MOTOR_WORKSPACE=/opt/windi/hios/motor/workspace
```

---

## 8. FLUXO DE DECISÃO — QUAL PROVIDER USAR?

```
┌─────────────────────────────────────────────┐
│         PRECISO GERAR MEDIA                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Tem face?      │
          └───────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
       SIM                 NÃO
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ É personagem  │   │ Use IONOS     │
│ existente?    │   │ (backgrounds, │
└───────┬───────┘   │  props, etc)  │
        │           └───────────────┘
   ┌────┴────┐
   │         │
  SIM       NÃO
   │         │
   ▼         ▼
┌────────┐ ┌────────────┐
│ RUNWAY │ │ IONOS para │
│ ou     │ │ criar novo │
│OPENART │ │ (1ª vez)   │
└────────┘ └────────────┘
```

---

## 9. INVARIANTES DO MOTOR

| ID | Invariante | Descrição |
|----|------------|-----------|
| M1 | Provider Provenance | Toda geração tem metadata de provider (sem secrets) |
| M2 | Manifest Atomicity | Output + manifest gerados juntos (I19) |
| M3 | Failure Classification | Erros classificados por tipo (V2-V8) |
| M4 | Human Gate | Promoção a âncora requer I9 |
| M5 | No Secret Leak | Tokens nunca em manifests/outputs |

---

## 10. PRÓXIMOS PASSOS

### Para activar RUNWAY:
```bash
# 1. Obter API key em runwayml.com
# 2. Adicionar ao .env
echo "WHIOS_RUNWAY_API_KEY=..." >> /opt/windi/hios/motor/.env

# 3. Implementar generate() em RunwayVideoProvider
# 4. Testar
python3 scripts/w_hios_motor.py create-image --provider runway --prompt "..."
```

### Para activar LOCAL-GPU:
```bash
# 1. Adquirir servidor com GPU (Hetzner, OVH, etc)
# 2. Instalar CUDA + PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install diffusers transformers accelerate

# 3. Implementar generate() em LocalGPUProvider
# 4. Testar
python3 scripts/w_hios_motor.py create-image --provider local-gpu --prompt "..."
```

---

*Liga IA+H · WINDI Publishing House · 2026-07-09*
*"O motor orquestra. Os providers executam."*
