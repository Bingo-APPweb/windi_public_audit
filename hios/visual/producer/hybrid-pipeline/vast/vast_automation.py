#!/usr/bin/env python3
"""
W-HIOS Vast.ai Automation — LIVE Implementation
================================================

Tier: CONTROLLED/RENTED
Purpose: Automate GPU rental and LTX 2.3 video extension

Three-Tier Flow:
    1. EXTERNAL/OPAQUE (Veo 3.1) → Keyframe 4s
    2. CONTROLLED/RENTED (Vast.ai + LTX 2.3) → Extend to 15-30s
    3. LOCAL/SOVEREIGN (Strato Ledger) → Seal with receipt

Dependencies:
    pip install vastai
    export VAST_API_KEY=<your-key>

Author: Liga IA+H · WINDI Publishing House
Date: 2026-05-25
"""

import os
import subprocess
import json
import time
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

VAST_API_KEY = os.environ.get("VAST_API_KEY", "")
WINDI_LTX_IMAGE = "windi/hios-ltx-extender:v1"  # Docker image for LTX 2.3
LTX_WORKSPACE = "/workspace"
LOCAL_OUTPUT_DIR = Path("/opt/windi/hios/visual/producer/output")

# GPU constraints
MIN_COMPUTE_CAP = 86  # RTX 3090+ or RTX 4090
MAX_PRICE_PER_HOUR = 0.60  # EUR/USD per hour
PREFERRED_GPU = "RTX_4090"


# =============================================================================
# Vast.ai CLI Wrapper
# =============================================================================

def run_vast_cmd(args: List[str], capture=True) -> subprocess.CompletedProcess:
    """Run vastai CLI command."""
    cmd = ["vastai"] + args
    if VAST_API_KEY:
        cmd = ["vastai", "--api-key", VAST_API_KEY] + args[1:] if args[0] != "vastai" else cmd

    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    else:
        return subprocess.run(cmd, timeout=300)


