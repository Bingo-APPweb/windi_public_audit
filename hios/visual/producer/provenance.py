#!/usr/bin/env python3
"""
WINDI-HIOS Provenance Module — Lei da Proveniência Inseparável
===============================================================
"A pele cresce com a carne; não se cose depois."

This module ensures every synthetic artifact is born with its provenance
sidecar. Generation and receipt are atomic — one cannot exist without the other.

Usage:
    from provenance import ProvenanceWriter, ProvenanceValidator

    # At generation time (atomic)
    with ProvenanceWriter(generator="veo", model="veo-3.1") as prov:
        prov.set_prompt(prompt)
        prov.set_reference_images([("char.png", "sha256:...")])
        video_path = generate_video(...)
        prov.seal(video_path)  # Writes sidecar atomically

    # At validation time
    validator = ProvenanceValidator()
    if not validator.has_valid_provenance(anchor_path):
        raise ValueError("Anchor without verifiable provenance chain")

Author: Liga IA+H · WINDI Publishing House
Date: 2026-06-01
Invariant: I19 (Lei da Proveniência Inseparável)
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# =============================================================================
# CONSTANTS
# =============================================================================

SCHEMA_VERSION = "1.0.0"
PROVENANCE_SUFFIX = ".provenance.json"

VALID_GENERATORS = ["veo", "runway", "sora", "kling", "midjourney", "dalle", "imagen", "local", "manual"]
VALID_ELO_TYPES = ["reference_image", "generated_video", "extracted_frame", "embedding", "composite", "transformed"]
VALID_PURPOSES = ["anchor", "scene", "test", "reference"]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def compute_string_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def generate_provenance_id() -> str:
    """Generate unique provenance ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_hash = hashlib.sha256(os.urandom(32)).hexdigest()[:8].upper()
    return f"WINDI-PROV-{timestamp}-{random_hash}"


def get_provenance_path(artifact_path: Path) -> Path:
    """Get the provenance sidecar path for an artifact."""
    return artifact_path.parent / f"{artifact_path.stem}{PROVENANCE_SUFFIX}"


# =============================================================================
# PROVENANCE WRITER (Context Manager for Atomic Operations)
# =============================================================================

