#!/bin/bash
# WINDI Templates - Installation Script
# Run on server: sudo bash install.sh

echo "=========================================="
echo "WINDI Templates - Installation"
echo "=========================================="

# 1. Install dependencies
echo "[1/4] Installing Python dependencies..."
pip install reportlab python-docx qrcode[pil] Pillow beautifulsoup4 --break-system-packages

# 2. Create directory
echo "[2/4] Creating template directory..."
sudo mkdir -p /opt/windi/templates

# 3. Copy files
echo "[3/4] Copying template files..."
sudo cp -r windi_templates/* /opt/windi/templates/

# 4. Set permissions
echo "[4/4] Setting permissions..."
sudo chown -R $USER:$USER /opt/windi/templates
sudo chmod -R 755 /opt/windi/templates

# Test
echo ""
echo "=========================================="
echo "Testing installation..."
echo "=========================================="
python3 -c "
import sys
sys.path.insert(0, '/opt/windi/templates')
from bescheid.generator import generate_bescheid_pdf, BEISPIEL_BAUGENEHMIGUNG
pdf, receipt = generate_bescheid_pdf(BEISPIEL_BAUGENEHMIGUNG)
print(f'✅ Bescheid template OK')
print(f'   Receipt ID: {receipt[\"id\"]}')
print(f'   Hash: {receipt[\"hash\"]}')
"

echo ""
echo "=========================================="
echo "QR Code status..."
echo "=========================================="
python3 -c "
try:
    import qrcode
    print('✅ QR Code library installed')
except ImportError:
    print('⚠️  QR Code library not installed')
    print('   Run: pip install qrcode[pil]')
"

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Templates installed at: /opt/windi/templates"
echo ""
echo "Usage in Python:"
echo "  from windi_templates.bescheid import generate_bescheid_pdf"
echo ""
