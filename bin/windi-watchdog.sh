#!/bin/bash
declare -A SERVICES=(
  ["windi-travel"]="8126"
  ["windi-nomad-bot"]="8127"
  ["windi-vd-cut"]="8128"
  ["windi-joe"]="8129"
)

while true; do
  for SERVICE in "${!SERVICES[@]}"; do
    PORT=${SERVICES[$SERVICE]}
    STATUS=$(systemctl is-active "$SERVICE" 2>/dev/null)
    if [ "$STATUS" != "active" ]; then
      echo "[WATCHDOG] $(date) — $SERVICE DOWN — restarting..."
      /usr/bin/fuser -k ${PORT}/tcp 2>/dev/null
      sleep 2
      systemctl restart "$SERVICE"
    fi
  done
  sleep 15
done
