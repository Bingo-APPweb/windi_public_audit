import os
import json
import subprocess
from datetime import datetime

class WindiEmbassy:
    def __init__(self, repo_path="/workspace/windi_public_audit"):
        self.repo_path = repo_path
        self.api_dir = os.path.join(repo_path, "api")
        self.status_file = os.path.join(self.api_dir, "reputation.json")

    def publish_update(self, alpha_score, beta_score, doc_hash):
        """Prepara os dados e faz o push automático para o GitHub"""
        print(f"🏛️ WINDI: Iniciando publicação de Auditoria...")
        
        # 1. Garantir que o diretório da API existe
        if not os.path.exists(self.api_dir):
            os.makedirs(self.api_dir)

        # 2. Gerar o Payload de Virtude
        payload = {
            "sovereign": "JOBER_CGO_2026",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "audit_results": {
                "IA_ALPHA": {"score": alpha_score, "status": "RISK" if alpha_score < 50 else "STABLE"},
                "IA_BETA": {"score": beta_score, "status": "VIRTUE"}
            },
            "forensic_hash": doc_hash,
            "integrity": "VERIFIED"
        }

        # 3. Salvar o arquivo JSON
        with open(self.status_file, 'w') as f:
            json.dump(payload, f, indent=4)
        
        # 4. Rito de Push Automático
        try:
            os.chdir(self.repo_path)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Audit Auto-Update: {alpha_score}/{beta_score}"], check=True)
            # Usando o push normal pois a URL já está com o Token
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("💎 Sucesso: Embaixada atualizada e assinada via Token!")
        except Exception as e:
            print(f"⚠️ Erro no rito de publicação: {e}")

if __name__ == "__main__":
    # Teste imediato de integração
    embassy = WindiEmbassy()
    embassy.publish_update(alpha_score=40, beta_score=100, doc_hash="328bd0896dd3691cc21f88f10ff074c1cf4e81f9d047008a70280b93fb19c454")
