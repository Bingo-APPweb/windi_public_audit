#!/usr/bin/env python3
"""
W-HIOS-001 — WINDI-HIOS Video Studio Server
Port: 8196
Invariants: I1, I9, I11, I14

PHASE: Phase 3 - W-PROMPT-001 Journalist Gate (25 Mai 2026)

Features:
- Three-Tier Sovereignty: EXTERNAL/OPAQUE (Veo) → CONTROLLED/RENTED (LTX) → LOCAL/SOVEREIGN (Strato)
- W-MAILs-001: Cryptographic prompt distribution protocol
- W-PROMPT-001: Journalistic Context Translator (proves PROVENANCE, not VERACITY)
- Media Browser: Videos <100MB with Ledger verification

Key Distinction (Guardian Correction):
- The seal proves PROVENANCE of intent and source
- NOT veracity of depicted events
- All video is SYNTHETIC_DRAMATIZATION inspired by real sources

Endpoints:
- POST /api/hios/mint-prompt — Create Pre-Ledger Token from facts + intention
- POST /api/hios/confirm-entities — Human confirmation gate for extracted entities
- POST /api/hios/generate — Generate video via Veo 3.1 or LTX 2.3 (async)
- POST /api/hios/seal — Seal approved video to Ledger
- GET /api/hios/job/<id> — Poll job status
- GET /api/hios/jobs — List all jobs
- GET /api/hios/media — List media files for browser
- GET /api/hios/health — Health check
"""

import os
import sys
import json
import hashlib
import subprocess
import threading
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add hybrid pipeline to path for VastPool import
sys.path.insert(0, '/opt/windi/hios/visual/producer/hybrid-pipeline/vast')

app = Flask(__name__)
CORS(app)

# =============================================================================
# Configuration
# =============================================================================

LEDGER_URL = "http://localhost:8101"
VERSION = "0.4.0"  # Phase 3: W-PROMPT-001 Journalist Gate

# W-PROMPT-001 Storage (in production, use Redis or DB)
PROMPT_TOKENS = {}

# Media directory (Die Entscheidung production)
MEDIA_DIR = Path("/opt/windi/hios/visual/producer/obras/die-entscheidung/output")
MAX_MEDIA_SIZE_MB = 100  # Media Browser limit

# Paths
VEO_PRODUCER = Path("/opt/windi/hios/visual/producer/veo_producer.py")
OUTPUT_DIR = Path("/opt/windi/hios/visual/producer/output/video-studio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Job storage (in production, use Redis or DB)
JOBS = {}

# Sovereignty Tiers
TIER_EXTERNAL_OPAQUE = "EXTERNAL/OPAQUE"
TIER_CONTROLLED_RENTED = "CONTROLLED/RENTED"
TIER_LOCAL_SOVEREIGN = "LOCAL/SOVEREIGN"


# =============================================================================
# Utilities
# =============================================================================

def generate_receipt_id(prefix="HIOS"):
    """Generate WINDI-compliant receipt ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_input = f"{prefix}-{timestamp}-{os.urandom(8).hex()}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
    return f"WINDI-{prefix}-{timestamp}-{short_hash}"


def compute_content_hash(content):
    """Compute SHA-256 hash of content (string or bytes)."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def compute_file_hash(filepath):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def build_veo_prompt(script, vibe, platform):
    """Build optimized prompt for Veo 3.1."""
    # Map vibe to cinematic style
    vibe_styles = {
        "documentary": "Cinematic documentary style, 4K, natural lighting, handheld camera stability",
        "educational": "Clean educational style, professional lighting, clear compositions",
        "philosophical": "Contemplative visual essay, slow movements, thoughtful framing",
        "institutional": "Corporate documentary, professional European cinema, warm muted tones",
        "atmospheric": "Atmospheric visual poem, cinematic color grading, emotional lighting"
    }

    style = vibe_styles.get(vibe.split(",")[0].strip().lower(), vibe_styles["documentary"])

    # Build prompt
    prompt = f"{style}. {script[:500]}"  # Veo has prompt limits

    return prompt


# =============================================================================
# Async Video Generation Worker
# =============================================================================

def generate_video_worker(job_id, prompt, output_path, api_key_num=3):
    """
    Background worker to generate video via Veo 3.1.

    Updates job status as it progresses:
    - pending_generation → processing → pending_approval (success)
    - pending_generation → processing → failed (error)
    """
    job = JOBS.get(job_id)
    if not job:
        return

    try:
        # Update status
        job['status'] = 'processing'
        job['processing_started_at'] = datetime.utcnow().isoformat() + "Z"
        job['engine'] = 'veo-3.1'
        job['tier'] = TIER_EXTERNAL_OPAQUE

        print(f"[HIOS] Starting Veo generation for job {job_id}")
        print(f"[HIOS] Prompt: {prompt[:80]}...")

        # Build command
        cmd = [
            "python3",
            str(VEO_PRODUCER),
            prompt,
            "--output", str(output_path),
            "--key", str(api_key_num),
            "--no-frames"  # Skip frame extraction for speed
        ]

        # Run Veo producer
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode != 0:
            job['status'] = 'failed'
            job['error'] = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"[HIOS] Veo failed for job {job_id}: {job['error']}")
            return

        # Check output exists
        if not output_path.exists():
            job['status'] = 'failed'
            job['error'] = f"Output file not created: {output_path}"
            print(f"[HIOS] Output not found for job {job_id}")
            return

        # Get file info
        file_size = output_path.stat().st_size
        file_hash = compute_file_hash(output_path)

        # Update job with success
        job['status'] = 'pending_approval'
        job['video_url'] = f"/api/hios/video/{output_path.name}"
        job['video_path'] = str(output_path)
        job['video_hash'] = file_hash
        job['video_size_mb'] = round(file_size / (1024 * 1024), 2)
        job['generated_at'] = datetime.utcnow().isoformat() + "Z"
        job['blocks'] = [
            {
                "stage": "keyframe",
                "tier": TIER_EXTERNAL_OPAQUE,
                "engine": "veo-3.1",
                "hash": file_hash
            }
        ]

        print(f"[HIOS] Video ready for job {job_id}: {file_size / (1024*1024):.1f} MB")
        print(f"[HIOS] Hash: {file_hash[:32]}...")

    except subprocess.TimeoutExpired:
        job['status'] = 'failed'
        job['error'] = "Veo generation timed out (>10 min)"
        print(f"[HIOS] Timeout for job {job_id}")

    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        print(f"[HIOS] Error for job {job_id}: {e}")


