#!/usr/bin/env python3
"""
W-LEXICON-001 — Semantic Drift Detection Service
=================================================
Port: 8193
Invariants: I9, I10, I13, I14

Architecture:
  Endpoint A (this service) — Orchestration on Server A
  Inference B (Ollama)      — mistral:7b on Server B (85.215.131.0:11434)

"Session proves presence. Identity proves agency. Lexicon proves meaning."
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error

# Stage 2 Constitutional Evaluator
from stage2_evaluator import evaluate as stage2_evaluate, Status as Stage2Status

# Configuration
PORT = int(os.environ.get('LEXICON_PORT', 8193))
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://85.215.131.0:11434')
STUB_MODE = os.environ.get('LEXICON_STUB', 'true').lower() == 'true'
CAP_ENABLED = os.environ.get('LEXICON_CAP', 'false').lower() == 'true'
CAP_URL = os.environ.get('CAP_URL', 'http://localhost:8194')
VERSION = '0.3.0'  # Added Stage 2 Constitutional Evaluator

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [LEXICON] %(levelname)s %(message)s'
)
log = logging.getLogger('w-lexicon-001')

# Drift detection prompt template
DRIFT_PROMPT = """Analyze the semantic drift between the REFERENCE text and the CANDIDATE text.

REFERENCE:
{reference}

