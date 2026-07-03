# Services

UrbanHub est découpé en quatre composants principaux. Chaque service possède son propre `README.md` dans le dépôt ; les pages ci-dessous reprennent ces README directement.

| Service | Rôle | Technologies |
|---|---|---|
| [alert-service](alert-service.md) | Cerveau de la plateforme : consommation Kafka, machine à états, persistance, REST/WebSocket | FastAPI, asyncpg, aiokafka |
| [iot-service](iot-service.md) | Source de données : poll Hub'Eau + simulateur local | FastAPI, urllib, aiokafka |
| [dashboard](dashboard.md) | Interface temps réel : carte, KPIs, drill-down | React 19, Vite, Tailwind, Leaflet, Recharts |
| [monitoring](monitoring.md) | Observabilité : métriques, logs, dashboards | Prometheus, Grafana, Loki, Promtail |

!!! info "Liens relatifs"
    Les liens internes des README pointent vers les fichiers du dépôt GitHub. Si un lien semble cassé dans cette version web, consulte directement le fichier source sur le repository.
