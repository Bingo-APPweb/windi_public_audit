#!/bin/bash
PORT=$1
echo "[AUTO-HEAL] $(date) — Checking port $PORT..."
fuser -k ${PORT}/tcp 2>/dev/null && echo "[AUTO-HEAL] Cleaned port $PORT" || echo "[AUTO-HEAL] Port $PORT already clean"
sleep 1
