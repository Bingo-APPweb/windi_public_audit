#!/usr/bin/env python3
"""
Add Human-Only Registration Modal (Onboarding)
"""

FILE = "/opt/windi/a4desk-editor/a4desk_tiptap_babel.py"

with open(FILE, 'r') as f:
    content = f.read()

# 1. Add CSS for modal
modal_css = '''
        /* ============================================
           HUMAN-ONLY REGISTRATION MODAL
           ============================================ */
        .onboarding-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .onboarding-modal {
            background: white;
            border-radius: 16px;
            padding: 32px;
            max-width: 480px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .onboarding-header {
            text-align: center;
            margin-bottom: 24px;
        }
        .onboarding-header .icon {
            font-size: 48px;
            margin-bottom: 12px;
        }
        .onboarding-header h2 {
            color: #1e293b;
            margin: 0 0 8px 0;
        }
        .onboarding-header p {
            color: #64748b;
            margin: 0;
            font-size: 0.9rem;
        }
        .human-only-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, #059669, #0d9488);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 16px;
        }
        .onboarding-form label {
            display: block;
            font-weight: 600;
            color: #374151;
            margin-bottom: 6px;
            font-size: 0.9rem;
        }
        .onboarding-form input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1rem;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        .onboarding-form input:focus {
            outline: none;
            border-color: #0d9488;
        }
        .onboarding-principle {
            background: #f0fdf4;
            border: 1px dashed #059669;
            border-radius: 8px;
            padding: 12px;
            margin: 16px 0;
            text-align: center;
            font-size: 0.85rem;
            color: #166534;
        }
        .onboarding-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #0d9488, #059669);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .onboarding-btn:hover {
            transform: translateY(-2px);
        }
        .onboarding-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .settings-indicator {
            position: fixed;
            top: 80px;
            right: 20px;
            background: #3b82f6;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            display: none;
            animation: pulse 2s infinite;
            z-index: 100;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
'''

# Insert CSS before the settings-panel CSS
if '.onboarding-overlay' not in content:
    content = content.replace(
        '/* ============================================\n           PANEL DIREITO - Colapsável (Settings)',
        modal_css + '\n        /* ============================================\n           PANEL DIREITO - Colapsável (Settings)'
    )
    print("✅ Added modal CSS")

# 2. Add modal HTML after body tag
modal_html = '''
    <!-- Human-Only Registration Modal -->
    <div class="onboarding-overlay" id="onboardingModal" style="display: none;">
        <div class="onboarding-modal">
            <div class="onboarding-header">
                <div class="icon">🏛️</div>
                <div class="human-only-badge">
                    <i class="fas fa-user-shield"></i>
                    <span data-t="human_only">Human Only</span>
                </div>
                <h2 data-t="welcome_title">Welcome to WINDI</h2>
                <p data-t="welcome_desc">Please register your identity. These fields can only be filled by humans.</p>
            </div>
            <form class="onboarding-form" onsubmit="saveHumanIdentity(event)">
                <label data-t="your_name">Your Name *</label>
                <input type="text" id="onboardingName" required placeholder="Max Mustermann">
                
                <label data-t="your_role">Your Role / Title</label>
                <input type="text" id="onboardingRole" placeholder="Sachbearbeiter">
                
                <label data-t="your_dept">Department</label>
                <input type="text" id="onboardingDept" placeholder="Bauamt">
                
                <div class="onboarding-principle">
                    🔒 <span data-t="principle">KI verarbeitet. Mensch entscheidet. WINDI garantiert.</span>
                </div>
                
                <button type="submit" class="onboarding-btn" data-t="start_working">
                    <i class="fas fa-check"></i> Start Working
                </button>
            </form>
        </div>
    </div>
    
    <!-- Settings indicator tooltip -->
    <div class="settings-indicator" id="settingsIndicator">
        ⚙️ <span data-t="settings_hint">Your profile is in Settings</span> →
    </div>

'''

