#!/bin/bash
# WINDI Snapshot — generates Outlook report
TIMESTAMP=$(date +%Y%m%d_%H%M)
DIR="/opt/windi/reports"
mkdir -p $DIR

echo "Generating WINDI snapshot..."

curl -sf http://localhost:8108/api/dragon/outlook/report.md -o "$DIR/outlook_${TIMESTAMP}.md" \
  && echo "  Outlook: $DIR/outlook_${TIMESTAMP}.md" \
  || echo "  Outlook: failed"

# Keep only last 20 reports
ls -t $DIR/outlook_*.md 2>/dev/null | tail -n +21 | xargs rm -f 2>/dev/null

echo "Snapshot complete."
