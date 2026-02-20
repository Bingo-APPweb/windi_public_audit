#!/usr/bin/env python3
"""
WINDI NOC Agent - Network Operations Center
O Guardiao da Rede WINDI

Sub-Agent #2 do WINDI Platform
Monitoramento, deteccao de anomalias e alertas inteligentes
"""

import os
import sys
import json
import yaml
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

import requests
from flask import Flask, jsonify, request
from prometheus_client import (
    Counter, Gauge, Histogram, Info,
    generate_latest, CONTENT_TYPE_LATEST
)

# Opcional: ML para deteccao de anomalias
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: sklearn not available, anomaly detection disabled")

# ============================================
# CONFIGURACAO
# ============================================

__version__ = "1.0.0"
__agent_name__ = "WINDI NOC Agent"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/noc_agent.log') if os.path.exists('/app/logs')
        else logging.FileHandler('logs/noc_agent.log')
    ]
)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class MetricPoint:
    timestamp: datetime
    name: str
    value: float
    labels: Dict[str, str]


@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    source: str
    labels: Dict[str, str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class NetworkBaseline:
    metric_name: str
    mean: float
    std: float
    min: float
    max: float
    percentile_95: float
    updated_at: datetime


# ============================================
# PROMETHEUS METRICS
# ============================================

# Metricas do NOC Agent
noc_health = Gauge('windi_noc_health', 'NOC Agent health status (1=healthy, 0=unhealthy)')
noc_uptime = Gauge('windi_noc_uptime_seconds', 'NOC Agent uptime in seconds')
noc_version = Info('windi_noc_version', 'NOC Agent version info')

# Metricas de monitoramento
alerts_total = Counter('windi_noc_alerts_total', 'Total alerts generated', ['severity'])
alerts_active = Gauge('windi_noc_alerts_active', 'Number of active alerts', ['severity'])
anomaly_score = Gauge('windi_noc_anomaly_score', 'Current anomaly score (0-1)')
failure_probability = Gauge('windi_noc_failure_probability', 'Predicted failure probability')

# Metricas de coleta
metrics_collected = Counter('windi_noc_metrics_collected_total', 'Total metrics collected')
collection_errors = Counter('windi_noc_collection_errors_total', 'Total collection errors')
collection_latency = Histogram('windi_noc_collection_latency_seconds', 'Collection latency')


# ============================================
# NOC AGENT CORE
# ============================================

class WindiNocAgent:
    """WINDI NOC Agent - Monitoramento Inteligente da Rede"""

    def __init__(self, config_path: str = "config/noc_config.yaml"):
        self.config = self._load_config(config_path)
        self.start_time = datetime.now()
        self.running = False

        # Storage
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.alerts: Dict[str, Alert] = {}
        self.baselines: Dict[str, NetworkBaseline] = {}

        # ML
        self.anomaly_detector = None
        self.scaler = None
        if ML_AVAILABLE and self.config.get('anomaly_detection', {}).get('enabled', True):
            self._init_anomaly_detector()

        # Threads
        self.collector_thread = None
        self.analyzer_thread = None

        # Flask app
        self.app = Flask(__name__)
        self._setup_routes()

        # Set version info
        noc_version.info({
            'version': __version__,
            'agent': __agent_name__
        })

        logger.info(f"WINDI NOC Agent v{__version__} initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Carrega configuracao do agente"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Configuracao padrao"""
        return {
            'agent': {'port': 8880, 'log_level': 'INFO'},
            'connections': {
                'prometheus': {'url': 'http://localhost:9090'},
                'alertmanager': {'url': 'http://localhost:9093'},
                'isp_agent': {'url': 'http://localhost:8800'}
            },
            'collection': {
                'metrics_interval': 15,
                'health_check_interval': 60,
                'anomaly_detection_interval': 30
            },
            'thresholds': {
                'cpu': {'warning': 70, 'critical': 90},
                'memory': {'warning': 75, 'critical': 95},
                'disk': {'warning': 80, 'critical': 95}
            },
            'anomaly_detection': {'enabled': True, 'contamination': 0.1}
        }

    def _init_anomaly_detector(self):
        """Inicializa detector de anomalias com Isolation Forest"""
        if not ML_AVAILABLE:
            return

        contamination = self.config.get('anomaly_detection', {}).get('contamination', 0.1)
        self.anomaly_detector = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        logger.info("Anomaly detector initialized (Isolation Forest)")

    def _setup_routes(self):
        """Configura rotas da API REST"""

        @self.app.route('/health', methods=['GET'])
        def health():
            status = self.get_health_status()
            return jsonify(status), 200 if status['status'] == 'healthy' else 503

        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

        @self.app.route('/alerts', methods=['GET'])
        def get_alerts():
            active_only = request.args.get('active', 'true').lower() == 'true'
            alerts = self.get_alerts(active_only=active_only)
            return jsonify({'alerts': [asdict(a) for a in alerts], 'count': len(alerts)})

        @self.app.route('/baseline', methods=['GET'])
        def get_baseline():
            return jsonify({
                'baselines': {k: asdict(v) for k, v in self.baselines.items()},
                'count': len(self.baselines)
            })

        @self.app.route('/baseline/update', methods=['POST'])
        def update_baseline():
            self.update_baseline()
            return jsonify({'status': 'ok', 'message': 'Baseline update triggered'})

        @self.app.route('/predict', methods=['POST'])
        def predict():
            data = request.get_json() or {}
            prediction = self.predict_failure(data.get('metrics', {}))
            return jsonify(prediction)

        @self.app.route('/webhook/alert', methods=['POST'])
        def webhook_alert():
            """Recebe alertas do Alertmanager"""
            data = request.get_json() or {}
            self._process_alertmanager_webhook(data)
            return jsonify({'status': 'ok'})

        @self.app.route('/api/v1/status', methods=['GET'])
        def api_status():
            return jsonify({
                'agent': __agent_name__,
                'version': __version__,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'health': self.get_health_status(),
                'alerts_active': len([a for a in self.alerts.values() if not a.resolved]),
                'metrics_buffered': len(self.metrics_buffer),
                'baselines_count': len(self.baselines),
                'ml_available': ML_AVAILABLE
            })

    def get_health_status(self) -> Dict:
        """Retorna status de saude do agente"""
        try:
            # Verifica conexoes
            prometheus_ok = self._check_prometheus()

            uptime = (datetime.now() - self.start_time).total_seconds()

            if prometheus_ok and self.running:
                status = HealthStatus.HEALTHY
                noc_health.set(1)
            elif self.running:
                status = HealthStatus.DEGRADED
                noc_health.set(0.5)
            else:
                status = HealthStatus.UNHEALTHY
                noc_health.set(0)

            noc_uptime.set(uptime)

            return {
                'status': status.value,
                'uptime_seconds': uptime,
                'prometheus_connected': prometheus_ok,
                'collector_running': self.collector_thread is not None and self.collector_thread.is_alive(),
                'analyzer_running': self.analyzer_thread is not None and self.analyzer_thread.is_alive(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            noc_health.set(0)
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_prometheus(self) -> bool:
        """Verifica conexao com Prometheus"""
        try:
            url = self.config['connections']['prometheus']['url']
            response = requests.get(f"{url}/-/healthy", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def query_prometheus(self, query: str) -> Optional[Dict]:
        """Executa query no Prometheus"""
        try:
            url = self.config['connections']['prometheus']['url']
            response = requests.get(
                f"{url}/api/v1/query",
                params={'query': query},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Prometheus query error: {e}")
            collection_errors.inc()
            return None

    def collect_metrics(self) -> List[MetricPoint]:
        """Coleta metricas do Prometheus"""
        metrics = []

        queries = {
            'cpu_usage': '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
            'memory_usage': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
            'disk_usage': '(1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})) * 100',
            'network_in': 'rate(node_network_receive_bytes_total[5m])',
            'network_out': 'rate(node_network_transmit_bytes_total[5m])',
            'load_1m': 'node_load1'
        }

        with collection_latency.time():
            for name, query in queries.items():
                result = self.query_prometheus(query)
                if result and result.get('status') == 'success':
                    for item in result.get('data', {}).get('result', []):
                        value = float(item.get('value', [0, 0])[1])
                        point = MetricPoint(
                            timestamp=datetime.now(),
                            name=name,
                            value=value,
                            labels=item.get('metric', {})
                        )
                        metrics.append(point)
                        self.metrics_buffer.append(point)
                        metrics_collected.inc()

        return metrics

    def detect_anomaly(self, metrics: List[MetricPoint]) -> float:
        """Detecta anomalias usando Isolation Forest"""
        if not ML_AVAILABLE or self.anomaly_detector is None:
            return 0.0

        if len(metrics) < 10:
            return 0.0

        try:
            # Agrupa metricas por tipo
            metric_values = {}
            for m in metrics:
                if m.name not in metric_values:
                    metric_values[m.name] = []
                metric_values[m.name].append(m.value)

            # Cria vetor de features
            features = []
            for name in ['cpu_usage', 'memory_usage', 'network_in', 'network_out']:
                if name in metric_values:
                    features.append(np.mean(metric_values[name]))
                else:
                    features.append(0)

            if len(features) < 4:
                return 0.0

            X = np.array([features])

            # Treina se necessario
            if len(self.metrics_buffer) >= 100:
                training_data = self._prepare_training_data()
                if training_data is not None and len(training_data) >= 50:
                    self.scaler.fit(training_data)
                    X_scaled = self.scaler.transform(training_data)
                    self.anomaly_detector.fit(X_scaled)

            # Prediz
            X_scaled = self.scaler.transform(X)
            score = -self.anomaly_detector.decision_function(X_scaled)[0]

            # Normaliza para 0-1
            score = max(0, min(1, (score + 0.5)))
            anomaly_score.set(score)

            return score

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return 0.0

    def _prepare_training_data(self) -> Optional[np.ndarray]:
        """Prepara dados para treinamento"""
        if len(self.metrics_buffer) < 100:
            return None

        # Agrupa por timestamp (aproximado)
        time_buckets = {}
        for m in self.metrics_buffer:
            bucket = m.timestamp.replace(second=0, microsecond=0)
            if bucket not in time_buckets:
                time_buckets[bucket] = {}
            if m.name not in time_buckets[bucket]:
                time_buckets[bucket][m.name] = []
            time_buckets[bucket][m.name].append(m.value)

        # Cria matriz de features
        data = []
        for bucket, metrics in time_buckets.items():
            row = []
            for name in ['cpu_usage', 'memory_usage', 'network_in', 'network_out']:
                if name in metrics:
                    row.append(np.mean(metrics[name]))
                else:
                    row.append(0)
            if len(row) == 4:
                data.append(row)

        return np.array(data) if data else None

    def check_thresholds(self, metrics: List[MetricPoint]) -> List[Alert]:
        """Verifica thresholds e gera alertas"""
        alerts = []
        thresholds = self.config.get('thresholds', {})

        for metric in metrics:
            metric_type = metric.name.replace('_usage', '')
            if metric_type in thresholds:
                threshold = thresholds[metric_type]

                if metric.value >= threshold.get('critical', 95):
                    alert = self._create_alert(
                        severity=AlertSeverity.CRITICAL,
                        title=f"Critical {metric_type.upper()}",
                        description=f"{metric_type} at {metric.value:.1f}% (threshold: {threshold['critical']}%)",
                        source=metric.labels.get('instance', 'unknown')
                    )
                    alerts.append(alert)

                elif metric.value >= threshold.get('warning', 80):
                    alert = self._create_alert(
                        severity=AlertSeverity.WARNING,
                        title=f"High {metric_type.upper()}",
                        description=f"{metric_type} at {metric.value:.1f}% (threshold: {threshold['warning']}%)",
                        source=metric.labels.get('instance', 'unknown')
                    )
                    alerts.append(alert)

        return alerts

    def _create_alert(self, severity: AlertSeverity, title: str,
                      description: str, source: str) -> Alert:
        """Cria um novo alerta"""
        alert_id = f"{severity.value}_{title}_{source}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            title=title,
            description=description,
            source=source,
            labels={'agent': 'noc'}
        )

        self.alerts[alert_id] = alert
        alerts_total.labels(severity=severity.value).inc()

        # Atualiza contador de alertas ativos
        active_count = len([a for a in self.alerts.values()
                          if not a.resolved and a.severity == severity])
        alerts_active.labels(severity=severity.value).set(active_count)

        logger.warning(f"Alert created: [{severity.value}] {title} - {description}")

        return alert

    def get_alerts(self, active_only: bool = True) -> List[Alert]:
        """Retorna lista de alertas"""
        alerts = list(self.alerts.values())
        if active_only:
            alerts = [a for a in alerts if not a.resolved]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def update_baseline(self):
        """Atualiza baseline da rede"""
        logger.info("Updating network baseline...")

        # Query ultimas 24h
        queries = {
            'cpu_usage': '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
            'memory_usage': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        }

        for name, query in queries.items():
            try:
                # Range query para ultimas 24h
                url = self.config['connections']['prometheus']['url']
                end = datetime.now()
                start = end - timedelta(hours=24)

                response = requests.get(
                    f"{url}/api/v1/query_range",
                    params={
                        'query': query,
                        'start': start.timestamp(),
                        'end': end.timestamp(),
                        'step': '5m'
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    values = []
                    for result in data.get('data', {}).get('result', []):
                        for v in result.get('values', []):
                            values.append(float(v[1]))

                    if values:
                        self.baselines[name] = NetworkBaseline(
                            metric_name=name,
                            mean=np.mean(values) if ML_AVAILABLE else sum(values)/len(values),
                            std=np.std(values) if ML_AVAILABLE else 0,
                            min=min(values),
                            max=max(values),
                            percentile_95=np.percentile(values, 95) if ML_AVAILABLE else max(values),
                            updated_at=datetime.now()
                        )
                        logger.info(f"Baseline updated for {name}: mean={self.baselines[name].mean:.2f}")

            except Exception as e:
                logger.error(f"Error updating baseline for {name}: {e}")

    def predict_failure(self, current_metrics: Dict) -> Dict:
        """Preve probabilidade de falha"""
        if not self.baselines:
            return {'probability': 0, 'confidence': 'low', 'reason': 'No baseline data'}

        # Calcula desvio do baseline
        deviations = []
        reasons = []

        for name, baseline in self.baselines.items():
            current_value = current_metrics.get(name)
            if current_value is not None and baseline.std > 0:
                z_score = abs(current_value - baseline.mean) / baseline.std
                deviations.append(z_score)
                if z_score > 2:
                    reasons.append(f"{name} deviating ({z_score:.1f} std)")

        if not deviations:
            probability = 0
            confidence = 'low'
        else:
            max_deviation = max(deviations)
            probability = min(1, max_deviation / 5)  # Normaliza
            confidence = 'high' if len(deviations) >= 2 else 'medium'

        failure_probability.set(probability)

        return {
            'probability': probability,
            'confidence': confidence,
            'reasons': reasons,
            'timestamp': datetime.now().isoformat()
        }

    def _process_alertmanager_webhook(self, data: Dict):
        """Processa webhook do Alertmanager"""
        for alert_data in data.get('alerts', []):
            status = alert_data.get('status', 'firing')
            labels = alert_data.get('labels', {})
            annotations = alert_data.get('annotations', {})

            if status == 'firing':
                severity_str = labels.get('severity', 'warning')
                severity = AlertSeverity(severity_str) if severity_str in ['warning', 'critical', 'info'] else AlertSeverity.WARNING

                self._create_alert(
                    severity=severity,
                    title=labels.get('alertname', 'Unknown'),
                    description=annotations.get('description', ''),
                    source=labels.get('instance', 'alertmanager')
                )
            elif status == 'resolved':
                # Marca alertas correspondentes como resolvidos
                alertname = labels.get('alertname', '')
                for alert in self.alerts.values():
                    if alertname in alert.title and not alert.resolved:
                        alert.resolved = True
                        alert.resolved_at = datetime.now()

    def _collector_loop(self):
        """Loop de coleta de metricas"""
        interval = self.config.get('collection', {}).get('metrics_interval', 15)

        while self.running:
            try:
                metrics = self.collect_metrics()

                # Verifica thresholds
                alerts = self.check_thresholds(metrics)

                # Detecta anomalias
                if ML_AVAILABLE:
                    score = self.detect_anomaly(metrics)
                    if score > 0.8:
                        self._create_alert(
                            severity=AlertSeverity.WARNING,
                            title="Anomaly Detected",
                            description=f"Anomaly score: {score:.2f}",
                            source="noc-agent"
                        )

                logger.debug(f"Collected {len(metrics)} metrics, {len(alerts)} alerts")

            except Exception as e:
                logger.error(f"Collector error: {e}")
                collection_errors.inc()

            time.sleep(interval)

    def _analyzer_loop(self):
        """Loop de analise e baseline"""
        interval = self.config.get('collection', {}).get('baseline_update_interval', 3600)

        # Atualiza baseline no inicio
        self.update_baseline()

        while self.running:
            time.sleep(interval)
            try:
                self.update_baseline()
            except Exception as e:
                logger.error(f"Analyzer error: {e}")

    def start(self):
        """Inicia o agente NOC"""
        self.running = True

        # Inicia threads
        self.collector_thread = threading.Thread(target=self._collector_loop, daemon=True)
        self.collector_thread.start()

        self.analyzer_thread = threading.Thread(target=self._analyzer_loop, daemon=True)
        self.analyzer_thread.start()

        logger.info(f"WINDI NOC Agent started on port {self.config['agent']['port']}")

        # Inicia servidor Flask
        port = self.config.get('agent', {}).get('port', 8880)
        self.app.run(host='0.0.0.0', port=port, threaded=True)

    def stop(self):
        """Para o agente NOC"""
        self.running = False
        logger.info("WINDI NOC Agent stopped")


# ============================================
# MAIN
# ============================================

def main():
    """Ponto de entrada do NOC Agent"""
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                   WINDI NOC Agent                         ║
    ║              Network Operations Center                    ║
    ║                    v{__version__}                              ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  The Guardian of WINDI Network                            ║
    ║  Sub-Agent #2 of WINDI Platform                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    config_path = os.environ.get('NOC_CONFIG', 'config/noc_config.yaml')

    agent = WindiNocAgent(config_path)

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