class ProvenanceWriter:
    """
    Context manager that ensures provenance is written atomically with generation.

    If the provenance sidecar fails to write, the entire operation is considered failed.
    This implements the core principle: generation and receipt are one act, not two.
    """

    def __init__(
        self,
        generator: str,
        model: str,
        elo_number: int = 2,
        elo_type: str = "generated_video",
        parent_provenance_id: Optional[str] = None,
        project: Optional[str] = None,
        scene: Optional[str] = None,
        character: Optional[str] = None,
        purpose: str = "scene"
    ):
        if generator not in VALID_GENERATORS:
            raise ValueError(f"Invalid generator: {generator}. Must be one of {VALID_GENERATORS}")
        if elo_type not in VALID_ELO_TYPES:
            raise ValueError(f"Invalid elo_type: {elo_type}. Must be one of {VALID_ELO_TYPES}")
        if purpose not in VALID_PURPOSES:
            raise ValueError(f"Invalid purpose: {purpose}. Must be one of {VALID_PURPOSES}")

        self.provenance_id = generate_provenance_id()
        self.generator = generator
        self.model = model
        self.elo = {
            "number": elo_number,
            "type": elo_type,
        }
        if parent_provenance_id:
            self.elo["parent_provenance_id"] = parent_provenance_id

        self.prompt: Optional[str] = None
        self.prompt_hash: Optional[str] = None
        self.reference_images: List[Dict[str, str]] = []
        self.parameters: Dict[str, Any] = {}
        self.api_response: Dict[str, Any] = {}
        self.windi_metadata = {
            "project": project,
            "scene": scene,
            "character": character,
            "purpose": purpose
        }
        # Remove None values
        self.windi_metadata = {k: v for k, v in self.windi_metadata.items() if v is not None}

        self._sealed = False
        self._artifact_path: Optional[Path] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred - provenance not sealed
            return False
        if not self._sealed:
            raise RuntimeError(
                "ProvenanceWriter exited without seal(). "
                "Generation without provenance violates Lei da Proveniência Inseparável."
            )
        return False

    def set_prompt(self, prompt: str) -> "ProvenanceWriter":
        """Set the generation prompt."""
        self.prompt = prompt[:2000] if len(prompt) > 2000 else prompt
        self.prompt_hash = compute_string_hash(prompt)
        return self

    def set_reference_images(self, images: List[Tuple[str, str, Optional[str]]]) -> "ProvenanceWriter":
        """
        Set reference images used in generation.

        Args:
            images: List of (filename, hash, role) tuples. Role is optional.
        """
        self.reference_images = []
        for item in images:
            if len(item) == 2:
                filename, hash_val = item
                role = "asset"
            else:
                filename, hash_val, role = item
            self.reference_images.append({
                "filename": filename,
                "hash": hash_val,
                "role": role or "asset"
            })
        return self

    def set_parameters(self, **kwargs) -> "ProvenanceWriter":
        """Set generation parameters."""
        self.parameters.update(kwargs)
        return self

    def set_api_response(self, operation_id: str = None, duration_seconds: float = None, status: str = None) -> "ProvenanceWriter":
        """Set API response metadata."""
        if operation_id:
            self.api_response["operation_id"] = operation_id
        if duration_seconds is not None:
            self.api_response["duration_seconds"] = duration_seconds
        if status:
            self.api_response["status"] = status
        return self

    def seal(self, artifact_path: Path) -> Path:
        """
        Seal the provenance sidecar atomically with the artifact.

        This MUST be called after the artifact is written but BEFORE any
        post-processing (FFmpeg, etc). The raw hash is computed here.

        Returns the path to the provenance sidecar.
        """
        artifact_path = Path(artifact_path)
        if not artifact_path.exists():
            raise FileNotFoundError(f"Artifact does not exist: {artifact_path}")

        if self.prompt_hash is None:
            raise ValueError("Prompt not set. Call set_prompt() before seal().")

        # Compute hash of RAW artifact (before any post-processing)
        output_hash_raw = compute_file_hash(artifact_path)

        # Build provenance document
        provenance = {
            "schema_version": SCHEMA_VERSION,
            "provenance_id": self.provenance_id,
            "generator": self.generator,
            "model": self.model,
            "elo": self.elo,
            "prompt": self.prompt,
            "prompt_hash": self.prompt_hash,
            "output_hash_raw": output_hash_raw,
            "output_filename": artifact_path.name,
            "created_at": datetime.now().isoformat(),
            "transformations": []  # Empty - this is the raw artifact
        }

        if self.reference_images:
            provenance["reference_images"] = self.reference_images
        if self.parameters:
            provenance["parameters"] = self.parameters
        if self.api_response:
            provenance["api_response"] = self.api_response
        if self.windi_metadata:
            provenance["windi_metadata"] = self.windi_metadata

        # Write sidecar atomically
        sidecar_path = get_provenance_path(artifact_path)
        temp_path = sidecar_path.with_suffix(".tmp")

        try:
            with open(temp_path, "w") as f:
                json.dump(provenance, f, indent=2, ensure_ascii=False)
            temp_path.rename(sidecar_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to write provenance sidecar: {e}") from e

        self._sealed = True
        self._artifact_path = artifact_path

        return sidecar_path


# =============================================================================
# TRANSFORMATION RECORDER
# =============================================================================

class TransformationRecorder:
    """
    Records a transformation step in the provenance chain.

    Use this when applying FFmpeg or other post-processing to an artifact
    that already has provenance.
    """

    @staticmethod
    def record(
        input_path: Path,
        output_path: Path,
        tool: str,
        operation: str,
        command: Optional[str] = None
    ) -> Path:
        """
        Record a transformation in the provenance chain.

        Reads the input's provenance, adds the transformation, writes to output's sidecar.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Load input provenance
        input_prov_path = get_provenance_path(input_path)
        if not input_prov_path.exists():
            raise FileNotFoundError(
                f"Input artifact has no provenance: {input_path}. "
                "Cannot record transformation without provenance chain."
            )

        with open(input_prov_path) as f:
            provenance = json.load(f)

        # Compute hashes
        input_hash = compute_file_hash(input_path)
        output_hash = compute_file_hash(output_path)

        # Add transformation
        transformation = {
            "tool": tool,
            "operation": operation,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "timestamp": datetime.now().isoformat(),
            "output_filename": output_path.name
        }
        if command:
            transformation["command"] = command

        provenance["transformations"].append(transformation)

        # Write new sidecar
        output_prov_path = get_provenance_path(output_path)
        with open(output_prov_path, "w") as f:
            json.dump(provenance, f, indent=2, ensure_ascii=False)

        return output_prov_path


# =============================================================================
# PROVENANCE VALIDATOR
# =============================================================================

class ProvenanceValidator:
    """
    Validates that an artifact has a complete, verifiable provenance chain.

    This implements the gate that refuses anchors without provenance.
    """

    def __init__(self, require_hash_match: bool = True):
        """
        Args:
            require_hash_match: If True, verify that current file hash matches
                               the last hash in the transformation chain.
        """
        self.require_hash_match = require_hash_match

    def has_valid_provenance(self, artifact_path: Path) -> bool:
        """Check if artifact has valid provenance sidecar."""
        artifact_path = Path(artifact_path)
        prov_path = get_provenance_path(artifact_path)
        return prov_path.exists()

    def load_provenance(self, artifact_path: Path) -> Dict[str, Any]:
        """Load and return provenance document."""
        artifact_path = Path(artifact_path)
        prov_path = get_provenance_path(artifact_path)
        if not prov_path.exists():
            raise FileNotFoundError(f"No provenance sidecar for: {artifact_path}")
        with open(prov_path) as f:
            return json.load(f)

    def get_generator(self, artifact_path: Path) -> str:
        """Get the generator (DOOR) that created this artifact."""
        prov = self.load_provenance(artifact_path)
        return prov["generator"]

    def get_elo(self, artifact_path: Path) -> Dict[str, Any]:
        """Get the elo information for this artifact."""
        prov = self.load_provenance(artifact_path)
        return prov["elo"]

    def validate_elo_coherence(self, anchor_path: Path, test_path: Path) -> Tuple[bool, str]:
        """
        Validate that anchor and test artifact are from the same elo.

        Returns (is_valid, reason).
        """
        anchor_path = Path(anchor_path)
        test_path = Path(test_path)

        if not self.has_valid_provenance(anchor_path):
            return False, f"Anchor has no provenance: {anchor_path}"
        if not self.has_valid_provenance(test_path):
            return False, f"Test artifact has no provenance: {test_path}"

        anchor_prov = self.load_provenance(anchor_path)
        test_prov = self.load_provenance(test_path)

        anchor_gen = anchor_prov["generator"]
        test_gen = test_prov["generator"]

        if anchor_gen != test_gen:
            return False, (
                f"Elo mismatch: anchor from {anchor_gen}, test from {test_gen}. "
                "Lei da Coerência de Elo violated."
            )

        return True, f"Elo coherent: both from {anchor_gen}"

    def validate_hash_integrity(self, artifact_path: Path) -> Tuple[bool, str]:
        """
        Validate that current file hash matches provenance chain.

        Returns (is_valid, reason).
        """
        artifact_path = Path(artifact_path)
        prov = self.load_provenance(artifact_path)

        current_hash = compute_file_hash(artifact_path)

        # Get expected hash (last in chain)
        if prov["transformations"]:
            expected_hash = prov["transformations"][-1]["output_hash"]
        else:
            expected_hash = prov["output_hash_raw"]

        if current_hash != expected_hash:
            return False, (
                f"Hash mismatch: file has {current_hash[:20]}..., "
                f"provenance says {expected_hash[:20]}..."
            )

        return True, "Hash verified"

    def full_validation(self, artifact_path: Path) -> Tuple[bool, List[str]]:
        """
        Perform full validation of artifact provenance.

        Returns (is_valid, list_of_issues).
        """
        issues = []
        artifact_path = Path(artifact_path)

        if not self.has_valid_provenance(artifact_path):
            return False, ["No provenance sidecar found"]

        try:
            prov = self.load_provenance(artifact_path)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in provenance: {e}"]

        # Check required fields
        required = ["schema_version", "provenance_id", "generator", "model",
                    "elo", "prompt_hash", "output_hash_raw", "created_at"]
        for field in required:
            if field not in prov:
                issues.append(f"Missing required field: {field}")

        # Validate hash if required
        if self.require_hash_match:
            hash_valid, hash_msg = self.validate_hash_integrity(artifact_path)
            if not hash_valid:
                issues.append(hash_msg)

        return len(issues) == 0, issues


# =============================================================================
# ANCHOR GATE (for spine.py integration)
# =============================================================================

def anchor_provenance_gate(anchor_path: Path, test_video_generator: str) -> Tuple[bool, str]:
    """
    Gate function for spine.py to check anchor provenance before measurement.

    Returns (can_proceed, reason).

    Usage in spine.py:
        from provenance import anchor_provenance_gate

        can_proceed, reason = anchor_provenance_gate(anchor_path, "veo")
        if not can_proceed:
            raise ValueError(f"Anchor rejected: {reason}")
    """
    validator = ProvenanceValidator(require_hash_match=False)

    if not validator.has_valid_provenance(anchor_path):
        return False, (
            f"Anchor has no provenance chain: {anchor_path}. "
            "Lei da Proveniência Inseparável: artifact without verifiable provenance "
            "cannot be used in cross-elo measurement."
        )

    try:
        prov = validator.load_provenance(anchor_path)
    except Exception as e:
        return False, f"Failed to load provenance: {e}"

    anchor_generator = prov["generator"]

    if anchor_generator != test_video_generator:
        return False, (
            f"Elo mismatch: anchor from '{anchor_generator}', test video from '{test_video_generator}'. "
            "Lei da Coerência de Elo: anchor must be from same elo as test frames."
        )

    return True, f"Provenance valid: anchor and test both from '{anchor_generator}'"


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WINDI-HIOS Provenance Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate artifact provenance")
    validate_parser.add_argument("path", help="Path to artifact")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show artifact provenance")
    show_parser.add_argument("path", help="Path to artifact")

    # Check-elo command
    elo_parser = subparsers.add_parser("check-elo", help="Check elo coherence between anchor and test")
    elo_parser.add_argument("anchor", help="Path to anchor")
    elo_parser.add_argument("test", help="Path to test artifact")

    args = parser.parse_args()

    if args.command == "validate":
        validator = ProvenanceValidator()
        is_valid, issues = validator.full_validation(Path(args.path))
        if is_valid:
            print(f"✅ Valid provenance: {args.path}")
        else:
            print(f"❌ Invalid provenance: {args.path}")
            for issue in issues:
                print(f"   - {issue}")

    elif args.command == "show":
        validator = ProvenanceValidator()
        try:
            prov = validator.load_provenance(Path(args.path))
            print(json.dumps(prov, indent=2))
        except FileNotFoundError:
            print(f"❌ No provenance for: {args.path}")

    elif args.command == "check-elo":
        validator = ProvenanceValidator()
        is_valid, reason = validator.validate_elo_coherence(Path(args.anchor), Path(args.test))
        if is_valid:
            print(f"✅ {reason}")
        else:
            print(f"❌ {reason}")

    else:
        parser.print_help()