def hybrid_video_worker(job_id, prompt, output_path, api_key_num=3, target_duration=15):
    """
    Background worker for HYBRID mode: Veo keyframe + LTX extension.

    Three-Tier Orchestration:
    1. EXTERNAL/OPAQUE (Veo 3.1) → Generate 4s keyframe
    2. CONTROLLED/RENTED (vast.ai + LTX 2.3) → Extend to target duration
    3. LOCAL/SOVEREIGN (Strato) → Seal with receipt

    The user sees none of this complexity — just clicks and gets video.
    """
    job = JOBS.get(job_id)
    if not job:
        return

    keyframe_path = None
    instance_id = None

    try:
        # Update status
        job['status'] = 'processing'
        job['processing_started_at'] = datetime.utcnow().isoformat() + "Z"
        job['engine'] = 'hybrid'

        print(f"\n{'='*60}")
        print(f"[STRATO] HYBRID ORCHESTRATION for job {job_id}")
        print(f"{'='*60}")

        # ================================================================
        # TIER 1: EXTERNAL/OPAQUE — Veo 3.1 Keyframe (4 seconds)
        # ================================================================
        print(f"[STRATO] TIER 1: Generating Veo keyframe...")

        keyframe_path = output_path.parent / f"{job_id}_keyframe.mp4"

        cmd = [
            "python3",
            str(VEO_PRODUCER),
            prompt,
            "--output", str(keyframe_path),
            "--key", str(api_key_num),
            "--no-frames"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0 or not keyframe_path.exists():
            raise Exception(f"Veo keyframe failed: {result.stderr[:200]}")

        keyframe_hash = compute_file_hash(keyframe_path)
        job['blocks'] = [{
            "stage": "keyframe",
            "tier": TIER_EXTERNAL_OPAQUE,
            "engine": "veo-3.1",
            "hash": keyframe_hash,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }]

        print(f"[STRATO] Keyframe ready: {keyframe_path.stat().st_size / (1024*1024):.1f} MB")

        # ================================================================
        # TIER 2: CONTROLLED/RENTED — vast.ai + LTX 2.3 Extension
        # ================================================================
        print(f"[STRATO] TIER 2: Initiating LTX extension via vast.ai...")

        try:
            from vast_automation import VastPool

            pool = VastPool()

            # Check if vast.ai is available
            if not pool.cli_available:
                print("[STRATO] vast.ai CLI not available — falling back to keyframe only")
                # Copy keyframe to output
                import shutil
                shutil.copy(keyframe_path, output_path)
            else:
                # Full hybrid flow
                print(f"[STRATO] Allocating GPU...")
                instance_id = pool.allocate_cheapest_rtx()

                if instance_id:
                    # Copy keyframe to instance
                    print(f"[STRATO] Uploading keyframe to instance {instance_id}...")
                    pool.copy_to_instance(instance_id, str(keyframe_path), "/workspace/input/keyframe.mp4")

                    # Execute extension
                    print(f"[STRATO] Running LTX 2.3 extension (target: {target_duration}s)...")
                    pool.execute_extension(instance_id, job_id, target_duration=target_duration)

                    # Download result
                    print(f"[STRATO] Downloading extended video...")
                    pool.copy_from_instance(instance_id, "/workspace/output/final.mp4", str(output_path))

                    # MANDATORY TEARDOWN
                    print(f"[STRATO] TEARDOWN: Destroying instance...")
                    pool.destroy_instance(instance_id)
                    instance_id = None

                    # Record extension block
                    extension_hash = compute_file_hash(output_path) if output_path.exists() else None
                    job['blocks'].append({
                        "stage": "extend",
                        "tier": TIER_CONTROLLED_RENTED,
                        "engine": "ltx-2.3-vast",
                        "hash": extension_hash,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                else:
                    print("[STRATO] No GPU available — falling back to keyframe only")
                    import shutil
                    shutil.copy(keyframe_path, output_path)

        except ImportError:
            print("[STRATO] VastPool not available — using keyframe only")
            import shutil
            shutil.copy(keyframe_path, output_path)

        except Exception as e:
            print(f"[STRATO] LTX extension error: {e}")
            # Fallback to keyframe
            if not output_path.exists():
                import shutil
                shutil.copy(keyframe_path, output_path)

            # CRITICAL: Teardown on error
            if instance_id:
                try:
                    pool.destroy_instance(instance_id)
                except:
                    pass

        # ================================================================
        # FINALIZE
        # ================================================================
        if not output_path.exists():
            raise Exception("No output video produced")

        file_size = output_path.stat().st_size
        file_hash = compute_file_hash(output_path)

        job['status'] = 'pending_approval'
        job['video_url'] = f"/api/hios/video/{output_path.name}"
        job['video_path'] = str(output_path)
        job['video_hash'] = file_hash
        job['video_size_mb'] = round(file_size / (1024 * 1024), 2)
        job['generated_at'] = datetime.utcnow().isoformat() + "Z"

        print(f"\n[STRATO] HYBRID COMPLETE: {file_size / (1024*1024):.1f} MB")
        print(f"[STRATO] Blocks: {len(job['blocks'])}")
        print(f"{'='*60}\n")

    except subprocess.TimeoutExpired:
        job['status'] = 'failed'
        job['error'] = "Hybrid generation timed out"
        print(f"[STRATO] Timeout for job {job_id}")

    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        print(f"[STRATO] Error for job {job_id}: {e}")

        # CRITICAL: Emergency teardown
        if instance_id:
            try:
                from vast_automation import VastPool
                VastPool().destroy_instance(instance_id)
            except:
                pass


# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/api/hios/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "service": "W-HIOS-001",
        "version": VERSION,
        "phase": "W-PROMPT-001 Journalist Gate",
        "status": "healthy",
        "port": 8196,
        "engine": "veo-3.1-direct",
        "invariants": ["I1", "I9", "I11", "I14"],
        "tiers": [TIER_EXTERNAL_OPAQUE, TIER_CONTROLLED_RENTED, TIER_LOCAL_SOVEREIGN],
        "ledger": LEDGER_URL,
        "guardian_correction": {
            "proves": "PROVENANCE_OF_INTENT_AND_SOURCE",
            "not": "VERACITY_OF_DEPICTED_EVENTS",
            "depiction_type": "SYNTHETIC_DRAMATIZATION"
        },
        "endpoints": {
            "mint_prompt": "POST /api/hios/mint-prompt",
            "confirm_entities": "POST /api/hios/confirm-entities",
            "generate": "POST /api/hios/generate",
            "seal": "POST /api/hios/seal",
            "job": "GET /api/hios/job/<job_id>",
            "jobs": "GET /api/hios/jobs",
            "media": "GET /api/hios/media"
        }
    })


# =============================================================================
# W-PROMPT-001: Journalist Gate Endpoints
# =============================================================================

@app.route('/api/hios/mint-prompt', methods=['POST'])
def mint_prompt():
    """
    Create a Pre-Ledger Token from journalist facts and intention.

    W-PROMPT-001: Proves PROVENANCE, not VERACITY.
    All generated video is SYNTHETIC_DRAMATIZATION.

    Accepts:
    - raw_facts: The factual source text (article, transcript, etc.)
    - source_type: NEWSPAPER_ARTICLE, INTERVIEW_TRANSCRIPT, etc.
    - source_language: de, en, pt
    - human_focus: Editorial intention (what story to tell)
    - audience: Target audience
    - journalist_did: DID of the journalist (optional, can be added later)

    Returns:
    - prompt_id: Token ID for this prompt
    - extracted_entities: Entities requiring human confirmation
    - lifecycle: ENTITY_CONFIRMATION_PENDING
    """
    data = request.get_json()

    # I14: Explicit failure for missing fields
    required = ['raw_facts', 'human_focus']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "error": "I14_MISSING_REQUIRED_FIELDS",
            "missing": missing
        }), 400

    # Generate prompt ID
    prompt_id = generate_receipt_id("WPMT").replace("WINDI-WPMT-", "WPMT-")[:13]
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Hash the raw facts (immutable from this point)
    raw_facts = data['raw_facts']
    context_hash = compute_content_hash(raw_facts)

    # Extract entities (simplified extraction - in production use NLP/LLM)
    entities = extract_entities(raw_facts)

    # Detect source language (simplified)
    source_lang = data.get('source_language', detect_language(raw_facts))

    # Build the token
    token = {
        "prompt_id": prompt_id,
        "journalist_did": data.get('journalist_did', 'pending'),
        "lifecycle": "ENTITY_CONFIRMATION_PENDING",
        "depiction_type": "SYNTHETIC_DRAMATIZATION",
        "proves": "PROVENANCE_OF_INTENT_AND_SOURCE",
        "source_artifact": {
            "type": data.get('source_type', 'NEWSPAPER_ARTICLE'),
            "raw_text": raw_facts,
            "headline": data.get('headline', ''),
            "publication": data.get('publication', ''),
            "context_hash": context_hash,
            "source_language": source_lang
        },
        "human_focus": {
            "intention_text": data['human_focus'],
            "dramatic_tension": data.get('dramatic_tension', ''),
            "intention_language": data.get('intention_language', source_lang),
            "NOT_claiming": "This intention does not claim the depicted scene occurred. It directs dramatization."
        },
        "audience": {
            "primary_audience": data.get('audience', 'GENERAL_PUBLIC'),
            "tone": data.get('tone', 'INFORMATIVE'),
            "complexity_level": data.get('complexity', 'STANDARD')
        },
        "extracted_entities": {
            "entities": entities,
            "human_confirmed": False,
            "confirmed_by": None,
            "confirmed_at": None,
            "corrections_made": []
        },
        "constitutional_constraints": {
            "invariants_applied": ["I9_NO_AUTONOMY_ESCALATION", "I9_ANTI_CLICHE", "I11_EVIDENCE_PERMANENT"],
            "style_constraints": {
                "regional_atmosphere": detect_regional_atmosphere(raw_facts),
                "forbidden_elements": ["dystopian_cliche", "sensationalism", "fictional_locations"],
                "required_elements": ["documentary_realism", "natural_lighting", "authentic_textures"]
            }
        },
        "generated_payload": None,  # Generated after entity confirmation
        "integrity": {
            "prompt_hash": None,  # Set after confirmation
            "created_at": timestamp,
            "pre_ledger_receipt": None
        }
    }

    # Store token
    PROMPT_TOKENS[prompt_id] = token

    print(f"[W-PROMPT-001] Created token {prompt_id}")
    print(f"[W-PROMPT-001] Extracted {len(entities)} entities pending confirmation")

    return jsonify({
        "success": True,
        "prompt_id": prompt_id,
        "lifecycle": "ENTITY_CONFIRMATION_PENDING",
        "depiction_type": "SYNTHETIC_DRAMATIZATION",
        "proves": "PROVENANCE_OF_INTENT_AND_SOURCE",
        "context_hash": context_hash,
        "extracted_entities": entities,
        "message": "Pre-Ledger Token created. Human must confirm extracted entities before prompt compilation.",
        "next_step": f"POST /api/hios/confirm-entities with prompt_id={prompt_id}"
    })


