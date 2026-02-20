# WINDI NOC Agent - Analyzers Module
"""
Analisadores de dados para o NOC Agent

- anomaly_detector: Deteccao de anomalias com ML
- baseline_analyzer: Calculo e comparacao de baselines
- trend_analyzer: Analise de tendencias
- predictor: Previsao de falhas
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

__all__ = ['AnomalyDetector', 'BaselineAnalyzer', 'TrendAnalyzer']


@dataclass
class AnomalyResult:
    score: float  # 0-1, maior = mais anomalo
    is_anomaly: bool
    features: Dict[str, float]
    timestamp: datetime
    explanation: Optional[str] = None


class AnomalyDetector:
    """Detector de anomalias usando Isolation Forest"""

    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = None
        self.scaler = None
        self.is_fitted = False

        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            import numpy as np

            self.model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            self.scaler = StandardScaler()
            self.np = np
        except ImportError:
            print("Warning: sklearn not available")

    def fit(self, data: List[Dict[str, float]]) -> bool:
        """Treina o modelo com dados historicos"""
        if self.model is None:
            return False

        try:
            X = self._prepare_features(data)
            if X is not None and len(X) >= 50:
                X_scaled = self.scaler.fit_transform(X)
                self.model.fit(X_scaled)
                self.is_fitted = True
                return True
        except Exception as e:
            print(f"Fit error: {e}")

        return False

    def detect(self, metrics: Dict[str, float]) -> AnomalyResult:
        """Detecta se as metricas atuais sao anomalas"""
        if not self.is_fitted or self.model is None:
            return AnomalyResult(
                score=0,
                is_anomaly=False,
                features=metrics,
                timestamp=datetime.now(),
                explanation="Model not fitted"
            )

        try:
            X = self._prepare_features([metrics])
            X_scaled = self.scaler.transform(X)

            # Score: -1 (normal) to 1 (anomaly)
            raw_score = -self.model.decision_function(X_scaled)[0]
            score = max(0, min(1, (raw_score + 0.5)))

            is_anomaly = score > 0.7

            return AnomalyResult(
                score=score,
                is_anomaly=is_anomaly,
                features=metrics,
                timestamp=datetime.now(),
                explanation=f"Score {score:.2f}" + (" - ANOMALY" if is_anomaly else "")
            )
        except Exception as e:
            return AnomalyResult(
                score=0,
                is_anomaly=False,
                features=metrics,
                timestamp=datetime.now(),
                explanation=f"Error: {e}"
            )

    def _prepare_features(self, data: List[Dict[str, float]]) -> Optional[Any]:
        """Prepara features para o modelo"""
        if not data:
            return None

        features = ['cpu', 'memory', 'network_in', 'network_out', 'latency']
        rows = []

        for item in data:
            row = [item.get(f, 0) for f in features]
            rows.append(row)

        return self.np.array(rows)


class BaselineAnalyzer:
    """Analisador de baseline da rede"""

    def __init__(self, window_hours: int = 168):
        self.window_hours = window_hours
        self.baselines: Dict[str, Dict] = {}

    def update(self, metric_name: str, values: List[float]):
        """Atualiza baseline para uma metrica"""
        if not values:
            return

        try:
            import numpy as np
            self.baselines[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'p95': np.percentile(values, 95),
                'updated_at': datetime.now().isoformat()
            }
        except ImportError:
            self.baselines[metric_name] = {
                'mean': sum(values) / len(values),
                'std': 0,
                'min': min(values),
                'max': max(values),
                'p95': max(values),
                'updated_at': datetime.now().isoformat()
            }

    def compare(self, metric_name: str, value: float) -> Dict:
        """Compara valor atual com baseline"""
        if metric_name not in self.baselines:
            return {'deviation': 0, 'status': 'unknown'}

        baseline = self.baselines[metric_name]
        mean = baseline['mean']
        std = baseline['std'] or 1

        z_score = abs(value - mean) / std

        if z_score < 1:
            status = 'normal'
        elif z_score < 2:
            status = 'elevated'
        elif z_score < 3:
            status = 'high'
        else:
            status = 'critical'

        return {
            'value': value,
            'baseline_mean': mean,
            'deviation': z_score,
            'status': status
        }


class TrendAnalyzer:
    """Analisador de tendencias"""

    @staticmethod
    def calculate_trend(values: List[float]) -> Dict:
        """Calcula tendencia de uma serie temporal"""
        if len(values) < 2:
            return {'direction': 'stable', 'slope': 0}

        try:
            import numpy as np
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)

            if slope > 0.1:
                direction = 'increasing'
            elif slope < -0.1:
                direction = 'decreasing'
            else:
                direction = 'stable'

            return {
                'direction': direction,
                'slope': slope,
                'change_percent': (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0
            }
        except Exception:
            return {'direction': 'unknown', 'slope': 0}
