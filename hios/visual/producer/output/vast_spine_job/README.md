# SPINE Validation Job — Vast.ai

## TEST-SPINE-001: SORA 2 × SPINE Identity Preservation

**Date:** 01 Jun 2026
**Liga IA+H:** Human Dragon · Guardian · Architect

---

## Purpose

Validate if SORA 2 preserves Elisa's identity when generating video from reference image.

## Contents

```
vast_spine_job/
├── frames/
│   ├── frame_01.png    # SORA 2 output frames
│   ├── frame_02.png
│   ├── frame_03.png
│   ├── frame_04.png
│   └── frame_05.png
├── elisa.anchor.v2.CURRENT.npy   # Canonical Elisa embedding (512D ArcFace)
├── spine_arcface_validate.py      # Validation script
├── setup_vast.sh                  # Environment setup
└── README.md                      # This file
```

## Quick Start (Vast.ai)

### 1. Rent GPU Instance

```bash
# RTX 4090 recommended (24GB VRAM)
vastai search offers 'gpu_name=RTX_4090 num_gpus=1' --order dph_base
vastai create instance <offer_id> --image pytorch/pytorch:latest
```

### 2. Upload Job Package

```bash
# From Strato server
scp -r vast_spine_job/ root@<vast-ip>:/workspace/
```

### 3. Run Setup

```bash
ssh root@<vast-ip>
cd /workspace/vast_spine_job
chmod +x setup_vast.sh
./setup_vast.sh
```

### 4. Execute Validation

```bash
python3 spine_arcface_validate.py
```

### 5. Download Results

```bash
scp root@<vast-ip>:/workspace/vast_spine_job/SPINE_VALIDATION_REPORT.json ./
```

---

## Thresholds

| Level | Similarity | Meaning |
|-------|------------|---------|
| ❌ FAIL | < 0.65 | Identity drift too high |
| 🟢 OPERATIONAL | ≥ 0.65 | Suitable for production |
| ✅ FORENSIC | ≥ 0.75 | Suitable for verification |

---

## Expected Output

```
📊 SUMMARY
   Frames analyzed: 5/5
   Average similarity: 0.7234
   Range: [0.6821 - 0.7589]
   Operational passes: 5/5 (100%)
   Forensic passes: 3/5 (60%)

🎯 SPINE COMPATIBILITY VERDICT
🟡 SORA 2 × SPINE: OPERATIONAL COMPATIBLE
```

---

## Interpreting Results

| Verdict | Action |
|---------|--------|
| FORENSIC_COMPATIBLE | ✅ Use SORA 2 for all scenes |
| OPERATIONAL_COMPATIBLE | 🟡 Use for draft/production, verify hero scenes |
| INCOMPATIBLE | ❌ Re-anchor or use different generator |

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