@app.route('/api/hios/confirm-entities', methods=['POST'])
def confirm_entities():
    """
    Human confirmation gate for extracted entities.

    CRITICAL: This gate prevents sealing extraction errors.
    The journalist must review and confirm the entities before they are locked.

    Accepts:
    - prompt_id: The token to confirm
    - confirmed: true/false
    - confirmer_did: DID of the human confirming
    - corrections: Optional array of corrections [{original, corrected, reason}]

    Returns:
    - compiled_prompt: The Master Prompt in technical English
    - locked_constants: The immutable factual constants
    - pre_ledger_receipt: Receipt for the pre-production seal
    """
    data = request.get_json()

    prompt_id = data.get('prompt_id')
    confirmed = data.get('confirmed', False)
    confirmer_did = data.get('confirmer_did', 'anonymous')

    if not prompt_id:
        return jsonify({"error": "I14_MISSING_PROMPT_ID"}), 400

    token = PROMPT_TOKENS.get(prompt_id)
    if not token:
        return jsonify({"error": "TOKEN_NOT_FOUND", "prompt_id": prompt_id}), 404

    if token['lifecycle'] != 'ENTITY_CONFIRMATION_PENDING':
        return jsonify({
            "error": "INVALID_LIFECYCLE",
            "current": token['lifecycle'],
            "expected": "ENTITY_CONFIRMATION_PENDING"
        }), 400

    if not confirmed:
        return jsonify({
            "error": "CONFIRMATION_REQUIRED",
            "message": "Human must confirm entities are correct. Set confirmed=true after review."
        }), 400

    # Apply any corrections
    corrections = data.get('corrections', [])
    if corrections:
        token['extracted_entities']['corrections_made'] = corrections
        # Apply corrections to entities
        for correction in corrections:
            for entity in token['extracted_entities']['entities']:
                if entity['value'] == correction.get('original'):
                    entity['value'] = correction['corrected']
                    entity['corrected'] = True

    # Mark as confirmed
    timestamp = datetime.utcnow().isoformat() + "Z"
    token['extracted_entities']['human_confirmed'] = True
    token['extracted_entities']['confirmed_by'] = confirmer_did
    token['extracted_entities']['confirmed_at'] = timestamp

    # Update journalist DID if provided
    if confirmer_did != 'anonymous':
        token['journalist_did'] = confirmer_did

    # Compile the Master Prompt
    master_prompt = compile_master_prompt(token)

    # Build locked constants from confirmed entities
    locked_constants = {
        "location": extract_location(token),
        "reference_year": datetime.utcnow().year,
        "verified_entities": [e['value'] for e in token['extracted_entities']['entities']]
    }

    # Update token with generated payload
    token['generated_payload'] = {
        "compiled_prompt": master_prompt,
        "prompt_language": "en",
        "target_engine": "VEO_3.1",
        "locked_constants": locked_constants,
        "dramatization_disclaimer": "This prompt generates SYNTHETIC DRAMATIZATION inspired by real sources. The resulting video depicts actors/AI-generated figures, not actual events."
    }

    # Compute integrity hash
    payload_for_hash = json.dumps({
        "source_hash": token['source_artifact']['context_hash'],
        "intention": token['human_focus']['intention_text'],
        "compiled_prompt": master_prompt,
        "locked_constants": locked_constants,
        "confirmed_by": confirmer_did
    }, sort_keys=True)
    prompt_hash = compute_content_hash(payload_for_hash)

    # Create pre-ledger receipt
    pre_receipt_id = generate_receipt_id("WPMT-PRE")

    token['integrity']['prompt_hash'] = prompt_hash
    token['integrity']['pre_ledger_receipt'] = pre_receipt_id
    token['lifecycle'] = 'LOCKED'

    print(f"[W-PROMPT-001] Token {prompt_id} LOCKED by {confirmer_did}")
    print(f"[W-PROMPT-001] Master Prompt: {master_prompt[:80]}...")

    return jsonify({
        "success": True,
        "prompt_id": prompt_id,
        "lifecycle": "LOCKED",
        "depiction_type": "SYNTHETIC_DRAMATIZATION",
        "proves": "PROVENANCE_OF_INTENT_AND_SOURCE",
        "compiled_prompt": master_prompt,
        "locked_constants": locked_constants,
        "prompt_hash": prompt_hash,
        "pre_ledger_receipt": pre_receipt_id,
        "message": "Entities confirmed. Master Prompt compiled. Token LOCKED and ready for generation.",
        "next_step": f"POST /api/hios/generate with prompt_id={prompt_id}"
    })


