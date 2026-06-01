#!/bin/bash
# =============================================================================
# SPINE Validation — Vast.ai Setup Script
# =============================================================================
# WINDI-HIOS Cinema · TEST-SPINE-001
#
# Run this on a Vast.ai GPU instance (RTX 3090/4090 recommended)
# =============================================================================

set -e

echo "=============================================="
echo "SPINE Validation Setup — Vast.ai"
echo "=============================================="

# Update pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install insightface onnxruntime-gpu opencv-python numpy

# Download ArcFace model (buffalo_l) on first run
echo "Pre-loading ArcFace model..."
python3 -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l'); app.prepare(ctx_id=0)"

echo ""
echo "=============================================="
echo "Setup complete! Run validation:"
echo "  python3 spine_arcface_validate.py"
echo "=============================================="
