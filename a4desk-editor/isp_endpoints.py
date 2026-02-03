"""
WINDI ISP Endpoints for A4 Desk
"""
import sys
sys.path.insert(0, '/opt/windi/isp')

from flask import Blueprint, jsonify, request
from isp_loader import list_profiles, load_profile, generate_styled_html, load_css
from datetime import datetime

isp_bp = Blueprint('isp', __name__)

@isp_bp.route('/api/isp/list')
def api_list_isp():
    """Lista todos os ISPs disponíveis"""
    profiles = list_profiles()
    return jsonify({"profiles": profiles})

@isp_bp.route('/api/isp/<profile_id>')
def api_get_isp(profile_id):
    """Retorna detalhes de um ISP"""
    profile = load_profile(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profile)

@isp_bp.route('/api/isp/<profile_id>/css')
def api_get_isp_css(profile_id):
    """Retorna CSS de um ISP"""
    css = load_css(profile_id)
    return css, 200, {'Content-Type': 'text/css'}

def apply_isp_to_export(profile_id, title, content_html):
    """Aplica ISP ao HTML para exportação"""
    if not profile_id:
        return None
    
    date_str = datetime.now().strftime("%d.%m.%Y")
    return generate_styled_html(profile_id, title, content_html, date_str)
