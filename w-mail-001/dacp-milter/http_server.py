"""
W-MAIL-DACP-MILTER — HTTP Admin Server
Spec: §227 Section 12
Endpoints: /health, /metrics, /version
Port: 8895
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

from metrics import get_metrics
from ledger_client import is_ledger_reachable
from selector_loader import is_selector_loaded, get_dkim_selector

logger = logging.getLogger(__name__)

HTTP_PORT = int(os.environ.get('HTTP_ADMIN_PORT', '8895'))
VERSION = "1.0.0"
COMMIT = os.environ.get('GIT_COMMIT', 'unknown')


class AdminHandler(BaseHTTPRequestHandler):
    """HTTP handler for admin endpoints"""

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(f"HTTP: {args[0]}")

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response"""
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str = 'text/plain', status: int = 200):
        """Send text response"""
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._handle_health()
        elif self.path == '/metrics':
            self._handle_metrics()
        elif self.path == '/version':
            self._handle_version()
        else:
            self.send_error(404, 'Not Found')

    def _handle_health(self):
        """
        Health check endpoint.
        Returns: {status, ledger_reachable, dkim_selector_loaded, uptime_s}
        """
        metrics = get_metrics()
        ledger_ok = is_ledger_reachable()
        selector_ok = is_selector_loaded()

        # Status is 'healthy' only if Ledger is reachable
        status = 'healthy' if ledger_ok else 'degraded'

        data = {
            'status': status,
            'ledger_reachable': ledger_ok,
            'dkim_selector_loaded': selector_ok,
            'dkim_selector': get_dkim_selector(),
            'uptime_s': round(metrics.get_uptime(), 1)
        }

        http_status = 200 if status == 'healthy' else 503
        self._send_json(data, http_status)

    def _handle_metrics(self):
        """
        Prometheus metrics endpoint.
        Returns metrics in Prometheus text format.
        """
        metrics = get_metrics()
        text = metrics.to_prometheus()
        self._send_text(text, content_type='text/plain; version=0.0.4')

    def _handle_version(self):
        """
        Version endpoint.
        Returns: {version, commit}
        """
        data = {
            'version': VERSION,
            'commit': COMMIT,
            'spec': '§227 W-MAIL-DACP-MILTER v1.0'
        }
        self._send_json(data)


def start_http_server(port: int = None):
    """Start the HTTP admin server (blocking)"""
    port = port or HTTP_PORT
    server = HTTPServer(('0.0.0.0', port), AdminHandler)
    logger.info(f"HTTP admin server listening on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_http_server()
