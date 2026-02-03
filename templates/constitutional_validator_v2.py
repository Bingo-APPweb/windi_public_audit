#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Constitutional Validator v2.0.0
9 Artigos da Constituicao WINDI
28 Janeiro 2026 - Three Dragons Protocol
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

VERSION = "2.0.0"

ARTICLE_WEIGHTS = {
    'A1': 10, 'A2': 10, 'A3': 10, 'A4': 10, 'A5': 15,
    'A6': 10, 'A7': 10, 'A8': 15, 'A9': 10
}

FORBIDDEN_TERMS = [
    r'\bich denke\b', r'\bich glaube\b', r'\bich meine\b',
    r'\bmeiner meinung nach\b', r'\bpersoenlich\b',
    r'\bvielleicht\b', r'\beventuell\b', r'\bmoeglicherweise\b',
]

REQUIRED_TERMS = [
    r'\bsehr geehrte\b', r'\bmit freundlichen gruessen\b',
    r'\bhochachtungsvoll\b',
]

HTML_PATTERNS = [r'<[a-zA-Z][^>]*>', r'</[a-zA-Z]+>', r'&[a-zA-Z]+;']


@dataclass
class Violation:
    article: str
    code: str
    message: str
    severity: str = 'warning'
    location: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'article': self.article,
            'code': self.code,
            'message': self.message,
            'severity': self.severity,
            'location': self.location
        }


@dataclass
class ValidationResult:
    compliant: bool
    quality_score: int
    violations: List[Violation] = field(default_factory=list)
    article_scores: Dict[str, int] = field(default_factory=dict)
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    validator_version: str = VERSION

    @property
    def axiom_scores(self):
        return self.article_scores

    def to_dict(self) -> dict:
        return {
            'compliant': self.compliant,
            'quality_score': self.quality_score,
            'violations': [v.to_dict() for v in self.violations],
            'article_scores': self.article_scores,
            'validated_at': self.validated_at,
            'validator_version': self.validator_version
        }


class ConstitutionalValidatorV2:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.min_score = self.config.get('min_quality_score', 70)

    def validate(self, template: dict, inputs: dict, content: Any) -> ValidationResult:
        violations = []
        article_scores = {}
        content_str = self._to_string(content).lower()

        article_scores['A1'] = self._check_a1(content_str, violations)
        article_scores['A2'] = self._check_a2(template, inputs, violations)
        article_scores['A3'] = self._check_a3(content_str, violations)
        article_scores['A4'] = self._check_a4(content_str, violations)
        article_scores['A5'] = self._check_a5(template, inputs, violations)
        article_scores['A6'] = 100
        article_scores['A7'] = self._check_a7(template, violations)
        article_scores['A8'] = self._check_a8(content_str, violations)
        article_scores['A9'] = self._check_a9(content_str, violations)

        quality_score = self._calculate_score(article_scores)
        has_critical = any(v.severity == 'critical' for v in violations)
        compliant = quality_score >= self.min_score and not has_critical

        return ValidationResult(
            compliant=compliant,
            quality_score=quality_score,
            violations=violations,
            article_scores=article_scores
        )

    def _to_string(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False)
        return str(content)

    def _check_a1(self, content: str, violations: List[Violation]) -> int:
        score = 100
        if re.search(r'\{template:', content, re.IGNORECASE):
            violations.append(Violation('A1', 'template_creation', 'Tentativa de criar template', 'critical'))
            score -= 50
        return max(0, score)

    def _check_a2(self, template: dict, inputs: dict, violations: List[Violation]) -> int:
        score = 100
        human_only_codes = {h.get('field_code', '') for h in template.get('human_only', [])}
        for code in inputs.keys():
            if code in human_only_codes:
                violations.append(Violation('A2', 'human_field_via_api', f"Campo human_only '{code}' via API", 'critical'))
                score -= 50
        return max(0, score)

    def _check_a3(self, content: str, violations: List[Violation]) -> int:
        score = 100
        for pattern in HTML_PATTERNS:
            if re.search(pattern, content):
                violations.append(Violation('A3', 'html_detected', 'HTML detectado', 'warning'))
                score -= 20
        return max(0, score)

    def _check_a4(self, content: str, violations: List[Violation]) -> int:
        score = 100
        if re.search(r'[\U0001F600-\U0001F64F]', content):
            violations.append(Violation('A4', 'emoji', 'Emoji em documento formal', 'warning'))
            score -= 30
        if content.count('!') > 3:
            violations.append(Violation('A4', 'exclamation', 'Pontuacao excessiva', 'info'))
            score -= 10
        return max(0, score)

    def _check_a5(self, template: dict, inputs: dict, violations: List[Violation]) -> int:
        human_only_codes = {h.get('field_code', '') for h in template.get('human_only', [])}
        for code in human_only_codes:
            if code and code in inputs:
                violations.append(Violation('A5', 'sacred_violated', f"Campo sagrado '{code}' violado", 'critical'))
                return 0
        return 100

    def _check_a7(self, template: dict, violations: List[Violation]) -> int:
        if not template or not template.get('id'):
            return 80
        return 100

    def _check_a8(self, content: str, violations: List[Violation]) -> int:
        score = 100
        for pattern in FORBIDDEN_TERMS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                violations.append(Violation('A8', 'forbidden_term', f"Termo proibido: '{match.group()}'", 'critical'))
                score -= 30
        has_required = any(re.search(p, content, re.IGNORECASE) for p in REQUIRED_TERMS)
        if not has_required and len(content) > 200:
            violations.append(Violation('A8', 'no_formal', 'Sem saudacao formal', 'warning'))
            score -= 15
        return max(0, score)

    def _check_a9(self, content: str, violations: List[Violation]) -> int:
        score = 100
        if len(content) < 50:
            violations.append(Violation('A9', 'too_short', 'Conteudo muito curto', 'warning'))
            score -= 30
        return max(0, score)

    def _calculate_score(self, article_scores: Dict[str, int]) -> int:
        total = sum(ARTICLE_WEIGHTS.values())
        weighted = sum(article_scores.get(a, 100) * w for a, w in ARTICLE_WEIGHTS.items())
        return int(weighted / total)


if __name__ == "__main__":
    v = ConstitutionalValidatorV2()
    r = v.validate({'id': 'test', 'human_only': []}, {}, "Sehr geehrter Herr Mueller, Mit freundlichen Gruessen.")
    print(f"Score: {r.quality_score}, OK: {r.compliant}")