@app.route('/api/hios/prompt/<prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """Get a prompt token by ID."""
    token = PROMPT_TOKENS.get(prompt_id)
    if not token:
        return jsonify({"error": "TOKEN_NOT_FOUND"}), 404

    # Return token with Guardian-auditable fields
    # DUAL LINEAGE: source_hash (original) + corrections_made (human intervention)
    return jsonify({
        "prompt_id": token['prompt_id'],
        "lifecycle": token['lifecycle'],
        "depiction_type": token['depiction_type'],
        "proves": token['proves'],
        "source_type": token['source_artifact']['type'],
        "context_hash": token['source_artifact']['context_hash'],
        "human_focus": token['human_focus']['intention_text'],
        "audience": token['audience'],
        # GUARDIAN AUDIT: Entity confirmation evidence
        "extracted_entities": {
            "entities": token['extracted_entities']['entities'],
            "human_confirmed": token['extracted_entities']['human_confirmed'],
            "confirmed_by": token['extracted_entities']['confirmed_by'],
            "confirmed_at": token['extracted_entities']['confirmed_at'],
            "corrections_made": token['extracted_entities'].get('corrections_made', [])
        },
        "compiled_prompt": token.get('generated_payload', {}).get('compiled_prompt'),
        "locked_constants": token.get('generated_payload', {}).get('locked_constants'),
        "integrity": token['integrity']
    })


# =============================================================================
# W-PROMPT-001 Helper Functions
# =============================================================================

def extract_entities(text):
    """
    Extract factual entities from text.
    Simplified implementation - in production, use NLP or LLM.
    """
    import re
    entities = []

    # Extract monetary values
    money_patterns = [
        (r'(\d+(?:[\.,]\d+)?)\s*(?:Milliarden?|billion|bilhões?)\s*(?:Euro|EUR|€)?', 'MONETARY_VALUE'),
        (r'(\d+(?:[\.,]\d+)?)\s*(?:Millionen?|million|milhões?)\s*(?:Euro|EUR|€)?', 'MONETARY_VALUE'),
        (r'€\s*(\d+(?:[\.,]\d+)?)\s*(?:Mrd|Mio)?', 'MONETARY_VALUE'),
    ]
    for pattern, etype in money_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                "type": etype,
                "value": match.group(0),
                "original_context": text[max(0, match.start()-30):match.end()+30],
                "confidence": 0.9
            })

    # Extract numbers/statistics
    stat_pattern = r'(\d{1,3}(?:\.\d{3})*|\d+)\s+(?:Mitarbeiter|employees|funcionários|Filialen|branches|filiais)'
    for match in re.finditer(stat_pattern, text, re.IGNORECASE):
        entities.append({
            "type": "STATISTIC",
            "value": match.group(0),
            "original_context": text[max(0, match.start()-30):match.end()+30],
            "confidence": 0.85
        })

    # Extract organization names (simplified - looks for capitalized words near bank/company indicators)
    org_pattern = r'(?:VR-Bank|Sparkasse|Bank|Volksbank|Raiffeisenbank)\s+[\w\-]+'
    for match in re.finditer(org_pattern, text):
        entities.append({
            "type": "ORGANIZATION",
            "value": match.group(0),
            "original_context": text[max(0, match.start()-30):match.end()+30],
            "confidence": 0.95
        })

    # Extract locations (German/Bavarian cities)
    locations = ['Kempten', 'Oberallgäu', 'Allgäu', 'München', 'Bavaria', 'Bayern', 'Augsburg']
    for loc in locations:
        if loc.lower() in text.lower():
            entities.append({
                "type": "LOCATION",
                "value": loc,
                "original_context": "",
                "confidence": 0.95
            })

    return entities


