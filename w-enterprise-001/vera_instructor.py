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
    # §162 F2: Optional profile override (if not set, uses DID's stored profile)
    officer_profile: Optional[str] = None

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
    # §162 F2: Profile-aware fields
    profile_context: Optional[Dict[str, Any]] = None
    profile_focus: Optional[List[str]] = None

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

# ─── §162 F2: PROFILE-AWARE GUIDANCE TEMPLATES ───────────────────────────
PROFILE_GUIDANCE_TEMPLATES = {
    "digital_risk": {
        "pt": {
            "intro": "Como especialista em risco e compliance, aqui está o que precisas saber:",
            "focus": "Foco: Âncoras legais, validação de políticas, evidência de auditoria.",
            "action": "Próximo passo compliance:",
        },
        "de": {
            "intro": "Als Risiko- und Compliance-Spezialist, hier ist was du wissen musst:",
            "focus": "Fokus: Rechtliche Anker, Policy-Validierung, Audit-Evidenz.",
            "action": "Nächster Compliance-Schritt:",
        },
        "en": {
            "intro": "As a risk and compliance specialist, here's what you need to know:",
            "focus": "Focus: Legal anchors, policy validation, audit evidence.",
            "action": "Next compliance step:",
        },
    },
    "tech_product": {
        "pt": {
            "intro": "Como owner de produto/sistemas, aqui está a perspectiva técnica:",
            "focus": "Foco: Integração, APIs, workflow de automação, design de sistema.",
            "action": "Próximo passo técnico:",
        },
        "de": {
            "intro": "Als Produkt-/System-Owner, hier ist die technische Perspektive:",
            "focus": "Fokus: Integration, APIs, Automatisierungs-Workflow, System-Design.",
            "action": "Nächster technischer Schritt:",
        },
        "en": {
            "intro": "As a product/systems owner, here's the technical perspective:",
            "focus": "Focus: Integration, APIs, automation workflow, system design.",
            "action": "Next technical step:",
        },
    },
    "internal_auditor": {
        "pt": {
            "intro": "Como auditor interno, aqui está a prova verificável:",
            "focus": "Foco: Verificação directa, queries Ledger, cadeia de evidência, prova SHA-256.",
            "action": "Próximo passo de auditoria:",
        },
        "de": {
            "intro": "Als interner Prüfer, hier ist der verifizierbare Beweis:",
            "focus": "Fokus: Direkte Verifizierung, Ledger-Abfragen, Evidenzkette, SHA-256-Beweis.",
            "action": "Nächster Audit-Schritt:",
        },
        "en": {
            "intro": "As an internal auditor, here's the verifiable evidence:",
            "focus": "Focus: Direct verification, Ledger queries, evidence chain, SHA-256 proof.",
            "action": "Next audit step:",
        },
    },
}


