# EC02 Analysis & Phase 3 Implementation Plan
## UrbanHub IRVE - Charging Stations Supervision Platform

**Session**: hans002  
**Date**: January 2025  
**Reference**: SOLAGNE/UH-IRVE/2026-014  
**Document Purpose**: Complete technical analysis of EC02 architecture and detailed implementation roadmap for charging stations dashboard and supervision services.

---

## Executive Summary

EC02 defines the **target architecture** for UrbanHub IRVE (Infrastructure de Recharge pour Véhicules Électriques) - a Smart City platform for **electric vehicle charging stations supervision and management** for Métropole de Solagne.

**Key Insight**: The system is fundamentally **event-driven, microservices-based**, and integrates with:
- OCPP protocol (charging stations communication)
- UrbanHub main platform (shared event bus, data warehouse, IAM)
- Payment providers (PSP integration)
- Real-time supervision dashboard for operators and end users

---

## 1. Project Context & Scope

### 1.1 What is IRVE?
IRVE = **Infrastructure de Recharge pour Véhicules Électriques** (EV Charging Infrastructure)

**Bornes de recharge** = charging points/stations with multiple connectors

### 1.2 Actors
- **Drivers/Users**: Reserve charging points, pay for sessions
- **Operators/Technicians**: Monitor network health, manage incidents
- **Elected Officials**: Access decision-support dashboards
- **System Admin**: Manage infrastructure, maintenance

### 1.3 External Systems
1. **Charging Stations** (OCPP protocol) - real-time events from bornes
2. **Payment Provider (PSP)** - process transactions, authorization
3. **Energy Management System** - consumption tracking, peak detection
4. **OCPI Networks** (roaming) - inter-network charging compatibility
5. **Notification Service** - alerts and messages
6. **UrbanHub Core Platform**:
   - Event bus (already exists - Kafka-based)
   - Data warehouse (for analytics)
   - IAM (authentication/authorization)

---

## 2. EC02 Architecture Overview (C4 Model)

### 2.1 Level 1: System Context
**External Stakeholders & Systems**:
```
Drivers ──────┐
Operators ────├──► [UrbanHub IRVE Platform] ──► Charging Bornes (OCPP)
Technicians ──┤                                │
Admins ───────┘                                ├──► Payment Provider
                                               ├──► Energy System
                                               └──► Roaming Networks (OCPI)
```

### 2.2 Level 2: Containers (Main Deployable Units)
The platform consists of **8 core containers**:

| Container | Purpose | Key Responsibility |
|-----------|---------|-------------------|
| **Front & Dashboard** | Web UI for users/operators | Real-time display of charger states, reservations, analytics |
| **API / Open Data** | Data exposure layer | REST APIs for front, third-party integrations, open data |
| **OCPP Gateway / Ingestion** | OCPP protocol handler | Real-time connection to charging bornes, event publication |
| **Supervision Service** | Network monitoring | Real-time status, cartography, health checks |
| **Reservation Service** | Booking system | Reserve charging points, manage queue, availability |
| **Payment Service** | Transaction processing | Session billing, PSP integration, compliance (PCI) |
| **Energy Service** | Power management | Consumption tracking, peak detection, load shedding |
| **Incidents/Alerts Service** | Incident management | Detect anomalies, qualify incidents, trigger notifications |

### 2.3 Level 3: Components (Service Internals - Hexagonal Architecture)

**Example: Session Service** (illustrates pattern for all services)
```
Domain Layer (Business Logic)
├── Session Entity
├── State Machine (Initiated → Authenticated → Active → Terminated → Billed)
├── Business Rules (pricing, idempotency, saga orchestration)
└── Ports (interfaces to external world)
    ├── Driving Adapter:
    │   ├── REST API (user commands)
    │   └── OCPP/WebSocket (charger events)
    └── Driven Adapter:
        ├── Repository (persistence)
        ├── Event Publisher (bus)
        ├── PSP Client (payment)
        └── OCPP Controller (charger commands)
```

**Benefit**: Domain is **testable independently**, technologies are **swappable**.

