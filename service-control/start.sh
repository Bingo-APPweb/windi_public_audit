#!/bin/bash
# W-SERVICE-CONTROL Start Script
cd /opt/windi/service-control
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
python3 app.py