# Find the body tag and insert after first main div
if 'onboardingModal' not in content:
    # Insert before the closing </body>
    content = content.replace(
        '</body>\n</html>"""',
        modal_html + '</body>\n</html>"""'
    )
    print("✅ Added modal HTML")

# 3. Add JavaScript for modal logic
modal_js = '''
// ============================================
// HUMAN-ONLY REGISTRATION (ONBOARDING)
// ============================================
const ONBOARDING_TRANSLATIONS = {
    de: {
        welcome_title: 'Willkommen bei WINDI',
        welcome_desc: 'Bitte registrieren Sie Ihre Identität. Diese Felder können nur von Menschen ausgefüllt werden.',
        your_name: 'Ihr Name *',
        your_role: 'Ihre Rolle / Titel',
        your_dept: 'Abteilung',
        start_working: 'Arbeiten beginnen',
        settings_hint: 'Ihr Profil ist in Einstellungen'
    },
    en: {
        welcome_title: 'Welcome to WINDI',
        welcome_desc: 'Please register your identity. These fields can only be filled by humans.',
        your_name: 'Your Name *',
        your_role: 'Your Role / Title',
        your_dept: 'Department',
        start_working: 'Start Working',
        settings_hint: 'Your profile is in Settings'
    },
    pt: {
        welcome_title: 'Bem-vindo ao WINDI',
        welcome_desc: 'Por favor registre sua identidade. Estes campos só podem ser preenchidos por humanos.',
        your_name: 'Seu Nome *',
        your_role: 'Seu Cargo / Título',
        your_dept: 'Departamento',
        start_working: 'Começar a Trabalhar',
        settings_hint: 'Seu perfil está em Configurações'
    }
};

function checkOnboarding() {
    const humanIdentity = localStorage.getItem('windi_human_identity');
    if (!humanIdentity) {
        document.getElementById('onboardingModal').style.display = 'flex';
        applyOnboardingTranslations();
    } else {
        // Load saved identity into fields
        const identity = JSON.parse(humanIdentity);
        document.getElementById('fieldAuthor').value = identity.name || '';
    }
}

function applyOnboardingTranslations() {
    const t = ONBOARDING_TRANSLATIONS[currentLang] || ONBOARDING_TRANSLATIONS['en'];
    document.querySelectorAll('#onboardingModal [data-t]').forEach(el => {
        const key = el.dataset.t;
        if (t[key]) el.textContent = t[key];
    });
}

function saveHumanIdentity(event) {
    event.preventDefault();
    
    const identity = {
        name: document.getElementById('onboardingName').value,
        role: document.getElementById('onboardingRole').value,
        department: document.getElementById('onboardingDept').value,
        registeredAt: new Date().toISOString(),
        isHuman: true
    };
    
    localStorage.setItem('windi_human_identity', JSON.stringify(identity));
    
    // Apply to current document fields
    document.getElementById('fieldAuthor').value = identity.name;
    
    // Close modal
    document.getElementById('onboardingModal').style.display = 'none';
    
    // Show settings indicator briefly
    const indicator = document.getElementById('settingsIndicator');
    indicator.style.display = 'block';
    setTimeout(() => { indicator.style.display = 'none'; }, 5000);
}

function resetHumanIdentity() {
    if (confirm('Reset your Human-Only registration?')) {
        localStorage.removeItem('windi_human_identity');
        location.reload();
    }
}

// Check onboarding on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(checkOnboarding, 500);
});

'''

# Insert JS before the closing script tag
if 'checkOnboarding' not in content:
    content = content.replace(
        'return render_template_string(BABEL_HTML)',
        modal_js + '\nreturn render_template_string(BABEL_HTML)'
    )
    print("✅ Added modal JavaScript")

with open(FILE, 'w') as f:
    f.write(content)

# Validate
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', FILE], capture_output=True)
if result.returncode == 0:
    print("✅ Syntax OK")
else:
    print(f"❌ Syntax ERROR: {result.stderr.decode()}")

print("Done!")