---

## 3. Primary Data Flows

### 3.1 Real-Time Ingestion Flow
```
Charging Borne (OCPP events)
    ↓
OCPP Gateway / Ingestion Service
    ↓
Event Bus (Kafka topic: `charge.station.events`)
    ↓
Supervision Service → Real-time map
Energy Service → Consumption tracking
Incidents Service → Anomaly detection
    ↓
Data Warehouse (historization)
```

### 3.2 Charging Session Flow (User perspective)
```
1. User finds borne on mobile app
2. Reservation request → Reservation Service
3. Payment pre-authorization → Payment Service → PSP
4. Start charging → Session Service → OCPP Gateway → Borne
5. Real-time monitoring → Dashboard gets updates via WebSocket
6. Stop charging → OCPP Gateway receives StopTransaction
7. Session finalized → Billing → Payment confirmation
```

### 3.3 Dashboard Real-Time Updates
```
Services publish events to:
    ├── `charge.session.started`
    ├── `charge.session.stopped`
    ├── `borne.state.changed` (available/reserved/charging/maintenance)
    ├── `borne.health.degraded`
    └── `incident.detected`
        ↓
Dashboard WebSocket subscriptions
    ↓
Users/Operators see instant updates (no polling)
```

---

## 4. Lifecycle & State Machines

### 4.1 Charging Borne States
```
Available → Reserved → Charging → Available
    ↓                               ↓
Available ← Maintenance ← Out of Service
    ↓
Reserved → In Charge → Available
```

**Triggered by OCPP messages**:
- `StatusNotification` → borne availability change
- `StartTransaction` → session started
- `StopTransaction` → session ended
- Health checks → detect out-of-service states

### 4.2 Charging Session States
```
Initiated (reservation created)
    ↓
Authenticated (payment authorized)
    ↓
Active (charging in progress)
    ↓
Terminated (user stopped or borne stopped)
    ↓
Billed (amount charged to payment method)
    ↓
Archived (or Failed if billing error)
```

---

## 5. Design Patterns & Resilience Strategies

### 5.1 Core Patterns (from EC02)

| Pattern | Role | Example |
|---------|------|---------|
| **Adapter (Adapter)** | Isolate domain from OCPP/PSP/persistence | OCPP Adapter handles WebSocket, parser |
| **Repository** | Persist and retrieve domain objects | ChargingBorneRepository, SessionRepository |
| **Strategy** | Swap pricing logic (per kWh, per hour, subscription) | PricingStrategy interface |
| **Observer/Events** | Decouple services via events | SessionStarted event published, Supervision subscribes |
| **Circuit Breaker + Retry** | Handle faults gracefully | OCPP command fails → exponential backoff |
| **Saga** | Multi-step transactions with compensation | Start charging: borne + payment in sync |
| **API Gateway** | Single entry point for auth, rate limiting | Routes to services, enforces policies |
| **Idempotency** | Safe retries of critical operations | Session start idempotent by session_id |

### 5.2 Resilience Tactics
- **Multi-zone redundancy** → services deployed across zones
- **Stateless services** → horizontal scaling
- **Circuit breaker** → protect calls to OCPP/PSP
- **Retry with exponential backoff** → transient faults
- **Saga pattern** → distributed transactions with compensation
- **Dead-letter queues** → handle poison messages
- **Graceful degradation** → show cached data if service unavailable

---

## 6. Technical Orientations (EC02 Guidance)

### 6.1 Execution Layer
- **Containerization**: Services as Docker containers
- **Orchestration**: Cloud-native deployment (Kubernetes or similar)
- **Networking**: API Gateway for routing, mTLS for service-to-service

### 6.2 Messaging & Events
- **Event Bus**: Kafka (shared UrbanHub infrastructure)
- **Topics to define**:
  - `charge.station.events` (OCPP events)
  - `charge.session.lifecycle` (session state changes)
  - `charge.payment.events` (payment authorization, settlement)
  - `charge.energy.consumption` (power usage)
  - `charge.incidents.detected` (anomalies)