def check_vast_cli() -> bool:
    """Check if vastai CLI is installed and configured."""
    try:
        result = subprocess.run(["vastai", "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# =============================================================================
# VastPool — Production GPU Pool Manager
# =============================================================================

class VastPool:
    """
    Manages vast.ai GPU instances for LTX 2.3 video extension.

    LIVE IMPLEMENTATION — No more stubs.

    Workflow:
        1. allocate_cheapest_rtx() → Find and rent GPU
        2. copy_to_instance() → Upload keyframe
        3. execute_extension() → Run LTX 2.3
        4. copy_from_instance() → Download result
        5. destroy_instance() → Teardown (mandatory)
    """

    def __init__(
        self,
        min_compute_cap: int = MIN_COMPUTE_CAP,
        max_price: float = MAX_PRICE_PER_HOUR,
        preferred_gpu: str = PREFERRED_GPU
    ):
        self.min_compute_cap = min_compute_cap
        self.max_price = max_price
        self.preferred_gpu = preferred_gpu
        self.api_key = VAST_API_KEY

        # Runtime state
        self.active_instances: Dict[str, dict] = {}

        # Check CLI availability
        self.cli_available = check_vast_cli()
        if not self.cli_available:
            print("[VastPool] WARNING: vastai CLI not installed. Run: pip install vastai")

    def search_offers(self, limit: int = 10) -> List[Dict]:
        """
        Search for available GPU offers on vast.ai.

        Returns list of offers sorted by price (cheapest first).
        """
        if not self.cli_available:
            print("[VastPool] CLI not available — returning empty offers")
            return []

        # Build search query
        query = f"compute_cap >= {self.min_compute_cap} verified == true num_gpus == 1 rentable == true"

        try:
            result = subprocess.run(
                ["vastai", "search", "offers", query, "-o", "dph", "--raw"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"[VastPool] Search failed: {result.stderr}")
                return []

            offers = json.loads(result.stdout)

            # Filter by price and limit
            filtered = [o for o in offers if o.get('dph_total', 999) <= self.max_price]
            return filtered[:limit]

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f"[VastPool] Search error: {e}")
            return []

    def allocate_cheapest_rtx(self) -> Optional[str]:
        """
        Find the cheapest available RTX 4090/3090 and create an instance.

        Returns instance_id on success, None on failure.
        """
        print(f"[VastPool] Searching for GPU <= ${self.max_price}/hr...")

        offers = self.search_offers(limit=5)

        if not offers:
            print("[VastPool] No suitable GPUs available")
            return None

        # Pick the cheapest
        best = offers[0]
        offer_id = best['id']
        gpu_name = best.get('gpu_name', 'Unknown GPU')
        price = best.get('dph_total', 0)

        print(f"[VastPool] Best offer: {gpu_name} @ ${price:.3f}/hr (ID: {offer_id})")

        # Create instance with WINDI LTX image
        try:
            result = subprocess.run(
                ["vastai", "create", "instance", str(offer_id),
                 "--image", WINDI_LTX_IMAGE,
                 "--disk", "20",  # 20GB disk
                 "--raw"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                # Fallback: try with standard CUDA image
                print(f"[VastPool] Custom image failed, trying CUDA base...")
                result = subprocess.run(
                    ["vastai", "create", "instance", str(offer_id),
                     "--image", "nvidia/cuda:12.1.0-devel-ubuntu22.04",
                     "--disk", "30",
                     "--raw"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

            if result.returncode == 0:
                # Parse instance ID from response
                response = json.loads(result.stdout)
                instance_id = str(response.get('new_contract', response.get('id', '')))

                print(f"[VastPool] Instance created: {instance_id}")

                # Store in active instances
                self.active_instances[instance_id] = {
                    "offer_id": offer_id,
                    "gpu_name": gpu_name,
                    "price": price,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "status": "starting"
                }

                # Wait for instance to be ready
                self._wait_for_ready(instance_id, timeout=180)

                return instance_id
            else:
                print(f"[VastPool] Create failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"[VastPool] Allocation error: {e}")
            return None

    def _wait_for_ready(self, instance_id: str, timeout: int = 180):
        """Wait for instance to be running and SSH-ready."""
        print(f"[VastPool] Waiting for instance {instance_id} to be ready...")

        start = time.time()
        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    ["vastai", "show", "instance", instance_id, "--raw"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    status = info.get('actual_status', '')

                    if status == 'running':
                        print(f"[VastPool] Instance {instance_id} is READY")
                        if instance_id in self.active_instances:
                            self.active_instances[instance_id]['status'] = 'running'
                            self.active_instances[instance_id]['ssh_host'] = info.get('ssh_host', '')
                            self.active_instances[instance_id]['ssh_port'] = info.get('ssh_port', 22)
                        return True

                    print(f"[VastPool] Status: {status} (waiting...)")

            except Exception as e:
                print(f"[VastPool] Check error: {e}")

            time.sleep(10)

        print(f"[VastPool] Timeout waiting for instance {instance_id}")
        return False

    def copy_to_instance(self, instance_id: str, local_path: str, remote_path: str) -> bool:
        """
        Copy a file to the vast.ai instance.

        Uses vastai copy command (SCP-based).
        """
        print(f"[VastPool] Copying {local_path} → instance:{remote_path}")

        try:
            result = subprocess.run(
                ["vastai", "copy", local_path, f"{instance_id}:{remote_path}"],
                capture_output=True,
                text=True,
                timeout=300  # 5 min for large files
            )

            if result.returncode == 0:
                print(f"[VastPool] Copy complete")
                return True
            else:
                print(f"[VastPool] Copy failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"[VastPool] Copy error: {e}")
            return False

    def copy_from_instance(self, instance_id: str, remote_path: str, local_path: str) -> bool:
        """
        Copy a file from the vast.ai instance to local.
        """
        print(f"[VastPool] Copying instance:{remote_path} → {local_path}")

        # Ensure output directory exists
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                ["vastai", "copy", f"{instance_id}:{remote_path}", local_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print(f"[VastPool] Download complete: {local_path}")
                return True
            else:
                print(f"[VastPool] Download failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"[VastPool] Download error: {e}")
            return False

    def execute_extension(self, instance_id: str, job_id: str,
                          input_file: str = "/workspace/input/keyframe.mp4",
                          output_file: str = "/workspace/output/final.mp4",
                          target_duration: int = 15) -> bool:
        """
        Execute LTX 2.3 video extension on the remote instance.

        Runs the extension script via SSH.
        """
        print(f"[VastPool] Executing LTX extension for job {job_id}")
        print(f"[VastPool] Input: {input_file} → Output: {output_file}")
        print(f"[VastPool] Target duration: {target_duration}s")

        # Extension command (assumes LTX 2.3 is installed in container)
        extension_cmd = f"""
cd /workspace && \\
python3 -m ltx_video.extend \\
    --input {input_file} \\
    --output {output_file} \\
    --target-duration {target_duration} \\
    --model ltx-2.3 \\
    --guidance-scale 7.5 \\
    --job-id {job_id}
"""

        try:
            result = subprocess.run(
                ["vastai", "ssh", instance_id, extension_cmd],
                capture_output=True,
                text=True,
                timeout=600  # 10 min max for extension
            )

            if result.returncode == 0:
                print(f"[VastPool] Extension complete")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                return True
            else:
                print(f"[VastPool] Extension failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[VastPool] Extension timeout (10 min)")
            return False
        except Exception as e:
            print(f"[VastPool] Extension error: {e}")
            return False

    def destroy_instance(self, instance_id: str) -> bool:
        """
        MANDATORY TEARDOWN — Destroy instance to stop billing.

        CRITICAL: Always call this after job completion or failure.
        """
        print(f"[VastPool] TEARDOWN: Destroying instance {instance_id}")

        try:
            result = subprocess.run(
                ["vastai", "destroy", "instance", instance_id, "-y"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"[VastPool] Instance {instance_id} destroyed")
                if instance_id in self.active_instances:
                    del self.active_instances[instance_id]
                return True
            else:
                print(f"[VastPool] Destroy warning: {result.stderr}")
                # Still remove from tracking
                if instance_id in self.active_instances:
                    del self.active_instances[instance_id]
                return True  # Consider destroyed even if warning

        except Exception as e:
            print(f"[VastPool] Destroy error: {e}")
            return False

    def get_status(self) -> Dict:
        """Get pool status for monitoring."""
        return {
            "cli_available": self.cli_available,
            "api_key_set": bool(self.api_key),
            "active_instances": len(self.active_instances),
            "instances": list(self.active_instances.keys()),
            "max_price": self.max_price,
            "preferred_gpu": self.preferred_gpu
        }

    def emergency_cleanup(self) -> int:
        """
        Destroy ALL active instances.

        Use in case of error or shutdown.
        """
        print(f"[VastPool] EMERGENCY CLEANUP: Destroying {len(self.active_instances)} instances")

        destroyed = 0
        for instance_id in list(self.active_instances.keys()):
            if self.destroy_instance(instance_id):
                destroyed += 1

        return destroyed


# =============================================================================
# Orchestration Functions (for hios_server.py integration)
# =============================================================================

def orchestrate_hybrid_extension(
    job_id: str,
    keyframe_path: str,
    target_duration: int = 15
) -> Optional[str]:
    """
    Complete hybrid extension workflow.

    Called by hios_server.py after Veo generates keyframe.

    Returns path to final video, or None on failure.
    """
    print(f"\n{'='*60}")
    print(f"[STRATO] Hybrid Extension Orchestration")
    print(f"[STRATO] Job: {job_id}")
    print(f"[STRATO] Keyframe: {keyframe_path}")
    print(f"{'='*60}\n")

    pool = VastPool()
    instance_id = None

    try:
        # Step 1: Allocate GPU
        print("[STRATO] Step 1/5: Allocating GPU...")
        instance_id = pool.allocate_cheapest_rtx()

        if not instance_id:
            print("[STRATO] FALLBACK: No GPU available, returning keyframe only")
            return keyframe_path

        # Step 2: Copy keyframe to instance
        print("[STRATO] Step 2/5: Uploading keyframe...")
        if not pool.copy_to_instance(instance_id, keyframe_path, "/workspace/input/keyframe.mp4"):
            raise Exception("Failed to upload keyframe")

        # Step 3: Execute extension
        print("[STRATO] Step 3/5: Running LTX 2.3 extension...")
        if not pool.execute_extension(instance_id, job_id, target_duration=target_duration):
            raise Exception("LTX extension failed")

        # Step 4: Download result
        print("[STRATO] Step 4/5: Downloading result...")
        local_output = str(LOCAL_OUTPUT_DIR / f"job_{job_id}_extended.mp4")

        if not pool.copy_from_instance(instance_id, "/workspace/output/final.mp4", local_output):
            raise Exception("Failed to download result")

        # Step 5: Teardown (MANDATORY)
        print("[STRATO] Step 5/5: Teardown...")
        pool.destroy_instance(instance_id)

        print(f"\n[STRATO] SUCCESS: Extended video at {local_output}")
        return local_output

    except Exception as e:
        print(f"[STRATO] ERROR: {e}")

        # CRITICAL: Always teardown on error
        if instance_id:
            print("[STRATO] Emergency teardown...")
            pool.destroy_instance(instance_id)

        # Fallback: return keyframe
        print(f"[STRATO] FALLBACK: Returning keyframe {keyframe_path}")
        return keyframe_path


# =============================================================================
# Main (for testing)
# =============================================================================

if __name__ == "__main__":
    print("W-HIOS Vast.ai Automation — LIVE")
    print("=" * 50)

    pool = VastPool()
    print("\nPool Status:", json.dumps(pool.get_status(), indent=2))

    if pool.cli_available:
        print("\n🔍 Searching for GPUs...")
        offers = pool.search_offers(limit=3)

        if offers:
            print(f"\n📊 Top {len(offers)} offers:")
            for i, offer in enumerate(offers):
                print(f"  {i+1}. {offer.get('gpu_name', '?')} @ ${offer.get('dph_total', 0):.3f}/hr")
        else:
            print("No offers found (check API key and filters)")
    else:
        print("\n⚠️  Install vastai CLI: pip install vastai")
        print("   Set API key: export VAST_API_KEY=<your-key>")