CANDIDATE:
{candidate}

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "drift_score": <number 0-100 where 0=identical meaning, 100=completely different>,
  "drift_type": "<semantic|structural|tonal|none>",
  "confidence": <number 0-100>,
  "summary": "<one sentence explanation>"
}}"""


def validate_cap_token(token: str, scope: str) -> dict:
    """Validate and consume a CAP token"""
    if not CAP_ENABLED:
        return {"ok": True, "cap_disabled": True}

    url = f"{CAP_URL}/api/cap/consume"
    payload = json.dumps({"token": token, "scope": scope}).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return json.loads(body)
        except:
            return {"ok": False, "error": f"CAP error: {e.code}"}
    except Exception as e:
        log.error(f"CAP validation failed: {e}")
        # I10: Fail open if CAP service is down (configurable)
        return {"ok": False, "error": str(e), "cap_unavailable": True}


def call_ollama(prompt: str, model: str = 'mistral:7b') -> dict:
    """Call Ollama inference on Server B"""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent analysis
            "num_predict": 256
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return {"ok": True, "response": result.get("response", "")}
    except urllib.error.URLError as e:
        log.error(f"Ollama connection failed: {e}")
        return {"ok": False, "error": str(e), "fallback": "I10"}
    except Exception as e:
        log.error(f"Ollama call failed: {e}")
        return {"ok": False, "error": str(e)}


def parse_drift_response(raw: str) -> dict:
    """Parse Ollama response into structured drift data"""
    try:
        # Try to extract JSON from response
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    
    # I14: Explicit failure, no fake data
    return {
        "drift_score": None,
        "drift_type": "parse_error",
        "confidence": 0,
        "summary": "Failed to parse inference response (I14)"
    }


class LexiconHandler(BaseHTTPRequestHandler):
    """HTTP handler for W-LEXICON-001"""
    
    def log_message(self, format, *args):
        log.info(f"{self.address_string()} - {format % args}")
    
    def send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_json({})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        if path in ['', '/health', '/api/lexicon/health']:
            self.handle_health()
        elif path == '/api/lexicon/status':
            self.handle_status()
        else:
            self.send_json({"error": "not_found", "path": path}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/api/lexicon/drift':
            self.handle_drift()
        elif path == '/api/lexicon/analyze':
            self.handle_analyze()
        elif path == '/api/lexicon/constitutional':
            self.handle_constitutional()
        else:
            self.send_json({"error": "not_found", "path": path}, 404)
    
    def handle_health(self):
        """Health check endpoint"""
        # Check Ollama connectivity
        ollama_ok = False
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                ollama_ok = resp.status == 200
        except:
            pass

        # Check CAP connectivity if enabled
        cap_ok = None
        if CAP_ENABLED:
            try:
                req = urllib.request.Request(f"{CAP_URL}/api/cap/health")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    cap_ok = resp.status == 200
            except:
                cap_ok = False

        self.send_json({
            "service": "W-LEXICON-001",
            "version": VERSION,
            "status": "healthy",
            "mode": "stub" if STUB_MODE else "live",
            "ollama_host": OLLAMA_HOST,
            "ollama_reachable": ollama_ok,
            "cap_enabled": CAP_ENABLED,
            "cap_reachable": cap_ok,
            "invariants": ["I9", "I10", "I13", "I14"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def handle_status(self):
        """Detailed status endpoint"""
        self.send_json({
            "service": "W-LEXICON-001",
            "version": VERSION,
            "mode": "stub" if STUB_MODE else "live",
            "description": "Semantic Drift Detection Service",
            "architecture": {
                "endpoint_a": "Server A (orchestration)",
                "inference_b": f"Server B ({OLLAMA_HOST})"
            },
            "endpoints": {
                "/api/lexicon/health": "GET - Health check",
                "/api/lexicon/status": "GET - Detailed status",
                "/api/lexicon/drift": "POST - Stage 1 drift detection",
                "/api/lexicon/constitutional": "POST - TWO-STAGE constitutional drift (Stage 1 + Stage 2)",
                "/api/lexicon/analyze": "POST - Text analysis (stub)"
            },
            "stub_mode": STUB_MODE,
            "stub_reason": "Phase 1 deployment - inference validated, orchestration in progress"
        })
    
    def handle_drift(self):
        """Drift detection endpoint"""
        # CAP token validation (if enabled)
        if CAP_ENABLED:
            auth = self.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                self.send_json({
                    "error": "missing_token",
                    "message": "Authorization: Bearer <token> required",
                    "invariant": "I9"
                }, 401)
                return

            token = auth[7:]
            cap_result = validate_cap_token(token, 'lexicon:drift')
            if not cap_result.get('ok'):
                self.send_json({
                    "error": cap_result.get('error', 'token_invalid'),
                    "invariant": cap_result.get('invariant', 'I9'),
                    "cap_error": True
                }, 401)
                return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json", "invariant": "I14"}, 400)
            return

        reference = data.get('reference', '')
        candidate = data.get('candidate', '')
        
        if not reference or not candidate:
            # I14: Explicit failure for missing data
            self.send_json({
                "error": "missing_fields",
                "required": ["reference", "candidate"],
                "invariant": "I14",
                "message": "Both reference and candidate texts are required"
            }, 400)
            return
        
        # Generate request hash for tracing
        request_hash = hashlib.sha256(
            f"{reference}:{candidate}".encode()
        ).hexdigest()[:16]
        
        if STUB_MODE:
            # Stub mode: return null drift_score with status
            self.send_json({
                "drift_score": None,
                "status": "stub",
                "mode": "stub",
                "request_hash": request_hash,
                "message": "W-LEXICON-001 running in stub mode. Inference B available but orchestration pending.",
                "ollama_host": OLLAMA_HOST,
                "next_phase": "Enable LEXICON_STUB=false for live inference",
                "invariants": {
                    "I9": "human_approval_required_for_live",
                    "I10": "ollama_fallback_available",
                    "I14": "explicit_stub_status"
                }
            })
            return
        
        # Live mode: call Ollama
        prompt = DRIFT_PROMPT.format(reference=reference, candidate=candidate)
        result = call_ollama(prompt)
        
        if not result.get('ok'):
            # I10: Fallback on LLM failure
            self.send_json({
                "drift_score": None,
                "status": "fallback",
                "error": result.get('error'),
                "invariant": "I10",
                "message": "Ollama inference failed, graceful fallback"
            })
            return
        
        # Parse and return drift analysis
        drift = parse_drift_response(result['response'])
        drift['request_hash'] = request_hash
        drift['status'] = 'analyzed'
        drift['model'] = 'mistral:7b'
        drift['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        self.send_json(drift)
    
    def handle_constitutional(self):
        """
        TWO-STAGE Constitutional Drift Detection
        Stage 1: LEXICON (polarity detection via Ollama)
        Stage 2: Constitutional Evaluator (invariant-specific via rules)
        """
        # CAP token validation (if enabled)
        if CAP_ENABLED:
            auth = self.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                self.send_json({
                    "error": "missing_token",
                    "message": "Authorization: Bearer <token> required",
                    "invariant": "I9"
                }, 401)
                return

            token = auth[7:]
            cap_result = validate_cap_token(token, 'lexicon:constitutional')
            if not cap_result.get('ok'):
                self.send_json({
                    "error": cap_result.get('error', 'token_invalid'),
                    "invariant": cap_result.get('invariant', 'I9'),
                    "cap_error": True
                }, 401)
                return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json", "invariant": "I14"}, 400)
            return

        reference = data.get('reference', '')
        candidate = data.get('candidate', '')

        if not reference or not candidate:
            self.send_json({
                "error": "missing_fields",
                "required": ["reference", "candidate"],
                "invariant": "I14",
                "message": "Both reference and candidate texts are required"
            }, 400)
            return

        # Generate request hash
        request_hash = hashlib.sha256(
            f"{reference}:{candidate}".encode()
        ).hexdigest()[:16]

        # === STAGE 1: LEXICON (Polarity Detection) ===
        stage1_result = {
            "drift_score": None,
            "confidence": 0,
            "status": "stub" if STUB_MODE else "pending"
        }

        if not STUB_MODE:
            prompt = DRIFT_PROMPT.format(reference=reference, candidate=candidate)
            ollama_result = call_ollama(prompt)

            if ollama_result.get('ok'):
                stage1_result = parse_drift_response(ollama_result['response'])
                stage1_result['status'] = 'analyzed'
            else:
                stage1_result['status'] = 'fallback'
                stage1_result['error'] = ollama_result.get('error')
                stage1_result['invariant'] = 'I10'

        stage1_drift = stage1_result.get('drift_score') or 0
        stage1_confidence = stage1_result.get('confidence') or 0

        # === STAGE 2: Constitutional Evaluator ===
        stage2_result = stage2_evaluate(
            reference=reference,
            candidate=candidate,
            stage1_drift=stage1_drift,
            stage1_confidence=stage1_confidence
        )

        # Build combined response
        invariants_triggered = [
            {
                "invariant": sig.invariant,
                "evidence": sig.evidence,
                "weight": sig.weight.name
            }
            for sig in stage2_result.invariants_triggered
        ]

        # Determine lexicon_action based on combined result
        if stage2_result.recommendation == 'halt':
            lexicon_action = 'halt'
        elif stage2_result.recommendation == 'interrupt':
            lexicon_action = 'interrupt'
        elif stage2_result.recommendation == 'invite':
            lexicon_action = 'invite'
        else:
            lexicon_action = 'silent'

        self.send_json({
            "request_hash": request_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),

            # Stage 1 results
            "stage1": {
                "drift_score": stage1_result.get('drift_score'),
                "drift_type": stage1_result.get('drift_type'),
                "confidence": stage1_result.get('confidence'),
                "status": stage1_result.get('status'),
                "summary": stage1_result.get('summary')
            },

            # Stage 2 results
            "stage2": {
                "constitutional_status": stage2_result.constitutional_status.value,
                "invariants_triggered": invariants_triggered,
                "requires_pho": stage2_result.requires_pho
            },

            # Combined output
            "combined": {
                "drift_score": stage2_result.combined_drift,
                "recommendation": stage2_result.recommendation,
                "lexicon_action": lexicon_action
            },

            # Metadata
            "model": {
                "stage1": "mistral:7b" if not STUB_MODE else "stub",
                "stage2": "rule-based-v0.1.0"
            },
            "architecture": "TWO-STAGE (§A.3.11)"
        })

    def handle_analyze(self):
        """General text analysis endpoint"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json", "invariant": "I14"}, 400)
            return
        
        text = data.get('text', '')
        analysis_type = data.get('type', 'semantic')
        
        if not text:
            self.send_json({
                "error": "missing_field",
                "required": "text",
                "invariant": "I14"
            }, 400)
            return
        
        if STUB_MODE:
            self.send_json({
                "analysis": None,
                "status": "stub",
                "type": analysis_type,
                "text_length": len(text),
                "message": "Analysis endpoint in stub mode"
            })
            return
        
        # Live mode would call Ollama here
        self.send_json({
            "error": "not_implemented",
            "message": "Live analysis requires I9 approval"
        }, 501)


def main():
    log.info(f"=" * 60)
    log.info(f"W-LEXICON-001 · Semantic Drift Detection")
    log.info(f"=" * 60)
    log.info(f"Port:        {PORT}")
    log.info(f"Mode:        {'STUB' if STUB_MODE else 'LIVE'}")
    log.info(f"Ollama:      {OLLAMA_HOST}")
    log.info(f"Version:     {VERSION}")
    log.info(f"Invariants:  I9, I10, I13, I14")
    log.info(f"=" * 60)
    
    server = HTTPServer(('0.0.0.0', PORT), LexiconHandler)
    log.info(f"Listening on http://0.0.0.0:{PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