def detect_language(text):
    """Simple language detection based on common words."""
    de_indicators = ['und', 'der', 'die', 'das', 'ist', 'nicht', 'mit', 'für']
    pt_indicators = ['que', 'não', 'para', 'com', 'uma', 'são', 'está']
    en_indicators = ['the', 'and', 'is', 'not', 'with', 'for', 'this']

    text_lower = text.lower()
    de_count = sum(1 for w in de_indicators if f' {w} ' in text_lower)
    pt_count = sum(1 for w in pt_indicators if f' {w} ' in text_lower)
    en_count = sum(1 for w in en_indicators if f' {w} ' in text_lower)

    if de_count > pt_count and de_count > en_count:
        return 'de'
    elif pt_count > en_count:
        return 'pt'
    return 'en'


def detect_regional_atmosphere(text):
    """Detect regional atmosphere from text content."""
    text_lower = text.lower()
    if any(loc in text_lower for loc in ['allgäu', 'kempten', 'oberallgäu', 'alpine']):
        return 'ALLGAU_REALISM'
    elif any(loc in text_lower for loc in ['münchen', 'munich', 'berlin', 'frankfurt']):
        return 'URBAN_GERMAN'
    elif any(loc in text_lower for loc in ['bayern', 'bavaria', 'alpen']):
        return 'ALPINE_BAVARIA'
    return 'NEUTRAL_EUROPEAN'


def extract_location(token):
    """Extract primary location from token."""
    for entity in token['extracted_entities']['entities']:
        if entity['type'] == 'LOCATION':
            return entity['value']
    return 'Germany'


