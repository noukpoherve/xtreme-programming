# 🎨 dashboard

> Real-time SPA for UrbanHub. **Dashboard-first** layout: KPIs + map + drill-down drawer.
> Built with **React 19 + Vite + Tailwind + Leaflet + Recharts**. Real-time via WebSocket.

[![React 19](https://img.shields.io/badge/react-19-61dafb.svg)](https://react.dev/)
[![Vite 6](https://img.shields.io/badge/vite-6-646cff.svg)](https://vitejs.dev/)
[![Tailwind 3](https://img.shields.io/badge/tailwindcss-3-38bdf8.svg)](https://tailwindcss.com/)
[![Recharts 2](https://img.shields.io/badge/recharts-2-8884d8.svg)](https://recharts.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)

---

## 📋 Table of Contents

- [What it does](#-what-it-does)
- [Tech stack](#-tech-stack)
- [Layout](#-layout)
- [Drill-down drawer](#-drill-down-drawer)
- [Real-time updates](#-real-time-updates)
- [Project layout](#-project-layout)
- [API client](#-api-client)
- [Development](#-development)
- [Building for production](#-building-for-production)
- [Docker](#-docker)

---

## 🎯 What it does

The dashboard is the **front-end** of UrbanHub. Single-page application:

1. **Visualizes** all 12 sensors on an interactive Leaflet map of Paris (dark theme).
2. **Displays** KPI cards (sensors tracked, alerts open / 24h / 7d) and the top 5 alerting sensors.
3. **Receives** state transitions in real time via WebSocket (`/api/stream`) and refreshes the UI.
4. **Drill-down** per sensor (click a map marker, a row in the table, or a top-alerter chip) — opens a side drawer with:
   - Full sensor metadata (name, location, data source, firmware)
   - 24-hour time-series chart (pH, temperature, dissolved O₂)
   - Last 20 measurements in a table
   - Recent alerts scoped to that sensor

It's deliberately **lightweight** (no Redux, no React Router) — a single page with 1 drawer.

---

## 🛠️ Tech stack

| Library | Version | Role |
|---------|---------|------|
| React | 19 | UI |
| Vite | 6 | Bundler / dev server |
| TypeScript | 5 | Type safety |
| Tailwind | 3 | Styling (utility classes) |
| Leaflet | 1.9 | Map (raw, not via react-leaflet) |
| Recharts | 2 | Time-series chart |
| Nginx | (Docker) | Reverse proxy + SPA hosting |

---

## 🖼️ Layout

```
┌────────────────────────────────────────────────────────────┐
│  Header (sticky): 🌊 UrbanHub · pulse dot · Connected      │
├────────────────────────────────────────────────────────────┤
│  Event banner (only when a state_transition was received)  │
├────────────────────────────────────────────────────────────┤
│  StatsBar — 4 KPI cards (full width)                       │
├──────────────────────────────────┬─────────────────────────┤
│                                  │  RightRail              │
│  SensorMap (2/3, 600px)          │  - Capteurs par état    │
│  Click marker → drawer           │  - Top alerters (7j)    │
│                                  │  - Alertes récentes     │
├──────────────────────────────────┴─────────────────────────┤
│  SensorTable (full width, click row → drawer)              │
├────────────────────────────────────────────────────────────┤
│  Footer: version · counts                                   │
└────────────────────────────────────────────────────────────┘
```

Responsive: `grid-cols-1 lg:grid-cols-3`. On mobile (<1024px), the map stacks above the right rail; the drawer becomes a bottom sheet.

---

## 🔍 Drill-down drawer

Trigger sources (all set `selectedSensorId`):
- Click on a **Leaflet marker** on the map
- Click on a **row** in the bottom table
- Click on a sensor chip in the **Top alerters** widget
- Click on an alert in the **Alertes récentes** widget

The drawer (desktop: right slide-in `w-[560px]`, mobile: bottom sheet) contains:

1. **Header** — sensor_id, state pill, data-source badge (🌐 Hub'Eau / 🎲 Simulé), close button
2. **KPI strip** — 4 cells: pH, T°, turbidity, dissolved O₂ (latest values)
3. **MeasurementChart** — Recharts multi-line chart of the last 24h
4. **MeasurementTable** — last 20 measurements in a compact table
5. **SensorAlerts** — last 10 alerts for this sensor

Closing: click backdrop, press `Escape`, click the ✕ button.

Body scroll lock while open; focus management on the panel.

---

## ⚡ Real-time updates

- **WebSocket** connects to `ws://<host>/api/stream` (proxied by nginx to `alert-service:8000/stream`).
- On `welcome` event, the indicator turns green: "Temps réel · WS connecté".
- On every `state_transition` event, the dashboard re-fetches `/sensors`, `/stats`, `/alerts` (KISS — small JSON, fast network) and shows an event banner at the top.

### Initial load + polling

```ts
// App.tsx
useEffect(() => {
  load();                     // initial: sensors, stats, alerts in parallel
  setInterval(load, 10_000);  // refresh every 10s as a safety net
}, []);
```

---

## 📁 Project layout

```
dashboard/
├── README.md
├── package.json
├── postcss.config.js           ← tailwindcss + autoprefixer
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
├── nginx.conf                  ← reverse proxy /api/* → alert-service:8000
├── Dockerfile
├── index.html
└── src/
    ├── main.tsx                ← React 19 root
    ├── App.tsx                 ← layout + selectedSensorId
    ├── api.ts                  ← REST client + useWebSocket hook
    ├── index.css               ← Tailwind + dark theme + Leaflet styles
    ├── types.ts                ← shared types (extracted from api.ts)
    └── components/
        ├── Header.tsx
        ├── EventBanner.tsx
        ├── StatsBar.tsx
        ├── SensorMap.tsx
        ├── RightRail.tsx
        ├── SensorTable.tsx
        ├── Drawer.tsx
        └── sensor-detail/
            ├── SensorDetailDrawer.tsx
            ├── MeasurementChart.tsx
            ├── MeasurementTable.tsx
            └── SensorAlerts.tsx
```

---

## 🔌 API client (`api.ts`)

The client wraps the alert-service REST API:

```ts
api.health()                        // GET /health
api.stats()                         // GET /stats
api.sensors()                       // GET /sensors
api.alerts(limit = 50)              // GET /alerts?limit=...

// Drill-down
api.sensorMetadata(id)              // GET /sensors/{id}/metadata
api.sensorMeasurements(id, hours=24)// GET /sensors/{id}/measurements?hours=24
api.sensorAlerts(id, limit=20)      // GET /sensors/{id}/alerts?limit=20
```

The `useWebSocket(onEvent)` hook manages reconnection with exponential backoff (capped at 30s).

---

## 🛠️ Development

```bash
cd dashboard
npm install
npm run dev
# → http://localhost:5173
```

Vite proxies `/api/*` to `http://alert-service:8000` (see `vite.config.ts`), so the dev environment matches production.

---

## 🏗️ Building for production

```bash
npm run build       # → dist/
npm run preview     # local preview of the production build
```

The Docker build (`Dockerfile`) does:
1. `npm run build` → static assets in `dist/`
2. Serve with `nginx:alpine` + `nginx.conf` (which proxies `/api/*` to `alert-service:8000`)

---

## 🐳 Docker

```bash
docker compose up -d dashboard
```

Multi-stage build (Node 20 for build, nginx for serve). Rebuild after a frontend change:

```bash
docker compose build --no-cache dashboard
docker compose up -d --force-recreate dashboard
```

---

## 🎨 Custom Tailwind theme

Defined in `tailwind.config.js`:

- `ocean-{500,600,700,900}` — primary brand color
- `sensor.normal / warning / critical` — state colors (green / amber / red)
- `.card`, `.pill`, `.pulse-dot`, `.stat-value`, `.stat-label`, `.skeleton` — component utilities in `index.css`

---

## 🔗 See also

- [alert-service](../alert-service/) — backend that exposes the REST + WS APIs.
- [iot-service](../iot-service/) — produces the measurements.
- [docs/architecture.md](https://github.com/chrfsa/xtreme-programming/blob/main/docs/architecture.md) — system-wide architecture.
