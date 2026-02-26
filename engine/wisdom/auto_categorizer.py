#!/usr/bin/env python3
"""
WINDI Wisdom Auto-Categorizer — Rule-Based (No LLM Key Required)
Categories: pattern | insight | decision | template | risk | best_practice
"""
import re, json

class WisdomCategorizer:
    RULES = {
        "pattern": {
            "keywords": ["always","every time","consistently","recurring","repeated",
                         "immer","jedes mal","wiederholt","muster",
                         "sempre","toda vez","recorrente","padrão"],
            "patterns": [r"when.*then",r"if.*always",r"cada vez que",r"whenever",r"typically",r"usually"],
            "weight": 1.0
        },
        "insight": {
            "keywords": ["realized","discovered","noticed","understood","learned",
                         "erkannt","entdeckt","bemerkt","verstanden",
                         "percebi","descobri","notei","entendi","aprendi"],
            "patterns": [r"turns out",r"key (finding|takeaway)",r"na verdade",
                         r"it means",r"isso significa",r"das bedeutet"],
            "weight": 1.0
        },
        "decision": {
            "keywords": ["decided","chose","approved","rejected","selected",
                         "entschieden","gewählt","genehmigt","abgelehnt",
                         "decidiu","escolheu","aprovou","rejeitou"],
            "patterns": [r"we (will|chose|decided)",r"going forward",
                         r"a partir de agora",r"ab jetzt",r"the decision"],
            "weight": 1.2
        },
        "template": {
            "keywords": ["template","format","structure","layout","schema",
                         "vorlage","struktur","formato","modelo","ISP"],
            "patterns": [r"use this (as|for)",r"standard (format|template)",
                         r"padrão de",r"Standardvorlage"],
            "weight": 0.9
        },
        "risk": {
            "keywords": ["risk","danger","warning","vulnerability","threat",
                         "risiko","gefahr","warnung","schwachstelle",
                         "risco","perigo","alerta","vulnerabilidade","ameaça"],
            "patterns": [r"watch out",r"be careful",r"cuidado",
                         r"achtung",r"never do",r"nunca faça",r"SGE.*(R[3-5])"],
            "weight": 1.3
        },
        "best_practice": {
            "keywords": ["best practice","recommended","optimal","proven",
                         "empfohlen","bewährt","optimal",
                         "recomendado","comprovado","melhor prática"],
            "patterns": [r"(should|must) always",r"golden rule",
                         r"regra de ouro",r"immer.*sollen"],
            "weight": 1.0
        }
    }

    def __init__(self):
        self.version = "1.0.0"
        self.requires_api_key = False

    def categorize(self, text: str) -> dict:
        text_lower = text.lower()
        scores = {}
        for cat, rules in self.RULES.items():
            score, matches = 0.0, []
            for kw in rules["keywords"]:
                if kw.lower() in text_lower:
                    score += 1.0; matches.append(f"kw:{kw}")
            for pat in rules["patterns"]:
                if re.search(pat, text_lower):
                    score += 1.5; matches.append(f"pat:{pat[:20]}")
            score *= rules["weight"]
            if score > 0:
                scores[cat] = {"score": round(score, 2), "matches": matches}

        if not scores:
            return {"category": "insight", "confidence": 0.3,
                    "method": "default_fallback", "requires_api_key": False}

        best = max(scores.items(), key=lambda x: x[1]["score"])
        total = sum(s["score"] for s in scores.values())
        return {
            "category": best[0],
            "confidence": round(best[1]["score"] / max(total, 1), 2),
            "score": best[1]["score"], "matches": best[1]["matches"],
            "alternatives": {k: v["score"] for k, v in scores.items() if k != best[0]},
            "method": "rule_based_trilingual", "requires_api_key": False
        }

    def health(self) -> dict:
        return {
            "status": "ok", "service": "windi-wisdom-categorizer",
            "version": self.version,
            "categories": list(self.RULES.keys()),
            "languages": ["de", "en", "pt"],
            "method": "rule_based",
            "requires_api_key": False, "autonomous": True
        }

if __name__ == "__main__":
    cat = WisdomCategorizer()
    tests = [
        ("Every time we export without QR, the client calls back", "pattern"),
        ("Decided: ab jetzt all ISP templates require trilingual metadata", "decision"),
        ("Risk alert: vulnerabilidade no pipeline quando Ledger timeout > 5s", "risk"),
    ]
    print("🧠 WINDI Wisdom Auto-Categorizer — Self-Test\n")
    for text, expected in tests:
        r = cat.categorize(text)
        status = "✓" if r["category"] == expected else f"✗ (got {r['category']})"
        print(f'  "{text[:55]}..." → {r["category"]} {status}')
    print(f"\n{json.dumps(cat.health(), indent=2)}")
    print("\n✅ Auto-Categorizer — LOCAL AUTONOMOUS — Ready")