def compile_master_prompt(token):
    """
    Compile the Master Prompt in technical English.

    Translates journalist intention + regional atmosphere + constitutional constraints
    into precise video generation instructions.
    """
    source = token['source_artifact']
    focus = token['human_focus']
    audience = token['audience']
    constraints = token['constitutional_constraints']

    # Map regional atmosphere to visual style
    atmosphere_styles = {
        'ALLGAU_REALISM': 'Soft alpine morning light, authentic Bavarian regional architecture, muted earth tones, documentary realism',
        'URBAN_GERMAN': 'Clean urban European lighting, modern German corporate environment, professional color grading',
        'ALPINE_BAVARIA': 'Dramatic alpine lighting, traditional Bavarian elements, warm golden hour tones',
        'NEUTRAL_EUROPEAN': 'Neutral European corporate setting, balanced natural lighting, professional documentary style'
    }

    atmosphere = constraints['style_constraints'].get('regional_atmosphere', 'NEUTRAL_EUROPEAN')
    visual_style = atmosphere_styles.get(atmosphere, atmosphere_styles['NEUTRAL_EUROPEAN'])

    # Map audience to narrative approach
    audience_styles = {
        'GENERAL_PUBLIC': 'accessible visual storytelling, clear compositions',
        'REGULATORS': 'precise institutional framing, formal documentary style',
        'EXECUTIVES': 'professional corporate aesthetic, confident camera work',
        'STUDENTS': 'engaging educational framing, dynamic but clear',
        'JOURNALISTS': 'investigative documentary style, objective framing'
    }

    audience_style = audience_styles.get(audience.get('primary_audience', 'GENERAL_PUBLIC'), '')

    # Extract key elements from intention
    intention = focus.get('intention_text', '')
    tension = focus.get('dramatic_tension', '')

    # Build the prompt
    prompt_parts = [
        "Cinematic documentary style, 4K resolution.",
        visual_style + ".",
        audience_style + "." if audience_style else "",
    ]

    # Add scene direction based on intention
    if intention:
        # Translate common patterns to visual directions
        if 'decidir' in intention.lower() or 'decide' in intention.lower() or 'entscheiden' in intention.lower():
            prompt_parts.append("A focused professional making a considered decision, human agency visible.")
        if 'aprovar' in intention.lower() or 'approve' in intention.lower() or 'genehmigen' in intention.lower():
            prompt_parts.append("Close-up on human hands reviewing physical documents, deliberate approval action.")
        if 'contra' in intention.lower() or 'against' in intention.lower() or 'gegen' in intention.lower():
            prompt_parts.append("Tension in body language, thoughtful resistance, human judgment prevailing.")

    # Add constitutional constraints
    prompt_parts.append("Zero special effects, pure documentary realism.")
    prompt_parts.append("Authentic textures, no artificial enhancement.")
    prompt_parts.append("Human responsibility and agency as central visual theme.")

    # Compile
    master_prompt = " ".join(p for p in prompt_parts if p)

    return master_prompt


@app.route('/api/hios/generate', methods=['POST'])
def generate_video():
    """
    Generate video via selected engine (async).

    Three-Tier Sovereignty Model:
    - veo-3.1: EXTERNAL/OPAQUE (Google Veo API)
    - ltx-2.3: CONTROLLED/RENTED (vast.ai GPU rental)
    - hybrid: Veo keyframe + LTX extension

    Accepts:
    - script: Video script/narrative (required)
    - topic: Video topic (required)
    - vibe: Style/mood (required)
    - targetAudience: Target audience (required)
    - platform: youtube|tiktok|instagram (required)
    - engine: veo-3.1|ltx-2.3|hybrid (optional, default: veo-3.1)
    - api_key: 1|2|3 (optional, default: 3)

    Returns job_id for polling. Video generated in background.
    """
    data = request.get_json()

    # I14: Explicit failure for missing required fields
    required = ['script', 'topic', 'vibe', 'targetAudience', 'platform']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "error": "I14_MISSING_REQUIRED_FIELDS",
            "missing": missing,
            "message": f"Required fields missing: {', '.join(missing)}"
        }), 400

    # Generate job ID
    job_id = generate_receipt_id("HIOS-JOB")
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Compute content hash for integrity
    content_for_hash = json.dumps({
        "script": data['script'],
        "topic": data['topic'],
        "vibe": data['vibe'],
        "platform": data['platform']
    }, sort_keys=True)
    content_hash = compute_content_hash(content_for_hash)

    # Get engine selection
    engine = data.get('engine', 'veo-3.1')
    if engine not in ['veo-3.1', 'ltx-2.3', 'hybrid']:
        engine = 'veo-3.1'

    # Map engine to tier
    engine_tier_map = {
        'veo-3.1': TIER_EXTERNAL_OPAQUE,
        'ltx-2.3': TIER_CONTROLLED_RENTED,
        'hybrid': TIER_EXTERNAL_OPAQUE  # Starts with Veo
    }
    tier = engine_tier_map.get(engine, TIER_EXTERNAL_OPAQUE)

    # Build Veo prompt
    prompt = build_veo_prompt(data['script'], data['vibe'], data['platform'])

    # Output path
    safe_topic = "".join(c if c.isalnum() or c in "-_ " else "" for c in data['topic'])[:30]
    output_filename = f"{job_id}_{safe_topic.replace(' ', '_')}.mp4"
    output_path = OUTPUT_DIR / output_filename

    # Create job record
    job = {
        "job_id": job_id,
        "status": "pending_generation",
        "created_at": timestamp,
        "params": {
            "script": data['script'],
            "topic": data['topic'],
            "vibe": data['vibe'],
            "targetAudience": data['targetAudience'],
            "platform": data['platform']
        },
        "prompt": prompt,
        "content_hash": content_hash,
        "output_path": str(output_path),
        "video_url": None,
        "video_hash": None,
        "receipt_id": None,
        "human_approved": False,
        "engine": engine,
        "tier": tier,
        "blocks": []
    }

    JOBS[job_id] = job

    # Get API key preference (default to key 3)
    api_key_num = data.get('api_key', 3)

    # Start async generation based on engine
    if engine == 'hybrid':
        # HYBRID: Veo keyframe + LTX extension via vast.ai
        worker = threading.Thread(
            target=hybrid_video_worker,
            args=(job_id, prompt, output_path, api_key_num),
            kwargs={'target_duration': data.get('target_duration', 15)},
            daemon=True
        )
        worker.start()

        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "pending_generation",
            "content_hash": content_hash,
            "engine": engine,
            "tier": tier,
            "mode": "three_tier_orchestration",
            "tiers": [
                {"stage": "keyframe", "tier": TIER_EXTERNAL_OPAQUE, "engine": "veo-3.1"},
                {"stage": "extend", "tier": TIER_CONTROLLED_RENTED, "engine": "ltx-2.3-vast"},
                {"stage": "seal", "tier": TIER_LOCAL_SOVEREIGN, "engine": "strato-ledger"}
            ],
            "message": "Hybrid orchestration started: Veo keyframe → vast.ai LTX extension → Ledger seal",
            "estimated_time": "5-10 minutes"
        })

    elif engine == 'ltx-2.3':
        # LTX standalone (requires existing keyframe)
        return jsonify({
            "success": False,
            "error": "LTX_REQUIRES_KEYFRAME",
            "message": "LTX 2.3 standalone requires a keyframe. Use 'hybrid' mode for full pipeline.",
            "hint": "Set engine='hybrid' to automatically generate keyframe + extension",
            "engine": engine,
            "tier": tier
        }), 400

    else:
        # VEO-3.1: Direct generation
        worker = threading.Thread(
            target=generate_video_worker,
            args=(job_id, prompt, output_path, api_key_num),
            daemon=True
        )
        worker.start()

    return jsonify({
        "success": True,
        "job_id": job_id,
        "status": "pending_generation",
        "content_hash": content_hash,
        "engine": engine,
        "tier": tier,
        "message": f"Video generation started via {engine}. Poll /api/hios/job/{{job_id}} for status.",
        "estimated_time": "2-5 minutes"
    })


