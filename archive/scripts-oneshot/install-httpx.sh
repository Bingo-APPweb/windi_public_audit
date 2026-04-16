#!/bin/bash
# Install httpx with Debian override
pip3 install httpx==0.27.0 --break-system-packages

# Verify
python3 -c "import httpx; print('✅ httpx', httpx.__version__, 'installed')"

# Restart verify-public
echo "Restarting verify-public..."
sudo systemctl restart windi-verify-public
sleep 3
sudo systemctl status windi-verify-public --no-pager | head -10