### 6.3 Data Storage
- **Time Series**: Charging sessions, power consumption, pricing history
- **Relational**: Borne catalog, user reservations, payment records
- **Data Warehouse**: UrbanHub shared warehouse for analytics/BI

### 6.4 Observability
- **Centralized Logging**: All service logs aggregated
- **Metrics**: Prometheus-compatible (availability, latency, errors)
- **Tracing**: Distributed traces across services (OpenTelemetry)
- **SLO Target**: ~99.5% availability
- **Dashboards**: Grafana for ops, custom BI for business metrics

### 6.5 Security & Compliance
- **Auth**: IAM (UrbanHub shared)
- **API Protection**: Rate limiting, DDoS protection
- **Payment**: PCI-DSS compliance (isolated payment service)
- **Data**: GDPR compliance (data minimization, retention policies)
- **Encryption**: TLS in transit, encryption at rest

---

## 7. Integration with UrbanHub Core Platform

The IRVE platform **reuses UrbanHub's shared infrastructure**:

1. **Event Bus** (Kafka)
   - IRVE publishes charging events
   - Data module subscribes for analytics
   - IA/MLOps module can analyze usage patterns

2. **Data Warehouse**
   - IRVE services write to shared warehouse
   - BI tools query for decision support
   - No duplicate data stores

3. **IAM (Identity & Access Management)**
   - Single sign-on for all UrbanHub modules
   - Role-based access control
   - User profiles, authentication tokens

4. **API Registry / Contracts**
   - All IRVE APIs documented and versioned
   - Other UrbanHub modules discover and call IRVE APIs
   - Open Data API exposes public charging data

---

## 8. Architectural Decisions (ADRs) from EC02

| ADR | Decision | Rationale | Impact |
|-----|----------|-----------|--------|
| **ADR-1** | Microservices | Autonomy, scalability, evolution | Manage integration complexity |
| **ADR-2** | Event-driven ingestion | Real-time, decoupling | Message broker as critical component |
| **ADR-3** | OCPP protocol | Multi-vendor charger compatibility | Protocol parsing complexity |
| **ADR-4** | Reuse UrbanHub | Cohesion, shared costs | Dependency on core platform |
| **ADR-5** | Payment isolation | PCI-DSS compliance | Separate payment service required |
| **ADR-6** | Hexagonal architecture | Testability, technology switching | Discipline in port design |
| **ADR-7** | Circuit breaker + saga | Handle faults, distributed transactions | Increased complexity, need monitoring |
| **ADR-8** | Observability + SLO | Detect issues, measure reliability | Comprehensive instrumentation needed |
| **ADR-9** | API-first, versioned | Openness, integration | Contract governance required |

---

## 9. Phase 3 Implementation Plan: Charging Stations Supervision Dashboard

### 9.1 Scope
Build the **backend foundation** for the dashboard to display real-time charging station supervision data.

**Focus**: Supervision Service + data flow from OCPP Gateway

### 9.2 Key Deliverables

#### 9.2.1 Data Models & Contracts

**Charging Borne (Station)**
```python
class ChargingBorne:
    id: str                           # e.g., "FR-SOLAGNE-0001"
    name: str                         # e.g., "Square République"
    latitude: float
    longitude: float
    address: str
    num_connectors: int
    connectors: List[Connector]
    status: BorneStatus              # available, reserved, charging, maintenance
    health: BorneHealth              # ok, degraded, failed
    last_updated: datetime
    sessions_active: List[SessionId]
```

**Connector**
```python
class Connector:
    id: str                          # e.g., "CONN-001"
    type: ConnectorType              # Type2, ChadeMO, CCS
    status: ConnectorStatus          # free, occupied, reserved
    session_id: Optional[SessionId]
    power_kw: float                  # available power
```

**Charging Session**
```python
class ChargingSession:
    id: str                          # session_id from OCPP
    borne_id: str
    connector_id: str
    user_id: str
    status: SessionStatus            # initiated, active, terminated, billed
    start_time: datetime
    end_time: Optional[datetime]
    energy_kwh: float
    duration_minutes: int
    cost_eur: float
    payment_status: PaymentStatus   # pending, authorized, charged, failed
```

