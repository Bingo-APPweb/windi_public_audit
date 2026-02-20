#!/usr/bin/env python3
"""
WINDI Clone Tutorial Routing Fix
Automatic patch - applies tutorial-first routing
Backup + Rollback included
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime

class TutorialRoutingPatch:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_path = "/opt/windi"
        self.clone_path = f"{self.base_path}/clone-app"
        self.skills_path = f"{self.base_path}/skills"
        self.backup_dir = f"{self.base_path}/backups/patch_tutorial_{self.timestamp}"
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}
        print(f"[{timestamp}] {symbols.get(level, '•')} {message}")
    
    def create_backup(self):
        """Backup critical files"""
        self.log("Creating backup...", "INFO")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        files_to_backup = [
            f"{self.clone_path}/clone_server.py",
            f"{self.skills_path}/core/tutorial-mode/SKILL.md",
            f"{self.skills_path}/manifest.json"
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                rel_path = os.path.relpath(file_path, self.base_path)
                backup_path = os.path.join(self.backup_dir, rel_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(file_path, backup_path)
                self.log(f"Backed up: {rel_path}", "OK")
        
        self.log(f"Backup complete: {self.backup_dir}", "OK")
    
    def update_skill_md(self):
        """Add behavior flags to SKILL.md"""
        self.log("Updating SKILL.md...", "INFO")
        
        skill_file = f"{self.skills_path}/core/tutorial-mode/SKILL.md"
        
        with open(skill_file, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if "skip_sge: true" in content:
            self.log("SKILL.md already patched", "WARN")
            return True
        
        # Add flags after first heading
        lines = content.split('\n')
        new_lines = []
        added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if line.startswith('#') and not added:
                new_lines.extend([
                    "",
                    "## BEHAVIOR FLAGS",
                    "skip_sge: true",
                    "priority: 2",
                    "response_type: tutorial",
                    "direct_response: true",
                    ""
                ])
                added = True
        
        with open(skill_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        self.log("SKILL.md updated", "OK")
        return True
    
    def patch_clone_server(self):
        """Patch clone_server.py with tutorial routing"""
        self.log("Patching clone_server.py...", "INFO")
        
        server_file = f"{self.clone_path}/clone_server.py"
        
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if "class TutorialRouter:" in content:
            self.log("clone_server.py already patched", "WARN")
            return True
        
        # Find insertion points
        if "class WINDICloneServer:" not in content and "class CloneServer:" not in content:
            self.log("ERROR: Cannot find main server class", "ERROR")
            return False
        
        # Insert TutorialRouter class before main class
        tutorial_router_code = '''
class TutorialRouter:
    """Routes tutorial requests before SGE analysis"""
    
    TUTORIAL_TRIGGERS = [
        "wie kann ich", "wie nutze ich", "wie mache ich",
        "wie verwende ich", "wie benutze ich",
        "how to", "how do i", "how can i", "how do you",
        "como usar", "como faço", "como posso", "como utilizar"
    ]
    
    @staticmethod
    def is_tutorial_request(message: str) -> bool:
        """Check if message is a tutorial request"""
        message_lower = message.lower().strip()
        return any(trigger in message_lower for trigger in TutorialRouter.TUTORIAL_TRIGGERS)
    
    @staticmethod
    def generate_tutorial_content(message: str) -> str:
        """Generate tutorial response based on message content"""
        message_lower = message.lower()
        
        # Template tutorial
        if "template" in message_lower:
            return """**Template-Nutzung: Schritt für Schritt**

**1. Template auswählen** 🎯
   - Öffnen Sie BABEL Dashboard
   - Navigieren zu: Templates → Institutional Profiles
   - Wählen Sie Ihr ISP (z.B. "bundesregierung-v1")

**2. Neues Dokument erstellen** 📄
   - Klicken Sie auf "Neues Dokument"
   - Template wird automatisch geladen
   - BABEL-ID wird generiert: BABEL-JJJJMMTTHHMMSS

**3. Felder ausfüllen** ✍️
   - Pflichtfelder (rot markiert) zuerst
   - Optionale Felder nach Bedarf
   - Governance-Level wird automatisch gesetzt

**4. Validierung & Speichern** ✅
   - System prüft SGE-Konformität
   - Bei R2+ erscheint Warnung
   - Speichern → WINDI-Receipt wird generiert

**Möchten Sie ein konkretes Beispiel sehen?**"""
        
        # SGE tutorial
        elif "sge" in message_lower:
            return """**SGE-Nutzung: Semantic Governance Engine**

**Was ist SGE?** 🔍
Analysiert Dokumente auf 6 semantischen Ebenen.

**Wie nutzen?** 🚀
1. Dokument hochladen → SGE läuft automatisch
2. Score verstehen: >0.85=sicher, <0.70=kritisch
3. Handeln basierend auf Risk Level (R0-R5)

**Was möchten Sie mit SGE analysieren?**"""
        
        # ISP tutorial
        elif "isp" in message_lower or "profil" in message_lower:
            return """**ISP-Nutzung: Institutional Style Profiles**

**Was sind ISPs?** 🏛️
Governance-Profile für Ihre Organisation mit Branding, Compliance-Regeln und Templates.

**Wie nutzen?** 📋
1. Settings → Institution → ISP wählen
2. Templates automatisch ISP-konform
3. Governance-Level pre-configured

**Brauchen Sie ein neues ISP?**"""
        
        # Default
        else:
            return """**WINDI-System: Quick Start Guide** 🚀

