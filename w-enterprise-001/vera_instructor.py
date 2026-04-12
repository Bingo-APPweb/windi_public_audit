# ═══════════════════════════════════════════════════════════════════════════
#  vera_instructor.py — VERA · Sovereign Instructor
#  REGO v1.2 · R10 Pedagogia Activa · R11 IAT-001 · R12 Mapa Vivo
#  Liga IA+H · Human Dragon · 12 Abril 2026
#
#  Princípio R10: "Não respondes. Guias. Não instruís. Capacitas."
#
#  VERA como instructor:
#   - Detecta lacunas de conhecimento
#   - Guia o utilizador pelos módulos
#   - Usa contexto inter-agente (IAT-001)
#   - Adapta nível de explicação (Tutorial/Briefing/Executive)
#   - Nunca abandona o utilizador diante de uma ferramenta desconhecida
# ═══════════════════════════════════════════════════════════════════════════

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("vera.instructor")

# ─── PATHS ────────────────────────────────────────────────────────────────
MODULE_MAP_PATH = Path(__file__).parent / "vera_module_map.json"

# ─── MODELS ───────────────────────────────────────────────────────────────
InstructorLevel = Literal["tutorial", "briefing", "executive"]

class InstructorRequest(BaseModel):
    officer_did: str
    module_id: Optional[str] = None
    action_id: Optional[str] = None
    question: Optional[str] = None
    level: InstructorLevel = "briefing"
    lang: Literal["pt", "de", "en"] = "en"

class InstructorResponse(BaseModel):
    status: str
    module_id: Optional[str]
    guidance: str
    legal_anchors: List[str]
    next_steps: List[str]
    vera_tip: Optional[str]
    pho_required: bool
    level: str
    lang: str
    timestamp: str

class OnboardingRequest(BaseModel):
    officer_did: str
    workflow_id: str = "new_user_onboarding"
    lang: Literal["pt", "de", "en"] = "en"

class OnboardingResponse(BaseModel):
    status: str
    workflow_id: str
    workflow_label: str
    modules_sequence: List[str]
    vera_intro: str
    current_step: int
    total_steps: int
    lang: str
    timestamp: str