**Supervision Dashboard State**
```python
class DashboardState:
    timestamp: datetime
    total_bornes: int
    available_count: int
    reserved_count: int
    charging_count: int
    maintenance_count: int
    active_sessions: int
    energy_total_kwh: float          # today
    revenue_eur: float               # today
    incident_count: int
    bornes_by_status: Dict[BorneStatus, int]
    recent_incidents: List[Incident]
    network_health: HealthScore     # 0-100
```

#### 9.2.2 API Endpoints (Supervision Service)

**GET /bornes**
- Returns list of all charging stations
- Query params: status filter, geo-bounds, available_only
- Response: List[ChargingBorne]

**GET /bornes/{borne_id}**
- Details of one borne with active sessions
- Response: ChargingBorne + active sessions

**GET /sessions**
- List active sessions
- Query: borne_id, status filter, limit
- Response: List[ChargingSession]

**GET /dashboard/summary**
- Real-time supervision overview
- Response: DashboardState (counts, aggregates)

**GET /dashboard/map**
- Borne positions + current status for map display
- Response: List[{id, lat, long, status, connector_count, available_count}]

**WebSocket /ws/dashboard/live**
- Subscribe to real-time updates
- Messages: borne status changes, session start/stop, incidents
- Auto-reconnect, heartbeat

**GET /incidents**
- Recent incidents (failures, maintenance, anomalies)
- Response: List[Incident] with severity

**GET /analytics/daily**
- Daily aggregates: sessions, energy, revenue
- Query: date range
- Response: time-series data for charting

#### 9.2.3 Kafka Topics & Event Contracts

**Topic: `charge.station.events`**
```json
{
  "event_type": "borne_status_changed",
  "borne_id": "FR-SOLAGNE-0001",
  "status": "charging",
  "timestamp": "2025-01-20T14:23:45Z",
  "previous_status": "available",
  "connector_id": "CONN-001",
  "session_id": "SESSION-12345"
}
```

**Topic: `charge.session.lifecycle`**
```json
{
  "event_type": "session_started",
  "session_id": "SESSION-12345",
  "borne_id": "FR-SOLAGNE-0001",
  "user_id": "USER-789",
  "start_time": "2025-01-20T14:00:00Z"
}
```

#### 9.2.4 Supervision Service Implementation

**Main Responsibilities**:
1. **Consume OCPP events** from `charge.station.events` Kafka topic
2. **Maintain real-time state** of all bornes and sessions in memory cache + DB
3. **Expose supervision APIs** for dashboard consumption
4. **Detect incidents** (offline bornes, failed transactions, energy anomalies)
5. **Push updates** via WebSocket to connected dashboard clients

**Technology Stack** (to justify):
- **Framework**: FastAPI (async, WebSocket support, performance)
- **Cache**: Redis (real-time borne/session state, WebSocket connection management)
- **Database**: PostgreSQL (persistence, complex queries for analytics)
- **Event Processing**: Kafka Consumer (Spring Boot or asyncio)
- **Real-time**: WebSocket (FastAPI + python-socketio or raw WebSocket)

**Architecture**:
```
OCPP Gateway → Kafka Topic
    ↓
Supervision Service (FastAPI)
    ├─ Kafka Consumer Thread
    │  └─ Updates Redis cache + PostgreSQL
    ├─ REST API Handlers
    │  └─ Query Redis for real-time data
    └─ WebSocket Manager
       └─ Broadcast state changes to connected clients
```

#### 9.2.5 Dashboard Backend Integration

**Session Planning** (what the dashboard needs):
1. **Real-time map** of bornes with status colors
   - API: `GET /dashboard/map` with auto-refresh or WebSocket
   
2. **Borne details panel**
   - API: `GET /bornes/{id}` + active sessions
   
3. **Session list** (filtering, sorting)
   - API: `GET /sessions?status=active`
   
4. **Summary tiles** (available, charging, incidents)
   - API: `GET /dashboard/summary` (cache for 5-10 seconds)
   
