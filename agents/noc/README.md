# WINDI NOC Agent

**Network Operations Center** - O Guardião da Rede WINDI

## Visao Geral

O NOC Agent e o segundo sub-agente do ecossistema WINDI, responsavel por:
- Monitoramento continuo da infraestrutura
- Deteccao de anomalias e padroes suspeitos
- Alertas inteligentes e resposta automatizada
- Aprendizado do comportamento normal da rede

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      WINDI NOC Agent                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Collectors  │  │  Analyzers  │  │  Alerting   │         │
│  │             │  │             │  │             │         │
│  │ - SNMP      │  │ - Anomaly   │  │ - Telegram  │         │
│  │ - Metrics   │  │ - Baseline  │  │ - Webhook   │         │
│  │ - Logs      │  │ - Predict   │  │ - Email     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │   Core DB   │                           │
│                   │ (TimeSeries)│                           │
│                   └─────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Stack Tecnologica

| Componente | Tecnologia | Funcao |
|------------|------------|--------|
| Metricas | Prometheus | Coleta e armazenamento |
| Logs | Loki | Agregacao de logs |
| Visualizacao | Grafana | Dashboards |
| Alertas | Alertmanager | Gestao de alertas |
| Analise | Python + Pandas | Deteccao de anomalias |
| ML | Scikit-learn | Previsao de falhas |

## Estrutura de Diretorios

```
noc/
├── config/              # Configuracoes do agente
├── collectors/          # Coletores de dados
├── analyzers/           # Analisadores e ML
├── alerting/            # Sistema de alertas
├── dashboards/          # Dashboards Grafana
├── data/                # Dados persistentes
├── logs/                # Logs do agente
├── docker-compose.yml   # Stack de monitoramento
└── noc_agent.py         # Agente principal
```

## Quick Start

```bash
# 1. Iniciar stack de monitoramento
cd /opt/windi/agents/noc
docker-compose up -d

# 2. Iniciar agente NOC
python3 noc_agent.py

# 3. Acessar dashboards
# Grafana: http://localhost:3000 (admin/windi123)
# Prometheus: http://localhost:9090
```

## Integracao com ISP WINDI

O NOC Agent consome dados do ISP Agent e fornece:
- Status de saude por ISP
- Alertas de degradacao
- Metricas de performance
- Previsoes de capacidade

## Endpoints

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/health` | GET | Status do agente |
| `/metrics` | GET | Metricas Prometheus |
| `/alerts` | GET | Alertas ativos |
| `/baseline` | GET | Baseline da rede |
| `/predict` | POST | Previsao de falhas |

## Configuracao

Edite `config/noc_config.yaml` para personalizar:
- Thresholds de alerta
- Canais de notificacao
- Intervalos de coleta
- Modelos de ML

## Roadmap

- [x] Estrutura base
- [x] Docker Compose stack
- [x] Coletor de metricas
- [x] Detector de anomalias
- [ ] Integracao Telegram
- [ ] Dashboard Grafana customizado
- [ ] Previsao de falhas com ML
- [ ] Auto-healing basico

---

**WINDI Platform** - Sub-Agent #2: NOC Agent v1.0.0