@app.route('/api/hios/job/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get job status and details."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({
            "error": "JOB_NOT_FOUND",
            "job_id": job_id
        }), 404

    # Return sanitized job (exclude internal paths in production)
    return jsonify({
        "job_id": job['job_id'],
        "status": job['status'],
        "created_at": job['created_at'],
        "content_hash": job['content_hash'],
        "video_url": job.get('video_url'),
        "video_hash": job.get('video_hash'),
        "video_size_mb": job.get('video_size_mb'),
        "generated_at": job.get('generated_at'),
        "receipt_id": job.get('receipt_id'),
        "human_approved": job.get('human_approved', False),
        "engine": job.get('engine'),
        "tier": job.get('tier'),
        "blocks": job.get('blocks', []),
        "error": job.get('error')
    })


@app.route('/api/hios/seal', methods=['POST'])
def seal_video():
    """
    Seal approved video to Forensic Ledger.

    I9: Requires human_approved=true
    I11: Creates immutable Ledger receipt

    Accepts:
    - job_id: Job ID from generate (required)
    - human_approved: Must be true (required, I9)
    - approver: Who approved (required)
    """
    data = request.get_json()

    job_id = data.get('job_id')
    human_approved = data.get('human_approved', False)
    approver_input = data.get('approver', 'anonymous')

    # Map approver to valid DID actor
    ACTOR_MAP = {
        'human-dragon': 'did:windi:dragon-001',
        'system': 'did:windi:system-001',
        'cgo': 'did:windi:dragon-001',
    }
    approver = ACTOR_MAP.get(approver_input, approver_input)
    if not approver.startswith('did:windi:') and '@' not in approver:
        approver = f"did:windi:{approver}"

    # I14: Explicit failure
    if not job_id:
        return jsonify({
            "error": "I14_MISSING_JOB_ID",
            "message": "job_id is required"
        }), 400

    job = JOBS.get(job_id)
    if not job:
        return jsonify({
            "error": "JOB_NOT_FOUND",
            "job_id": job_id
        }), 404

    # I9: Human approval gate
    if not human_approved:
        return jsonify({
            "error": "I9_HUMAN_APPROVAL_REQUIRED",
            "message": "human_approved must be true. AI cannot auto-seal.",
            "invariant": "I9"
        }), 403

    # Check video is ready
    if job['status'] != 'pending_approval' or not job.get('video_url'):
        return jsonify({
            "error": "VIDEO_NOT_READY",
            "message": "Video must be generated and pending_approval before sealing",
            "job_status": job.get('status')
        }), 400

    # Generate receipt ID
    receipt_id = generate_receipt_id("VSTUDIO")
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Add seal block to lineage
    seal_block = {
        "stage": "seal",
        "tier": TIER_LOCAL_SOVEREIGN,
        "engine": "strato-ledger",
        "hash": job.get('video_hash', job['content_hash'])
    }
    blocks = job.get('blocks', []) + [seal_block]

    # Build lineage string
    engines = [b['engine'].split('-')[0] for b in blocks]
    lineage = "->".join(engines)

    # Build Ledger payload
    ledger_payload = {
        "schema_version": "1.0",
        "id": receipt_id,
        "actor": approver,
        "app": "hios-video-studio",
        "doc_name": job['params']['topic'],
        "doc_type": "video_production",
        "governance_level": "MEDIUM",
        "content_hash": job.get('video_hash', job['content_hash']),
        "sge_score": 0.85,
        "wallet_id": "",
        "metadata": {
            "job_id": job_id,
            "video_url": job['video_url'],
            "video_size_mb": job.get('video_size_mb'),
            "platform": job['params']['platform'],
            "vibe": job['params']['vibe'],
            "engine": job.get('engine'),
            "blocks": blocks,
            "lineage": lineage,
            "human_approved": True,
            "approved_by": approver,
            "invariants": ["I1", "I9", "I11"],
            "stage": "C6",
            "sealed_at": timestamp
        }
    }

    # POST to Ledger
    try:
        response = requests.post(
            f"{LEDGER_URL}/api/receipts",
            json=ledger_payload,
            timeout=10
        )

        if response.status_code in [200, 201]:
            ledger_response = response.json()

            # Update job
            job['status'] = "sealed"
            job['receipt_id'] = receipt_id
            job['sealed_at'] = timestamp
            job['human_approved'] = True
            job['approved_by'] = approver
            job['blocks'] = blocks
            job['lineage'] = lineage

            print(f"[HIOS] Sealed job {job_id} with receipt {receipt_id}")
            print(f"[HIOS] Lineage: {lineage}")

            return jsonify({
                "success": True,
                "receipt_id": receipt_id,
                "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}",
                "video_url": job['video_url'],
                "video_hash": job.get('video_hash'),
                "content_hash": job['content_hash'],
                "lineage": lineage,
                "blocks": blocks,
                "sealed_at": timestamp,
                "invariants": ["I1", "I9", "I11"],
                "ledger_response": ledger_response
            })
        else:
            return jsonify({
                "error": "LEDGER_ERROR",
                "status_code": response.status_code,
                "message": response.text
            }), 500

    except requests.RequestException as e:
        return jsonify({
            "error": "LEDGER_CONNECTION_ERROR",
            "message": str(e)
        }), 500