5. **Incidents log**
   - API: `GET /incidents?limit=20`
   
6. **Charts/Analytics** (daily usage, revenue)
   - API: `GET /analytics/daily?start=2025-01-01&end=2025-01-31`

**Frontend Communication** (anticipated):
- Dashboard calls REST APIs for data
- WebSocket for real-time updates
- Handle network reconnection gracefully
- Cache state locally, show loading indicators during refresh

---

## 10. Implementation Roadmap

### Phase 3a: Foundation (Week 1)
- [ ] Create Supervision Service skeleton (FastAPI)
- [ ] Define Pydantic data models (Borne, Session, DashboardState, etc.)
- [ ] Create PostgreSQL schema for bornes, sessions, incidents
- [ ] Implement Kafka consumer for OCPP events
- [ ] Set up Redis for caching

### Phase 3b: Core APIs (Week 2)
- [ ] Implement REST endpoints: `/bornes`, `/bornes/{id}`, `/sessions`
- [ ] Implement `/dashboard/summary` and `/dashboard/map`
- [ ] Add incident detection logic
- [ ] Add pagination, filtering, sorting
- [ ] Test with mock Kafka events

### Phase 3c: Real-Time Features (Week 3)
- [ ] Implement WebSocket `/ws/dashboard/live`
- [ ] Test subscription/broadcast logic
- [ ] Connection pool management
- [ ] Heartbeat/reconnection

### Phase 3d: Analytics & Monitoring (Week 4)
- [ ] Analytics APIs (`/analytics/daily`)
- [ ] Add Prometheus metrics
- [ ] Logging (structured, correlation IDs)
- [ ] SLO instrumentation

### Phase 3e: Integration & Testing (Week 5)
- [ ] End-to-end tests with fake OCPP events
- [ ] Load testing (concurrent WebSocket clients)
- [ ] Error handling & resilience testing
- [ ] Integration with UrbanHub event bus

### Phase 3f: Documentation & Handoff (Week 6)
- [ ] OpenAPI/Swagger docs
- [ ] Deployment guide
- [ ] Operations runbook
- [ ] Handoff to dashboard frontend team

---

## 11. Technology Choices (to be Justified)

### 11.1 Core Stack
- **Language**: Python 3.12 (consistency with IoT/Alert services)
- **Web Framework**: FastAPI (async, WebSocket native, auto docs)
- **Async Runtime**: asyncio (built-in, no additional dependency)
- **Database**: PostgreSQL (mature, ACID, geospatial queries, analytics)
- **Cache**: Redis (high performance, pub/sub, native WebSocket support)
- **Message Broker**: Kafka (existing UrbanHub infrastructure)
- **Containerization**: Docker (existing workflow)

### 11.2 Libraries (to add to requirements)
- `pydantic` (data validation) - already used
- `sqlalchemy` (ORM for PostgreSQL)
- `redis` (Redis client, caching)
- `kafka-python` (Kafka consumer)
- `python-socketio` (WebSocket support) or raw `websockets`
- `geoalchemy2` (geospatial queries)
- `prometheus-client` (metrics)
- `python-json-logger` (structured logging)

---

## 12. Known Constraints & Open Questions

### Constraints from EC02
1. **Multi-vendor bornes**: Must support multiple OCPP-compliant vendors
2. **PCI-DSS**: Payment data must stay in isolated service (not Supervision Service)
3. **99.5% availability** SLO: Requires redundancy, circuit breakers, observability
4. **GDPR**: Don't store unnecessary user PII, respect retention policies
5. **Sobriété Numérique**: Limit message volumes, optimize queries

### Open Questions (for Dashboard Frontend Team)
1. **Update frequency**: How often does the map refresh? (real-time WebSocket vs polling?)
2. **Historical data**: Do we need to show past sessions/incidents in dashboard?
3. **Geo-bounds filter**: Which map library on frontend? (Leaflet, Mapbox, etc.)
4. **Filtering criteria**: Priority incidents, specific borne types, availability zones?
5. **Performance SLA**: How many concurrent users on dashboard?
6. **Alerting**: Should dashboard trigger alerts, or separate notification service?

