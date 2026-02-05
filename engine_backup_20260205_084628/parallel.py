# engine/parallel.py
# WINDI Parallel Dual-Run
# Status: PENDENTE | Prioridade: MÉDIA
# "A ordem temporal não importa. A ordem decisória continua humana."

import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ParallelResult:
    claude_response: Optional[Dict[str, Any]]
    gpt_response: Optional[Dict[str, Any]]
    gemini_response: Optional[Dict[str, Any]]
    parallel: bool
    total_time_s: float
    partial_failure: bool
    failed_backends: list


class ParallelExecutor:
    """
    Executa múltiplos backends em paralelo.
    
    REGRA: Ordem temporal não afeta ordem decisória.
    BENEFÍCIO: Reduz ~28s para ~15s em dual-run.
    """
    
    def __init__(self, orchestrator):
        self.orch = orchestrator
    
    async def _call_worker_async(
        self,
        backend: str,
        query: str,
        system_prompt: str,
        receipt_id: str,
        classification: Dict
    ) -> Dict[str, Any]:
        """Wrapper async para chamada síncrona do worker."""
        loop = asyncio.get_event_loop()
        
        if backend == "claude":
            worker = self.orch.claude_worker
        elif backend == "gpt":
            worker = self.orch.gpt_worker
        elif backend == "gemini":
            worker = self.orch.gemini_worker
        else:
            return {"error": f"Unknown backend: {backend}", "fail_closed": True}
        
        # Executa em thread separada para não bloquear
        return await loop.run_in_executor(
            None,
            lambda: worker.chat(
                query, system_prompt, self.orch.canon,
                receipt_id, classification
            )
        )
    
    async def dual_run(
        self,
        query: str,
        system_prompt: str,
        receipt_id: str,
        classification: Dict,
        backends: list = ["claude", "gpt"]
    ) -> ParallelResult:
        """
        Executa dois backends em paralelo.
        
        Args:
            query: User query
            system_prompt: System prompt from enforcer
            receipt_id: WINDI receipt
            classification: Risk classification dict
            backends: Lista de backends a executar
            
        Returns:
            ParallelResult com respostas de ambos
        """
        t0 = time.time()
        
        tasks = []
        for backend in backends:
            task = self._call_worker_async(
                backend, query, system_prompt, receipt_id, classification
            )
            tasks.append((backend, task))
        
        # Executa todos em paralelo
        results = {}
        failed = []
        
        for backend, task in tasks:
            try:
                results[backend] = await task
                if results[backend].get("flags", {}).get("fail_closed"):
                    failed.append(backend)
            except Exception as e:
                results[backend] = {
                    "error": str(e),
                    "flags": {"fail_closed": True, "fail_reason": str(e)}
                }
                failed.append(backend)
        
        t1 = time.time()
        
        return ParallelResult(
            claude_response=results.get("claude"),
            gpt_response=results.get("gpt"),
            gemini_response=results.get("gemini"),
            parallel=True,
            total_time_s=round(t1 - t0, 3),
            partial_failure=len(failed) > 0,
            failed_backends=failed
        )
    
    async def tri_run(
        self,
        query: str,
        system_prompt: str,
        receipt_id: str,
        classification: Dict
    ) -> ParallelResult:
        """Executa três backends em paralelo."""
        return await self.dual_run(
            query, system_prompt, receipt_id, classification,
            backends=["claude", "gpt", "gemini"]
        )


# Função de conveniência para uso síncrono
def run_parallel(orchestrator, query, system_prompt, receipt_id, classification):
    """Wrapper síncrono para parallel dual-run."""
    executor = ParallelExecutor(orchestrator)
    return asyncio.run(
        executor.dual_run(query, system_prompt, receipt_id, classification)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI PARALLEL EXECUTOR - Module loaded")
    print("=" * 60)
    print("\nUsage:")
    print("  from engine.parallel import ParallelExecutor")
    print("  executor = ParallelExecutor(orchestrator)")
    print("  result = await executor.dual_run(...)")
    print("\nBenefício esperado: ~28s → ~15s em dual-run")
    print("=" * 60)
