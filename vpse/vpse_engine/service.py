"""
VPSE · HTTP Service (FastAPI)
=============================
READ-ONLY por construção:
  - não escreve no Ledger
  - não emite selo
  - não presume DID
  - receipt-candidate só em memória, MORTO (Regra Canónica 3)

Porta: NÃO hardcoded. Lida de env VPSE_PORT.
  GOLDEN RULE: porta final é decisão do Human Dragon (I9) após
  verificação no Strato. Default 8120 é APENAS placeholder [estimado].

Run local:
  VPSE_PORT=8120 uvicorn vpse_engine.service:app --host 127.0.0.1 --port 8120
"""
import os
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .pipeline import run_vpse
from . import __version__

app = FastAPI(
    title="VPSE — Viability Pre-Screen Engine",
    description="Pre-HIOS, pre-DID. Pre-Screen, não veredicto. WINDI Playground P0.",
    version=__version__,
)


class VPSERequest(BaseModel):
    idea: str = Field(..., description="Descrição da ideia de produto/serviço/sistema")
    context: str = Field("", description="Background opcional")
    target_domain: str = Field("", description="Domínio alvo opcional")
    jurisdiction: str = Field("", description="Jurisdição opcional")
    desired_output: str = Field("unknown",
        description="prototype | report | app | service | research | unknown")
    emit_receipt_candidate: bool = Field(False,
        description="Emite receipt-candidate MORTO (unsealed, ledger_eligible=false)")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "engine": "VPSE",
        "version": __version__,
        "pre_did_pre_hios": True,
        "writes_to_ledger": False,
        "presumes_did": False,
    }


@app.get("/doctrine")
def doctrine():
    return {
        "name": "Viability Pre-Screen Engine",
        "principle": "Pre-Screen, não veredicto.",
        "method": "A memória propõe, a fonte dispõe, o Humano decide.",
        "i9": "Autoridade de decisão é humana.",
        "canonical_rules": [
            "1. Todo output carrega proveniência [lido]/[estimado]/[nao_verificado].",
            "2. Riscos e compliance questions nunca saem como verdade nua.",
            "3. Receipt-candidate é artefacto local morto (unsealed, ledger_eligible=false).",
            "4. Pré-HIOS e pré-DID — só vira candidato a Ledger via /farm/claim com DID válido.",
        ],
        "non_goals": [
            "não gera código de produção como primeira resposta",
            "não promete certeza legal",
            "não certifica compliance automaticamente",
            "não substitui autoridade humana",
            "não bypassa governança HIOS",
            "não trata ideia atraente como produto validado",
        ],
    }


@app.post("/prescreen")
def prescreen(req: VPSERequest):
    report = run_vpse(
        idea=req.idea,
        context=req.context,
        target_domain=req.target_domain,
        jurisdiction=req.jurisdiction,
        desired_output=req.desired_output,
        emit_receipt_candidate=req.emit_receipt_candidate,
    )
    if "error" in report:
        return JSONResponse(status_code=422, content=report)
    return report


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("VPSE_PORT", "8120"))  # placeholder — confirmar no Strato
    uvicorn.run(app, host="127.0.0.1", port=port)