---

## 13. Deliverables for This Session (hans002)

### 13.1 Code (to commit & push)
- [ ] `supervision-service/` directory structure
- [ ] `supervision-service/src/supervision_service/`
  - [ ] `main.py` (FastAPI app setup)
  - [ ] `contracts.py` (Pydantic models)
  - [ ] `models.py` (SQLAlchemy ORM)
  - [ ] `kafka_consumer.py` (OCPP event processor)
  - [ ] `api_handlers.py` (REST endpoints)
  - [ ] `websocket_manager.py` (WebSocket subscriptions)
  - [ ] `incident_detector.py` (anomaly detection)
- [ ] `supervision-service/requirements.txt`
- [ ] `supervision-service/Dockerfile`
- [ ] `docker-compose.yml` (updated to include supervision service)
- [ ] `tests/` (unit tests for models, incident detection)

### 13.2 Documentation (to commit & push)
- [ ] `SUPERVISION_SERVICE_README.md` (service overview, running locally)
- [ ] `API_SPECIFICATION.md` (OpenAPI/Swagger docs)
- [ ] `EVENT_SCHEMAS.md` (Kafka topic contracts)
- [ ] `DATA_MODEL.md` (ER diagram, schema definitions)

### 13.3 Local Session Documents (NOT pushed to GitHub)
- [ ] `SESSION_DECISIONS.md` (technology choices justified)
- [ ] `INTEGRATION_CHECKLIST.md` (what frontend team needs)
- [ ] `NEXT_SESSION_HANDOFF.md` (continuation guide for next phase)

---

## 14. Next Steps After hans002

### 14.1 Phase 3b: Dashboard Frontend (on separate branch)
- Implement React/Vue components for map, panels, real-time updates
- Connect to Supervision Service APIs
- WebSocket client for live updates

### 14.2 Phase 3c: Incident Service (on separate branch)
- Anomaly detection algorithms
- Alert generation and notification
- Integration with notification service

### 14.3 Phase 4: Payment Service Integration
- PCI-DSS compliant payment processing
- Session billing automation
- Saga pattern for distributed transactions

### 14.4 Phase 5: Energy Management
- Power consumption tracking
- Peak detection and load shedding
- Integration with energy provider systems

---

## 15. Key Takeaways for Implementation

✅ **IRVE is event-driven**: All state changes flow through Kafka  
✅ **Hexagonal architecture**: Services must isolate domain from protocols (OCPP, PSP)  
✅ **Real-time supervision**: Dashboard needs WebSocket for instant updates, not polling  
✅ **Resilience critical**: Circuit breakers, retries, idempotence for OCPP/payment calls  
✅ **Observability essential**: 99.5% SLO requires comprehensive instrumentation  
✅ **Integration-heavy**: Supervision Service is the "hub" connecting OCPP, energy, payment  
✅ **Testability first**: Hexagonal design allows testing domain logic without external dependencies  

---

## Appendix A: Glossary

- **OCPP**: Open Charge Point Protocol (standard for charger ↔ server communication)
- **OCPI**: Open Charge Point Interface (standard for roaming between networks)
- **PSP**: Payment Service Provider
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **RGPD**: GDPR in French (Règlement Général sur la Protection des Données)
- **SLO**: Service Level Objective (target availability/performance)
- **Saga**: Distributed transaction pattern with compensation
- **Circuit Breaker**: Fault tolerance pattern (fail fast before cascading)
- **Idempotency**: Operation produces same result regardless of how many times it's executed
- **WebSocket**: Bi-directional communication protocol (low-latency real-time)

---

## Appendix B: References from EC02

- Reference: SOLAGNE/UH-IRVE/2026-014
- Source: EC02 - Kit de démarrage (7-page architecture document)
- Document Classification: Confidentiel EADL - RNCP39765
- Architecture baseline from EC01 (pre-study)

---

**End of Document**

*This plan is a living document. Update as implementation progresses and questions are resolved.*
