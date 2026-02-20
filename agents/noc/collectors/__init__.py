# WINDI NOC Agent - Collectors Module
"""
Coletores de metricas para o NOC Agent

- prometheus_collector: Coleta metricas do Prometheus
- snmp_collector: Coleta via SNMP (equipamentos de rede)
- log_collector: Coleta e processa logs
- isp_collector: Integração com ISP Agent
"""

from typing import Dict, List, Any

__all__ = ['BaseCollector', 'PrometheusCollector']


class BaseCollector:
    """Base class for all collectors"""

    def __init__(self, config: Dict):
        self.config = config
        self.enabled = True

    def collect(self) -> List[Dict[str, Any]]:
        """Collect metrics - override in subclass"""
        raise NotImplementedError

    def validate(self) -> bool:
        """Validate collector configuration"""
        return True


class PrometheusCollector(BaseCollector):
    """Prometheus metrics collector"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.url = config.get('url', 'http://localhost:9090')

    def collect(self) -> List[Dict[str, Any]]:
        import requests
        metrics = []

        queries = {
            'cpu': '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
            'memory': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
            'disk': 'max(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100'
        }

        for name, query in queries.items():
            try:
                response = requests.get(
                    f"{self.url}/api/v1/query",
                    params={'query': query},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get('data', {}).get('result', []):
                        metrics.append({
                            'name': name,
                            'value': float(result['value'][1]),
                            'labels': result.get('metric', {})
                        })
            except Exception as e:
                print(f"Error collecting {name}: {e}")

        return metrics