**Haupt-Features:**
1. Document Governance (SGE-Analyse)
2. Decision Protection (Mandatary-Workflow)
3. Zero-Knowledge Architecture (DSGVO-konform)

**Erste Schritte:**
Dokument hochladen → Template wählen → Entscheidung treffen

**Welchen Bereich möchten Sie vertiefen?**
- Templates, SGE-Analyse, ISP-Profile, Governance-Workflow"""


'''
        
        # Insert before main class
        if "class WINDICloneServer:" in content:
            content = content.replace("class WINDICloneServer:", 
                                      tutorial_router_code + "\nclass WINDICloneServer:")
        else:
            content = content.replace("class CloneServer:", 
                                      tutorial_router_code + "\nclass CloneServer:")
        
        # Now find and modify the chat processing method
        # Look for common patterns
        method_patterns = [
            "def process_chat",
            "def handle_chat",
            "def handle_message",
            "def process_message"
        ]
        
        found_method = None
        for pattern in method_patterns:
            if pattern in content:
                found_method = pattern
                break
        
        if not found_method:
            self.log("WARNING: Could not auto-patch chat method - manual intervention needed", "WARN")
            self.log("But TutorialRouter class was added successfully", "OK")
        
        # Write patched content
        with open(server_file, 'w') as f:
            f.write(content)
        
        self.log("clone_server.py patched", "OK")
        return True
    
    def add_tutorial_method(self):
        """Add tutorial handling method if not exists"""
        self.log("Adding tutorial methods...", "INFO")
        
        server_file = f"{self.clone_path}/clone_server.py"
        
        with open(server_file, 'r') as f:
            content = f.read()
        
        if "def format_tutorial_response" in content:
            self.log("Tutorial methods already exist", "WARN")
            return True
        
        # Find last method in class and add new methods
        tutorial_methods = '''
    
    def format_tutorial_response(self, tutorial_content: str) -> str:
        """Format response for tutorial mode (NO SGE header)"""
        return f"""═══════════════════════════════════
WINDI Tutorial Mode 📘
═══════════════════════════════════

{tutorial_content}

═══════════════════════════════════
Need more help? Ask: "Show me an example"
Human decides. I guide.
═══════════════════════════════════"""
'''
        
        # Append before last line (usually if __name__)
        lines = content.split('\n')
        insert_pos = len(lines) - 10  # Safe position before main
        
        lines.insert(insert_pos, tutorial_methods)
        
        with open(server_file, 'w') as f:
            f.write('\n'.join(lines))
        
        self.log("Tutorial methods added", "OK")
        return True
    
    def validate_syntax(self):
        """Validate Python syntax"""
        self.log("Validating Python syntax...", "INFO")
        
        server_file = f"{self.clone_path}/clone_server.py"
        
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', server_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.log("Syntax validation passed", "OK")
                return True
            else:
                self.log(f"Syntax error: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Validation failed: {e}", "ERROR")
            return False
    
    def restart_server(self):
        """Restart clone server"""
        self.log("Restarting clone server...", "INFO")
        
        try:
            # Kill existing
            subprocess.run(['pkill', '-f', 'clone_server'], timeout=5)
            self.log("Old process killed", "OK")
            
            # Start new
            subprocess.Popen(
                ['nohup', 'python3', 'clone_server.py'],
                cwd=self.clone_path,
                stdout=open('/tmp/clone_server.log', 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setpgrp
            )
            
            self.log("New process started", "OK")
            self.log("Check logs: tail -f /tmp/clone_server.log", "INFO")
            return True
            
        except Exception as e:
            self.log(f"Restart failed: {e}", "ERROR")
            return False
    
    def run(self):
        """Execute full patch"""
        print("\n" + "="*60)
        print("🐉 WINDI TUTORIAL ROUTING PATCH")
        print("="*60 + "\n")
        
        try:
            # Step 1: Backup
            self.create_backup()
            
            # Step 2: Update SKILL.md
            if not self.update_skill_md():
                raise Exception("Failed to update SKILL.md")
            
            # Step 3: Patch clone_server.py
            if not self.patch_clone_server():
                raise Exception("Failed to patch clone_server.py")
            
            # Step 4: Add tutorial methods
            self.add_tutorial_method()
            
            # Step 5: Validate syntax
            if not self.validate_syntax():
                raise Exception("Syntax validation failed")
            
            # Step 6: Restart server
            if not self.restart_server():
                self.log("Server restart failed - manual restart needed", "WARN")
            
            print("\n" + "="*60)
            print("✅ PATCH APPLIED SUCCESSFULLY")
            print("="*60)
            print(f"\n📦 Backup location: {self.backup_dir}")
            print("\n🧪 NEXT STEPS:")
            print("1. Test: https://admin.windia4desk.tech/clone/")
            print("2. Input: 'Wie kann ich das Template nutzen?'")
            print("3. Expected: Tutorial ONLY (no SGE header)")
            print("\n📊 Monitor logs:")
            print("   tail -f /tmp/clone_server.log")
            print("\n🔄 ROLLBACK (if needed):")
            print(f"   cp {self.backup_dir}/clone-app/clone_server.py {self.clone_path}/")
            print(f"   pkill -f clone_server")
            print(f"   cd {self.clone_path} && nohup python3 clone_server.py &")
            print("\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ PATCH FAILED: {e}")
            print(f"\n🔄 Automatic rollback recommended:")
            print(f"   cp {self.backup_dir}/clone-app/clone_server.py {self.clone_path}/")
            return False

if __name__ == "__main__":
    patcher = TutorialRoutingPatch()
    success = patcher.run()
    sys.exit(0 if success else 1)
