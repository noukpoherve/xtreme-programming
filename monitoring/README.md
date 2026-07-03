# 📊 monitoring

> Prometheus + Grafana + Loki + Promtail stack for the UrbanHub platform. Collects metrics, scrapes application endpoints, ships logs from all Docker containers, and renders ready-to-use dashboards.

---

## 🎯 Components

| Tool | Role | Port |
|------|------|:----:|
| **Prometheus** | Metrics scraping + alerting rules | 9090 |
| **Grafana** | Dashboards (pre-provisioned) | 3000 |
| **Loki** | Log aggregation | 3100 |
| **Promtail** | Docker log shipping → Loki | — |

---

## 🚀 Quick start

The stack is started automatically by `docker compose up`:

```bash
docker compose up -d prometheus grafana loki promtail
```

Open <http://localhost:3000> (login: **admin / admin**).

---

## 📁 Configuration

```
monitoring/
├── README.md                               ← you are here
├── prometheus.yml                          ← scrape config
├── promtail.yml                            ← Docker log shipping
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml             ← Prometheus + Loki auto-config
│       └── dashboards/
│           ├── dashboards.yml              ← provider config
│           └── urbanhub.json               ← UrbanHub dashboard
└── postgres/
    └── init/
        └── 01-init-extensions.sql          ← PostgreSQL schema + seeds
```

---

## 📈 Prometheus scrape config

Current targets (edit `prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Add application scrapes here (TODO: instrument alert-service, etc.)
  # - job_name: 'alert-service'
  #   static_configs:
  #     - targets: ['alert-service:8000']
```

**TODO** (next sprint): add `prometheus-fastapi-instrumentator` to each service so they expose `/metrics` automatically.

---

## 📜 Grafana dashboards

The UrbanHub dashboard is auto-loaded on Grafana startup. It includes:

- **System health**: container count, Kafka lag, PostgreSQL connections.
- **Logs**: application errors by service (via Loki).

> **TODO** (next sprint): add a custom dashboard with KPIs from `/stats` and live state distribution.

---

## 📦 Loki + Promtail

Promtail tails every Docker container's stdout/stderr and forwards logs to Loki. Grafana queries Loki via the provisioned datasource.

Log labels:
- `container` — container name (e.g. `alert-service`)
- `logstream` — `stdout` / `stderr`

Query in Grafana: `{container="alert-service"}`.

---

## 🔐 Production hardening (TODO)

- [ ] Replace `admin / admin` with a real auth provider (Keycloak, Auth0).
- [ ] Enable TLS on Grafana and Prometheus.
- [ ] Configure Loki S3 backend (instead of local filesystem).
- [ ] Add alerting rules to Prometheus (alertmanager).
- [ ] Set retention policies for Loki (90 days).

---

## 📜 License

MIT — see [LICENSE](../LICENSE).