# ─── INSTRUCTOR ENGINE ────────────────────────────────────────────────────
class VERAInstructor:
    """
    VERA Sovereign Instructor Engine.
    R10: Detecta lacunas e entra em modo instructor automaticamente.
    R12: Conhece todos os módulos em profundidade.
    §162 F2: Adapts guidance based on officer profile (OVS).
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
        officer_profile: Optional[str] = None,
    ) -> InstructorResponse:
        """
        Get guidance for a specific module/action.
        R10: Adapts explanation level based on user context.
        §162 F2: Adapts tone and focus based on officer profile.
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

        # §162 F2: Get profile-specific templates
        profile_templates = PROFILE_GUIDANCE_TEMPLATES.get(officer_profile, {})
        profile_lang_templates = profile_templates.get(lang, profile_templates.get("en", {}))

        # §162 F2: Build profile-aware guidance
        profile_intro = profile_lang_templates.get("intro", "")
        profile_focus = profile_lang_templates.get("focus", "")
        profile_action = profile_lang_templates.get("action", "")

        if level == "tutorial":
            # Detailed step-by-step with profile context
            guidance = ""
            if profile_intro:
                guidance = f"{profile_intro}\n\n"
            guidance += f"{vera_intro}\n\n"
            if profile_focus:
                guidance += f"{profile_focus}\n\n"
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
            # Briefing (default) with profile context
            if profile_intro:
                guidance = f"{profile_intro}\n\n{vera_intro}"
            else:
                guidance = vera_intro

        # Get vera_tip if action specified
        vera_tip = None
        if action_id:
            action = self._find_action(module, action_id)
            if action:
                vera_tip = self._get_text(action.get("vera_tip", ""), lang)

        # §162 F2: Profile-aware next steps
        next_module = module.get("next_module")
        next_steps = []
        if next_module:
            next_mod_data = self.module_map.get_module(next_module)
            if next_mod_data:
                step_text = f"{profile_action} {next_mod_data.get('label', next_module)}" if profile_action else f"Próximo módulo: {next_mod_data.get('label', next_module)}"
                next_steps.append(step_text)

        # §162 F2: Profile context for response
        profile_context = None
        profile_focus_areas = None
        if officer_profile and officer_profile in PROFILE_GUIDANCE_TEMPLATES:
            profile_context = {
                "profile_id": officer_profile,
                "vera_tone": {
                    "digital_risk": "compliance",
                    "tech_product": "technical",
                    "internal_auditor": "audit",
                }.get(officer_profile, "general"),
            }
            profile_focus_areas = {
                "digital_risk": ["legal_anchors", "frameworks", "audit_evidence"],
                "tech_product": ["integration", "api_workflow", "system_design"],
                "internal_auditor": ["verification", "ledger_queries", "sha256_proof"],
            }.get(officer_profile, [])

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
            profile_context=profile_context,
            profile_focus=profile_focus_areas,
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
        officer_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Answer a freeform question by identifying relevant modules.
        R10: VERA nunca deixa o utilizador sem resposta.
        §162 F2: Prioritizes modules relevant to officer profile.
        """
        question_lower = question.lower()

        # §162 F2: Get profile-preferred modules for boosting
        profile_preferred = {
            "digital_risk": ["pho", "lod2", "legal_advisory", "rep"],
            "tech_product": ["obs_engine", "lod1", "doc_gen", "invoice_gen"],
            "internal_auditor": ["pho", "rep", "obs_engine", "lod2"],
        }.get(officer_profile, [])

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

            # §162 F2: Boost score for profile-preferred modules
            if mod_id in profile_preferred:
                score += 2  # Slight boost for profile relevance

            if score > 0:
                relevance.append((mod_id, mod_data, score))

        # Sort by relevance
        relevance.sort(key=lambda x: x[2], reverse=True)

        # §162 F2: Get profile-specific templates
        profile_templates = PROFILE_GUIDANCE_TEMPLATES.get(officer_profile, {})
        profile_lang_templates = profile_templates.get(lang, profile_templates.get("en", {}))
        profile_intro = profile_lang_templates.get("intro", "")

        if relevance:
            top_mod_id, top_mod, _ = relevance[0]
            vera_intro = self._get_text(top_mod.get("vera_intro", ""), lang)
            legal_anchors = top_mod.get("legal_anchors", [])

            # §162 F2: Prepend profile intro if available
            if profile_intro:
                guidance = f"{profile_intro}\n\n{vera_intro}"
            else:
                guidance = vera_intro

            return {
                "status": "success",
                "matched_module": top_mod_id,
                "module_label": top_mod.get("label", top_mod_id),
                "guidance": guidance,
                "legal_anchors": legal_anchors,
                "other_relevant": [m[0] for m in relevance[1:4]],
                "lang": lang,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # §162 F2: Profile context
                "profile_context": {
                    "profile_id": officer_profile,
                    "profile_preferred_modules": profile_preferred,
                } if officer_profile else None,
            }
        else:
            return {
                "status": "no_match",
                "guidance": self._get_fallback_guidance(lang, officer_profile),
                "suggested_workflow": "new_user_onboarding",
                "lang": lang,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _get_fallback_guidance(self, lang: str, officer_profile: Optional[str] = None) -> str:
        """
        §162 F2: Profile-aware fallback guidance.
        """
        # Profile-specific fallbacks
        if officer_profile == "digital_risk":
            fallbacks = {
                "pt": "Não encontrei um módulo específico. Como especialista em compliance, recomendo começares pelo PHO (Proof of Human Oversight) — garante que toda decisão AI passa por supervisão humana.",
                "de": "Ich habe kein spezifisches Modul gefunden. Als Compliance-Spezialist empfehle ich, mit PHO (Proof of Human Oversight) zu beginnen — es stellt sicher, dass jede KI-Entscheidung menschliche Aufsicht durchläuft.",
                "en": "I didn't find a specific module. As a compliance specialist, I recommend starting with PHO (Proof of Human Oversight) — it ensures every AI decision goes through human supervision.",
            }
        elif officer_profile == "tech_product":
            fallbacks = {
                "pt": "Não encontrei um módulo específico. Como owner técnico, recomendo começares pelo ObsEngine — monitoriza o sistema em tempo real e integra-se facilmente com os teus workflows.",
                "de": "Ich habe kein spezifisches Modul gefunden. Als technischer Owner empfehle ich, mit ObsEngine zu beginnen — es überwacht das System in Echtzeit und integriert sich leicht in deine Workflows.",
                "en": "I didn't find a specific module. As a technical owner, I recommend starting with ObsEngine — it monitors the system in real-time and integrates easily with your workflows.",
            }
        elif officer_profile == "internal_auditor":
            fallbacks = {
                "pt": "Não encontrei um módulo específico. Como auditor interno, recomendo começares pelo PHO — cada aprovação gera um receipt SHA-256 verificável no Ledger. Prova imediata.",
                "de": "Ich habe kein spezifisches Modul gefunden. Als interner Prüfer empfehle ich, mit PHO zu beginnen — jede Genehmigung erzeugt einen verifizierbaren SHA-256-Receipt im Ledger. Sofortiger Beweis.",
                "en": "I didn't find a specific module. As an internal auditor, I recommend starting with PHO — every approval generates a verifiable SHA-256 receipt in the Ledger. Immediate proof.",
            }
        else:
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
    from vera_did_gate import (
        verify_did, bind_action_to_did, get_wallet_banner, restore_did_context,
        get_officer_profile, set_officer_profile, adapt_guidance_to_profile,
        VALID_PROFILES,
    )

    @router.post("/ask", response_model=None)
    async def instructor_ask(req: InstructorRequest):
        """
        Main instructor endpoint.
        - If module_id provided: get module-specific guidance
        - If question provided: answer freeform question
        R10: VERA nunca deixa o utilizador sozinho.
        §162 F2: Adapts guidance to officer profile (OVS).

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
        context = await restore_did_context(req.officer_did, req.lang)

        # §162 F2: Get officer profile (from request or stored)
        officer_profile = req.officer_profile
        if not officer_profile:
            stored_profile = get_officer_profile(req.officer_did)
            if stored_profile:
                officer_profile = stored_profile.profile_id

        # Process request
        if req.module_id:
            result = instructor.get_module_guidance(
                module_id=req.module_id,
                action_id=req.action_id,
                level=req.level,
                lang=req.lang,
                officer_did=req.officer_did,
                officer_profile=officer_profile,  # §162 F2
            )
            action = f"module_guidance:{req.module_id}"
        elif req.question:
            result = instructor.answer_question(
                question=req.question,
                officer_did=req.officer_did,
                lang=req.lang,
                officer_profile=officer_profile,  # §162 F2
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
            # §162 F2: Add profile context
            result["officer_profile"] = officer_profile
            result["profile_greeting"] = context.get("profile_greeting")

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
                "engine": "VERA Instructor v1.1",
                "constitution": "REGO v1.2 · R10 + R12",
                "features": {
                    "r10_pedagogia": True,
                    "r12_mapa_vivo": True,
                    "f2_profile_aware": True,  # §162 F2
                },
                "modules_loaded": len(mm.get_all_modules()),
                "workflows_loaded": len(mm.get_all_workflows()),
                "supported_profiles": VALID_PROFILES,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    return router
