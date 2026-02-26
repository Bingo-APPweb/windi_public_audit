// ═══════════════════════════════════════════════════════════════════════
// WINDI THREE DRAGONS PROTOCOL v1.0.0
// Guardian | Architect | Witness
// ═══════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  const DRAGONS = {
    guardian: {
      emoji: '🛡️',
      name: { de: 'Guardian', en: 'Guardian', pt: 'Guardião' },
      role: {
        de: 'Schutz & Ethik',
        en: 'Protection & Ethics',
        pt: 'Proteção & Ética'
      },
      color: '#2D5016',
      description: {
        de: 'Wächter der Governance. Prüft Risiken und ethische Aspekte.',
        en: 'Guardian of governance. Checks risks and ethical aspects.',
        pt: 'Guardião da governança. Verifica riscos e aspectos éticos.'
      }
    },
    architect: {
      emoji: '🏗️',
      name: { de: 'Architect', en: 'Architect', pt: 'Arquiteto' },
      role: {
        de: 'Struktur & Aufbau',
        en: 'Structure & Build',
        pt: 'Estrutura & Construção'
      },
      color: '#4A3728',
      description: {
        de: 'Strukturiert und baut. Erstellt Dokumente und Templates.',
        en: 'Structures and builds. Creates documents and templates.',
        pt: 'Estrutura e constrói. Cria documentos e templates.'
      }
    },
    witness: {
      emoji: '👁️',
      name: { de: 'Witness', en: 'Witness', pt: 'Testemunha' },
      role: {
        de: 'Beobachtung & Validierung',
        en: 'Observation & Validation',
        pt: 'Observação & Validação'
      },
      color: '#1E3A5F',
      description: {
        de: 'Beobachtet und validiert. Prüft Integrität und Audit.',
        en: 'Observes and validates. Checks integrity and audit.',
        pt: 'Observa e valida. Verifica integridade e auditoria.'
      }
    }
  };

  // Dragon routing based on message content
  function routeDragon(message) {
    const t = message.toLowerCase();

    // Guardian triggers: risk, compliance, ethics, approval
    const guardianPatterns = [
      /risk|risiko|risco/i,
      /compliance|konform|conformidade/i,
      /ethik|ethics|ética/i,
      /approve|genehmig|aprovar/i,
      /gdpr|dsgvo|lgpd/i,
      /security|sicherheit|segurança/i
    ];

    // Architect triggers: create, build, document, template
    const architectPatterns = [
      /create|erstell|cria/i,
      /build|bau|construir/i,
      /document|dokument|documento/i,
      /template|vorlage|modelo/i,
      /write|schreib|escreve/i,
      /generate|generier|gerar/i
    ];

    // Witness triggers: verify, audit, check, proof
    const witnessPatterns = [
      /verify|verifizier|verificar/i,
      /audit|prüf|auditar/i,
      /check|überprüf|checar/i,
      /proof|beweis|prova/i,
      /integrity|integrität|integridade/i,
      /seal|siegel|selo/i
    ];

    let scores = { guardian: 0, architect: 0, witness: 0 };

    guardianPatterns.forEach(p => { if (p.test(t)) scores.guardian += 1; });
    architectPatterns.forEach(p => { if (p.test(t)) scores.architect += 1; });
    witnessPatterns.forEach(p => { if (p.test(t)) scores.witness += 1; });

    const sorted = Object.entries(scores).sort((a,b) => b[1] - a[1]);
    return sorted[0][1] > 0 ? sorted[0][0] : 'guardian'; // Default to guardian
  }

  // Get dragon info
  function getDragon(name) {
    return DRAGONS[name] || DRAGONS.guardian;
  }

  // Display dragon badge
  function dragonBadge(name, lang = 'de') {
    const d = getDragon(name);
    return `${d.emoji} ${d.name[lang] || d.name.de}`;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXPOSE TO GLOBAL
  // ═══════════════════════════════════════════════════════════════════════

  window.WINDI_Dragons = {
    version: '1.0.0',
    DRAGONS,
    routeDragon,
    getDragon,
    dragonBadge,
    emojis: { guardian: '🛡️', architect: '🏗️', witness: '👁️' },
    names: { guardian: 'Guardian', architect: 'Architect', witness: 'Witness' }
  };

})();