# ─── MODULE MAP LOADER ────────────────────────────────────────────────────
class ModuleMap:
    """Loads and provides access to vera_module_map.json"""

    def __init__(self, path: Path = MODULE_MAP_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Module map not found: {path} [I14]")
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._modules = self._data.get("modules", {})
        self._workflows = self._data.get("common_workflows", [])
        self._adoption_seq = self._data.get("adoption_sequence", [])
        log.info(f"Module map loaded: {len(self._modules)} modules · {len(self._workflows)} workflows")

    def get_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        return self._modules.get(module_id)

    def get_all_modules(self) -> Dict[str, Any]:
        return self._modules

    def get_adoption_sequence(self) -> List[str]:
        return self._adoption_seq

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        for wf in self._workflows:
            if wf.get("id") == workflow_id:
                return wf
        return None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        return self._workflows

    def get_meta(self) -> Dict[str, Any]:
        return self._data.get("_meta", {})

# ─── INSTRUCTOR ENGINE ────────────────────────────────────────────────────
class VERAInstructor:
    """
    VERA Sovereign Instructor Engine.
    R10: Detecta lacunas e entra em modo instructor automaticamente.
    R12: Conhece todos os módulos em profundidade.
    """

    def __init__(self):
        self.module_map = ModuleMap()

    def _get_text(self, obj: Any, lang: str) -> str:
        """Extract text from multilingual dict or return string directly."""
        if isinstance(obj, dict):
            return obj.get(lang, obj.get("en", str(obj)))
        return str(obj) if obj else ""

    def get_module_guidance(
        self,
        module_id: str,
        action_id: Optional[str],
        level: InstructorLevel,
        lang: str,
        officer_did: str,
    ) -> InstructorResponse:
        """
        Get guidance for a specific module/action.
        R10: Adapts explanation level based on user context.
        """
        module = self.module_map.get_module(module_id)

        if not module:
            raise HTTPException(
                status_code=404,
                detail=f"Module '{module_id}' not found in module map [I14]"
            )

        # Build guidance based on level
        vera_intro = self._get_text(module.get("vera_intro", ""), lang)
        legal_anchors = module.get("legal_anchors", [])
        pho_triggers = module.get("pho_required_when", [])

        if level == "tutorial":
            # Detailed step-by-step
            guidance = f"{vera_intro}\n\n"
            if action_id:
                action = self._find_action(module, action_id)
                if action:
                    steps = self._get_text(action.get("steps", []), lang)
                    if isinstance(steps, list):
                        guidance += "Passos:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))
                    else:
                        guidance += f"Passos: {steps}"
        elif level == "executive":
            # Brief summary only
            guidance = module.get("short", module.get("label", ""))
            guidance += f" — {', '.join(legal_anchors[:2])}" if legal_anchors else ""
        else:
            # Briefing (default)
            guidance = vera_intro

        # Get vera_tip if action specified
        vera_tip = None
        if action_id:
            action = self._find_action(module, action_id)
            if action:
                vera_tip = self._get_text(action.get("vera_tip", ""), lang)

        # Next steps
        next_module = module.get("next_module")
        next_steps = []
        if next_module:
            next_mod_data = self.module_map.get_module(next_module)
            if next_mod_data:
                next_steps.append(f"Próximo módulo: {next_mod_data.get('label', next_module)}")

        return InstructorResponse(
            status="success",
            module_id=module_id,
            guidance=guidance,
            legal_anchors=legal_anchors,
            next_steps=next_steps,
            vera_tip=vera_tip,
            pho_required=len(pho_triggers) > 0,
            level=level,
            lang=lang,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _find_action(self, module: Dict[str, Any], action_id: str) -> Optional[Dict[str, Any]]:
        """Find an action within a module's key_actions."""
        for action in module.get("key_actions", []):
            if action.get("id") == action_id:
                return action
        return None

    def start_onboarding(
        self,
        workflow_id: str,
        lang: str,
        officer_did: str,
    ) -> OnboardingResponse:
        """
        Start a guided onboarding workflow.
        R10: VERA guia o utilizador desde o primeiro passo.
        """
        workflow = self.module_map.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' not found [I14]"
            )

        label = self._get_text(workflow.get("label", workflow_id), lang)
        vera_intro = self._get_text(workflow.get("vera_intro", ""), lang)
        sequence = workflow.get("vera_sequence", [])

        return OnboardingResponse(
            status="success",
            workflow_id=workflow_id,
            workflow_label=label,
            modules_sequence=sequence,
            vera_intro=vera_intro,
            current_step=1,
            total_steps=len(sequence),
            lang=lang,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def answer_question(
        self,
        question: str,
        officer_did: str,
        lang: str,
    ) -> Dict[str, Any]:
        """
        Answer a freeform question by identifying relevant modules.
        R10: VERA nunca deixa o utilizador sem resposta.
        """
        question_lower = question.lower()

        # Simple keyword matching to find relevant modules
        relevance = []
        for mod_id, mod_data in self.module_map.get_all_modules().items():
            score = 0
            label = mod_data.get("label", "").lower()
            short = mod_data.get("short", "").lower()
            desc = mod_data.get("description", "").lower()

            if mod_id in question_lower or label in question_lower:
                score += 10
            if short in question_lower:
                score += 5

            # Check legal anchors
            for anchor in mod_data.get("legal_anchors", []):
                if anchor.lower() in question_lower:
                    score += 8

            # Keywords
            keywords = {
                "pho": ["supervisão", "oversight", "aprovação", "approval", "humano", "human"],
                "lod1": ["risco", "risk", "regist", "first line", "primeira linha"],
                "lod2": ["compliance", "supervisão", "review", "segunda linha"],
                "doc_gen": ["documento", "document", "gerar", "generate", "contrato", "contract"],
                "obs_engine": ["monitor", "alert", "anomal", "observ"],
                "invoice_gen": ["factura", "invoice", "xrechnung", "zugferd"],
                "legal_advisory": ["legal", "jurídic", "advic", "parecer"],
                "rep": ["relatório", "report", "audit", "csrd", "dora"],
            }

            for kw in keywords.get(mod_id, []):
                if kw in question_lower:
                    score += 3

            if score > 0:
                relevance.append((mod_id, mod_data, score))

        # Sort by relevance
        relevance.sort(key=lambda x: x[2], reverse=True)

        if relevance:
            top_mod_id, top_mod, _ = relevance[0]
            vera_intro = self._get_text(top_mod.get("vera_intro", ""), lang)
            legal_anchors = top_mod.get("legal_anchors", [])

            return {
                "status": "success",
                "matched_module": top_mod_id,
                "module_label": top_mod.get("label", top_mod_id),
                "guidance": vera_intro,
                "legal_anchors": legal_anchors,
                "other_relevant": [m[0] for m in relevance[1:4]],
                "lang": lang,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "status": "no_match",
                "guidance": self._get_fallback_guidance(lang),
                "suggested_workflow": "new_user_onboarding",
                "lang": lang,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _get_fallback_guidance(self, lang: str) -> str:
        fallbacks = {
            "pt": "Não encontrei um módulo específico para a tua pergunta. Recomendo começares pelo PHO — é o coração do sistema. Posso guiar-te pelo onboarding?",
            "de": "Ich habe kein spezifisches Modul für deine Frage gefunden. Ich empfehle, mit PHO zu beginnen — es ist das Herz des Systems. Soll ich dich durch das Onboarding führen?",
            "en": "I didn't find a specific module for your question. I recommend starting with PHO — it's the heart of the system. Shall I guide you through onboarding?",
        }
        return fallbacks.get(lang, fallbacks["en"])


# ─── FASTAPI ROUTER ───────────────────────────────────────────────────────
def create_instructor_router() -> APIRouter:
    router = APIRouter(prefix="/vera/instructor", tags=["VERA-Instructor"])
    instructor = VERAInstructor()

    # Import DID Gate
    from vera_did_gate import verify_did, bind_action_to_did, get_wallet_banner, restore_did_context

    @router.post("/ask", response_model=None)
    async def instructor_ask(req: InstructorRequest):
        """
        Main instructor endpoint.
        - If module_id provided: get module-specific guidance
        - If question provided: answer freeform question
        R10: VERA nunca deixa o utilizador sozinho.

        EVANGELHO: DID é PORTÃO.
        Lei I: Sem DID → WalletBanner mode.
        Lei II: Cada pergunta → rastro no Ledger.
        Lei III: DID regressa → VERA restaura contexto.
        """
        # LEI I — Existência antes de Acção
        if not req.officer_did:
            banner = get_wallet_banner(req.lang)
            return {
                "status": "did_required",
                "law": "Lei I — Existência antes de Acção",
                "message": "DID obrigatório para instrução VERA.",
                "wallet_banner": banner.model_dump(),
            }

        # Validate DID
        validation = await verify_did(req.officer_did)
        if not validation.valid:
            banner = get_wallet_banner(req.lang)
            return {
                "status": "invalid_did",
                "law": "Lei I — Existência antes de Acção",
                "error": validation.error,
                "wallet_banner": banner.model_dump(),
            }

        # LEI III — Restaurar contexto ao regressar
        context = await restore_did_context(req.officer_did)

        # Process request
        if req.module_id:
            result = instructor.get_module_guidance(
                module_id=req.module_id,
                action_id=req.action_id,
                level=req.level,
                lang=req.lang,
                officer_did=req.officer_did,
            )
            action = f"module_guidance:{req.module_id}"
        elif req.question:
            result = instructor.answer_question(
                question=req.question,
                officer_did=req.officer_did,
                lang=req.lang,
            )
            action = "question"
        else:
            raise HTTPException(
                status_code=400,
                detail="Either module_id or question required [I14]"
            )

        # LEI II — Toda Acção gera Rastro DID
        await bind_action_to_did(
            did=req.officer_did,
            action=action,
            module="instructor",
        )

        # Enrich with context
        if isinstance(result, dict):
            result["did_context"] = {
                "total_actions": context.get("history", {}).get("total_actions", 0),
                "modules_used": context.get("history", {}).get("modules_used", []),
            }

        return result

    @router.post("/onboard", response_model=None)
    async def start_onboarding(req: OnboardingRequest):
        """
        Start a guided onboarding workflow.
        R10: Pedagogia activa desde o primeiro contacto.

        EVANGELHO: DID é PORTÃO.
        """
        # LEI I — Existência antes de Acção
        if not req.officer_did:
            banner = get_wallet_banner(req.lang)
            return {
                "status": "did_required",
                "law": "Lei I — Existência antes de Acção",
                "message": "DID obrigatório para onboarding.",
                "wallet_banner": banner.model_dump(),
            }

        # Validate DID
        validation = await verify_did(req.officer_did)
        if not validation.valid:
            banner = get_wallet_banner(req.lang)
            return {
                "status": "invalid_did",
                "error": validation.error,
                "wallet_banner": banner.model_dump(),
            }

        result = instructor.start_onboarding(
            workflow_id=req.workflow_id,
            lang=req.lang,
            officer_did=req.officer_did,
        )

        # LEI II — Toda Acção gera Rastro DID
        await bind_action_to_did(
            did=req.officer_did,
            action=f"onboarding:{req.workflow_id}",
            module="instructor",
        )

        return result

    @router.get("/module/{module_id}")
    async def get_module_info(module_id: str, lang: str = "en"):
        """Get detailed information about a specific module."""
        module = instructor.module_map.get_module(module_id)
        if not module:
            raise HTTPException(404, f"Module '{module_id}' not found [I14]")
        return {
            "status": "success",
            "module": module,
            "lang": lang,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/modules")
    async def list_modules():
        """List all available modules."""
        return {
            "status": "success",
            "modules": list(instructor.module_map.get_all_modules().keys()),
            "adoption_sequence": instructor.module_map.get_adoption_sequence(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/adoption-sequence")
    async def get_adoption_sequence():
        """Get the recommended module adoption sequence."""
        seq = instructor.module_map.get_adoption_sequence()
        modules = instructor.module_map.get_all_modules()

        detailed = []
        for i, mod_id in enumerate(seq, 1):
            mod = modules.get(mod_id, {})
            detailed.append({
                "order": i,
                "id": mod_id,
                "label": mod.get("label", mod_id),
                "short": mod.get("short", ""),
            })

        return {
            "status": "success",
            "sequence": detailed,
            "vera_recommendation": "Comece pelo PHO, depois ObsEngine, depois 1LOD. Esta sequência garante que entende a supervisão humana antes de começar a registar.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/workflows")
    async def list_workflows():
        """List all available onboarding workflows."""
        return {
            "status": "success",
            "workflows": instructor.module_map.get_all_workflows(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/health")
    async def instructor_health():
        try:
            mm = ModuleMap()
            return {
                "status": "operational",
                "engine": "VERA Instructor v1.0",
                "constitution": "REGO v1.2 · R10 + R12",
                "modules_loaded": len(mm.get_all_modules()),
                "workflows_loaded": len(mm.get_all_workflows()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    return router
