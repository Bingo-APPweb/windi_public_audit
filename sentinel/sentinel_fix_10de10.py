#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  WINDI SENTINEL — Fix Cirúrgico + Expansão do Radar             ║
║  "O Sentinel procurava a alma no lugar errado."                  ║
║                                                                  ║
║  Fixes:                                                          ║
║    1. Governance health check: /health → /api/status             ║
║    2. Adiciona Forensic (:8094) ao monitoramento                 ║
║    3. Adiciona Wallet (:8099) ao monitoramento                   ║
║                                                                  ║
║  Run: python3 sentinel_fix_10de10.py                             ║
║  Then: sudo systemctl restart windi-sentinel                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import shutil
from datetime import datetime

SENTINEL_FILE = "/opt/windi/sentinel/windi_sentinel.py"
BACKUP_DIR = "/opt/windi/backups"

def backup_sentinel():
    """Backup before surgery — always."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_dir = os.path.join(BACKUP_DIR, f"pre_sentinel_fix_{ts}")
    os.makedirs(bk_dir, exist_ok=True)
    dest = os.path.join(bk_dir, "windi_sentinel.py")
    shutil.copy2(SENTINEL_FILE, dest)
    print(f"  ✅ Backup: {dest}")
    return bk_dir


def read_sentinel():
    with open(SENTINEL_FILE, "r") as f:
        return f.read()


def write_sentinel(content):
    with open(SENTINEL_FILE, "w") as f:
        f.write(content)


def fix_governance_health_check(content):
    """
    Fix 1: O Sentinel verifica /health na Governance API,
    mas o endpoint real é /api/status.
    
    Procura a configuração do windi-governance e muda o health_endpoint.
    """
    # Strategy: find the governance service config and fix the endpoint
    # The config uses "health_endpoint" or checks against /health
    
    fixes_applied = 0
    
    # Pattern 1: Direct health_endpoint config
    if '"health_endpoint": "/health"' in content:
        # Find governance-specific occurrence
        # We need to be surgical — only change governance, not all services
        lines = content.split('\n')
        in_governance = False
        new_lines = []
        
        for i, line in enumerate(lines):
            if 'windi-governance' in line or '"governance"' in line:
                in_governance = True
            
            if in_governance and '"health_endpoint": "/health"' in line:
                line = line.replace('"health_endpoint": "/health"', '"health_endpoint": "/api/status"')
                in_governance = False
                fixes_applied += 1
                print(f"  ✅ Fix 1a: Governance health_endpoint → /api/status (line ~{i+1})")
            
            # Reset context after moving past the service block
            if in_governance and line.strip() == '},' :
                in_governance = False
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # Pattern 2: URL-based check like http://localhost:8080/health
    old_gov_url = "http://localhost:8080/health"
    new_gov_url = "http://localhost:8080/api/status"
    if old_gov_url in content:
        content = content.replace(old_gov_url, new_gov_url)
        fixes_applied += 1
        print(f"  ✅ Fix 1b: Governance URL → {new_gov_url}")
    
    # Pattern 3: Check path in service definition dict
    old_path = '"url": "http://127.0.0.1:8080/health"'
    new_path = '"url": "http://127.0.0.1:8080/api/status"'
    if old_path in content:
        content = content.replace(old_path, new_path)
        fixes_applied += 1
        print(f"  ✅ Fix 1c: Governance check URL → /api/status")

    # Pattern 4: Generic path association with port 8080
    # Look for the SERVICE_CHECKS or SERVICES dict
    if fixes_applied == 0:
        # More aggressive search — find any /health associated with 8080
        import re
        # Find blocks that mention 8080 and /health nearby
        pattern = r'(8080[^}]*?)/health'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(
                r'(8080[^}]*?)/health',
                r'\1/api/status',
                content,
                count=1
            )
            fixes_applied += 1
            print(f"  ✅ Fix 1d: Governance check path → /api/status (regex)")
    
    if fixes_applied == 0:
        print(f"  ⚠️  Fix 1: Could not locate governance health check path")
        print(f"      Manual fix needed: change :8080 check from /health to /api/status")
    
    return content


def add_forensic_to_monitor(content):
    """
    Fix 2: Adicionar Forensic (:8094) ao monitoramento do Sentinel.
    """
    if "8094" in content and "forensic" in content.lower():
        print(f"  ℹ️  Fix 2: Forensic (:8094) já está no Sentinel config")
        return content
    
    # Find the services dict and add forensic
    # Look for the last service entry before the closing of the dict
    forensic_config = '''
        "windi-forensic": {
            "port": 8094,
            "url": "http://127.0.0.1:8094/health",
            "expected_status": [200],
            "critical": false,
            "description": "Forensic validation and ledger API",
            "systemd_name": "windi-forensic"
        },'''
    
    # Try to insert after the last known service (bridge at 8097)
    if '"windi-bridge"' in content or '"bridge"' in content:
        # Find the bridge block end and insert after
        lines = content.split('\n')
        new_lines = []
        bridge_found = False
        brace_count = 0
        inserted = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            if ('windi-bridge' in line or '"bridge"' in line) and not bridge_found:
                bridge_found = True
                brace_count = 0
            
            if bridge_found and not inserted:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and '}' in line:
                    # End of bridge block — insert forensic after
                    for fl in forensic_config.strip().split('\n'):
                        new_lines.append(fl)
                    inserted = True
                    print(f"  ✅ Fix 2: Forensic (:8094) adicionado ao monitoramento")
        
        if inserted:
            content = '\n'.join(new_lines)
        else:
            print(f"  ⚠️  Fix 2: Could not auto-insert forensic — manual add needed")
    
    return content


def add_wallet_to_monitor(content):
    """
    Fix 3: Adicionar Wallet (:8099) ao monitoramento do Sentinel.
    """
    if "8099" in content and "wallet" in content.lower():
        print(f"  ℹ️  Fix 3: Wallet (:8099) já está no Sentinel config")
        return content
    
    wallet_config = '''
        "windi-wallet": {
            "port": 8099,
            "url": "http://127.0.0.1:8099/api/wallet/health",
            "expected_status": [200],
            "critical": false,
            "description": "Sovereign Identity Wallet — O Espelho",
            "systemd_name": "windi-wallet"
        },'''
    
    # Same insertion strategy as forensic
    if '"windi-forensic"' in content or '"forensic"' in content:
        target = '"windi-forensic"'
    elif '"windi-bridge"' in content or '"bridge"' in content:
        target = '"windi-bridge"' if '"windi-bridge"' in content else '"bridge"'
    else:
        print(f"  ⚠️  Fix 3: Could not find insertion point for wallet")
        return content
    
    lines = content.split('\n')
    new_lines = []
    target_found = False
    brace_count = 0
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        if target in line and not target_found:
            target_found = True
            brace_count = 0
        
        if target_found and not inserted:
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0 and '}' in line:
                for wl in wallet_config.strip().split('\n'):
                    new_lines.append(wl)
                inserted = True
                print(f"  ✅ Fix 3: Wallet (:8099) adicionado ao monitoramento")
    
    if inserted:
        content = '\n'.join(new_lines)
    else:
        print(f"  ⚠️  Fix 3: Could not auto-insert wallet — manual add needed")
    
    return content


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  WINDI SENTINEL — Fix Cirúrgico                                ║")
    print("║  De 8/9 para 10/10 — completando a visão                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Pre-flight
    if not os.path.exists(SENTINEL_FILE):
        print(f"  ❌ Sentinel não encontrado: {SENTINEL_FILE}")
        sys.exit(1)
    
    print("── Step 1: Backup ──")
    bk = backup_sentinel()
    print()
    
    print("── Step 2: Reading Sentinel ──")
    content = read_sentinel()
    original_len = len(content)
    print(f"  ✅ {original_len} chars loaded")
    print()
    
    print("── Step 3: Fix Governance health check ──")
    content = fix_governance_health_check(content)
    print()
    
    print("── Step 4: Add Forensic to radar ──")
    content = add_forensic_to_monitor(content)
    print()
    
    print("── Step 5: Add Wallet to radar ──")
    content = add_wallet_to_monitor(content)
    print()
    
    print("── Step 6: Write fixed Sentinel ──")
    write_sentinel(content)
    new_len = len(content)
    print(f"  ✅ Written: {new_len} chars (delta: +{new_len - original_len})")
    print()
    
    print("══════════════════════════════════════════════════════════════════")
    print("  PRÓXIMOS PASSOS:")
    print("  1. sudo systemctl restart windi-sentinel")
    print("  2. sleep 65")
    print("  3. tail -20 /opt/windi/logs/sentinel.log")
    print("  4. curl -s http://localhost:8098/api/status | python3 -m json.tool")
    print("══════════════════════════════════════════════════════════════════")
    print()
    print("  🐉 'O Sentinel agora vê com olhos completos.'")
    print()


if __name__ == "__main__":
    main()