@app.route('/api/hios/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (admin/debug)."""
    jobs_summary = []
    for job in JOBS.values():
        jobs_summary.append({
            "job_id": job['job_id'],
            "status": job['status'],
            "topic": job['params'].get('topic', '')[:50],
            "created_at": job['created_at'],
            "engine": job.get('engine'),
            "tier": job.get('tier'),
            "receipt_id": job.get('receipt_id')
        })

    return jsonify({
        "jobs": jobs_summary,
        "total": len(JOBS),
        "by_status": {
            "pending_generation": sum(1 for j in JOBS.values() if j['status'] == 'pending_generation'),
            "processing": sum(1 for j in JOBS.values() if j['status'] == 'processing'),
            "pending_approval": sum(1 for j in JOBS.values() if j['status'] == 'pending_approval'),
            "sealed": sum(1 for j in JOBS.values() if j['status'] == 'sealed'),
            "failed": sum(1 for j in JOBS.values() if j['status'] == 'failed')
        }
    })


# =============================================================================
# Media Browser API
# =============================================================================

@app.route('/api/hios/media', methods=['GET'])
def list_media():
    """
    List media files for the Media Browser.
    Only includes videos under 100MB with Ledger verification status.
    """
    media_files = []

    # Scan media directory
    if MEDIA_DIR.exists():
        for video_file in MEDIA_DIR.glob("*.mp4"):
            try:
                file_size = video_file.stat().st_size
                size_mb = file_size / (1024 * 1024)

                # Only include files under the limit
                if size_mb <= MAX_MEDIA_SIZE_MB:
                    # Check if we have a receipt for this file (simplified check)
                    file_hash = compute_file_hash(video_file)
                    is_verified = any(
                        j.get('video_hash') == file_hash and j.get('receipt_id')
                        for j in JOBS.values()
                    )

                    media_files.append({
                        "filename": video_file.name,
                        "size_mb": round(size_mb, 2),
                        "url": f"/api/hios/media/{video_file.name}",
                        "hash": file_hash[:32] + "...",
                        "verified": is_verified,
                        "modified": datetime.fromtimestamp(video_file.stat().st_mtime).isoformat()
                    })
            except Exception as e:
                print(f"[HIOS] Error scanning {video_file}: {e}")

    # Sort by modification time (newest first)
    media_files.sort(key=lambda x: x['modified'], reverse=True)

    return jsonify({
        "media": media_files,
        "total": len(media_files),
        "max_size_mb": MAX_MEDIA_SIZE_MB,
        "directory": str(MEDIA_DIR)
    })


@app.route('/api/hios/media/<filename>')
def serve_media(filename):
    """Serve media files from the production directory."""
    from flask import send_from_directory
    if MEDIA_DIR.exists():
        return send_from_directory(str(MEDIA_DIR), filename)
    return jsonify({"error": "MEDIA_NOT_FOUND"}), 404


# =============================================================================
# Static file serving for generated videos (Video Studio output)
# =============================================================================

@app.route('/api/hios/video/<filename>')
def serve_video(filename):
    """Serve generated video files from Video Studio output."""
    from flask import send_from_directory
    return send_from_directory(str(OUTPUT_DIR), filename)


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  W-HIOS-001 — WINDI-HIOS Video Studio Server                ║
║  Version: {VERSION}                                            ║
║  Port: 8196                                                  ║
║  Phase: W-PROMPT-001 Journalist Gate                         ║
║  Invariants: I1, I9, I11, I14                               ║
╠══════════════════════════════════════════════════════════════╣
║  GUARDIAN CORRECTION (Constitutional):                       ║
║  • Proves: PROVENANCE of intent and source                   ║
║  • NOT: Veracity of depicted events                          ║
║  • Type: SYNTHETIC_DRAMATIZATION                             ║
╠══════════════════════════════════════════════════════════════╣
║  Journalist Gate (W-PROMPT-001):                             ║
║  POST /api/hios/mint-prompt      — Create Pre-Ledger Token  ║
║  POST /api/hios/confirm-entities — Human confirmation gate  ║
║  GET  /api/hios/prompt/ID        — Get prompt token         ║
╠══════════════════════════════════════════════════════════════╣
║  Generation Pipeline:                                        ║
║  POST /api/hios/generate  — Start async video generation    ║
║  GET  /api/hios/job/ID    — Poll job status                 ║
║  POST /api/hios/seal      — Seal to Ledger (I9 gate)        ║
║  GET  /api/hios/jobs      — List all jobs                   ║
║  GET  /api/hios/media     — Media Browser (videos <100MB)   ║
║  GET  /api/hios/health    — Health check                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=8196, debug=False)
