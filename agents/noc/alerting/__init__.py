# WINDI NOC Agent - Alerting Module
"""
Sistema de alertas do NOC Agent

- alert_manager: Gerenciamento de alertas
- notifiers: Canais de notificacao (Telegram, Email, Webhook)
- aggregator: Agregacao de alertas
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import requests

__all__ = ['AlertManager', 'TelegramNotifier', 'WebhookNotifier', 'AlertSeverity']


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    notification_sent: bool = False


class AlertManager:
    """Gerenciador central de alertas"""

    def __init__(self, config: Dict):
        self.config = config
        self.alerts: Dict[str, Alert] = {}
        self.notifiers: List[Callable] = []
        self.alert_history: List[Alert] = []

        # Agregacao
        self.aggregation_window = config.get('aggregation', {}).get('window_seconds', 300)
        self.last_aggregation: Dict[str, datetime] = {}

    def add_notifier(self, notifier: Callable):
        """Adiciona canal de notificacao"""
        self.notifiers.append(notifier)

    def create_alert(self, severity: AlertSeverity, title: str,
                     description: str, source: str, labels: Dict = None) -> Optional[Alert]:
        """Cria novo alerta"""

        # Verifica agregacao (evita spam)
        key = f"{severity.value}_{title}_{source}"
        if key in self.last_aggregation:
            elapsed = (datetime.now() - self.last_aggregation[key]).total_seconds()
            if elapsed < self.aggregation_window:
                return None  # Alerta agregado

        self.last_aggregation[key] = datetime.now()

        # Cria alerta
        alert_id = f"{key}_{int(datetime.now().timestamp())}"
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            source=source,
            labels=labels or {}
        )

        self.alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Notifica
        self._notify(alert)

        return alert

    def resolve_alert(self, alert_id: str):
        """Resolve um alerta"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()

    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos"""
        return [a for a in self.alerts.values() if not a.resolved]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Retorna alertas por severidade"""
        return [a for a in self.alerts.values()
                if a.severity == severity and not a.resolved]

    def _notify(self, alert: Alert):
        """Envia notificacoes"""
        for notifier in self.notifiers:
            try:
                notifier(alert)
                alert.notification_sent = True
            except Exception as e:
                print(f"Notification error: {e}")

    def cleanup_old_alerts(self, max_age_hours: int = 24):
        """Remove alertas antigos resolvidos"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            aid for aid, alert in self.alerts.items()
            if alert.resolved and alert.timestamp < cutoff
        ]
        for aid in to_remove:
            del self.alerts[aid]


class TelegramNotifier:
    """Notificador Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def __call__(self, alert: Alert):
        """Envia alerta via Telegram"""
        emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨"
        }

        message = f"""
{emoji.get(alert.severity, '📢')} <b>WINDI NOC Alert</b>

<b>Severity:</b> {alert.severity.value.upper()}
<b>Title:</b> {alert.title}
<b>Source:</b> {alert.source}

<b>Description:</b>
{alert.description}

<i>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>
"""

        try:
            requests.post(self.api_url, data={
                'chat_id': self.chat_id,
                'text': message.strip(),
                'parse_mode': 'HTML'
            }, timeout=10)
        except Exception as e:
            print(f"Telegram error: {e}")


class WebhookNotifier:
    """Notificador Webhook"""

    def __init__(self, url: str, headers: Dict = None):
        self.url = url
        self.headers = headers or {'Content-Type': 'application/json'}

    def __call__(self, alert: Alert):
        """Envia alerta via Webhook"""
        payload = {
            'id': alert.id,
            'severity': alert.severity.value,
            'title': alert.title,
            'description': alert.description,
            'source': alert.source,
            'timestamp': alert.timestamp.isoformat(),
            'labels': alert.labels
        }

        try:
            requests.post(
                self.url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=10
            )
        except Exception as e:
            print(f"Webhook error: {e}")
