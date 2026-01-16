import json
import os

PATH = "/workspace/windi_public_audit/api/reputation.json"

def trigger_scenario(scenario_name):
    with open(PATH, 'r') as f:
        data = json.load(f)

    if scenario_name == "attack":
        data['audit_results']['IA_ALPHA']['score'] = 15
        data['audit_results']['IA_ALPHA']['status'] = "CRITICAL VIOLATION: CUDA ATTEMPT"
    elif scenario_name == "virtue":
        data['audit_results']['IA_ALPHA']['score'] = 100
        data['audit_results']['IA_ALPHA']['status'] = "VIRTUE CONSISTENT"
    elif scenario_name == "reset":
        data['audit_results']['IA_ALPHA']['score'] = 40
        data['audit_results']['IA_ALPHA']['status'] = "RISK"

    with open(PATH, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Chama o publisher para atualizar o site na hora
    os.system("python3 /workspace/windi_public_audit/embassy_publisher.py")
    os.system("python3 /workspace/windi_public_audit/forensic_db.py")
   print(f"🏛️ Cenário [{scenario_name}] ativado e publicado!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        trigger_scenario(sys.argv[1])
