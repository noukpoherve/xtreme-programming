# 📋 API Contracts - UrbanHub

## Alert Service (Port 8000)

### 📦 Models

#### AlertCreate - Create an alert
```json
{
  "alert_id": "a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p",
  "event_id": "e1e2e3e4-f1f2-4f3f-4f4f-5f5f6f6f7f7f",
  "sensor_id": "SEINE-001",
  "timestamp": "2026-06-30T12:00:00Z",
  "severity": "CRITICAL",
  "type": "ph",
  "message": "Critical pH detected: 5.2",
  "trace_id": "trace-xyz-123"
}
```

#### AlertUpdate - Update an alert
```json
{
  "severity": "WARNING",
  "message": "Alert updated",
  "metadata": {}
}
```

#### AlertDetail - Detail response
```json
{
  "alert_id": "a1b2c3d4",
  "event_id": "e1e2e3e4",
  "sensor_id": "SEINE-001",
  "timestamp": "2026-06-30T12:00:00Z",
  "severity": "CRITICAL",
  "type": "ph",
  "message": "Critical pH detected: 5.2",
  "trace_id": "trace-xyz"
}
```

#### AlertListResponse - Paginated list
```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "alerts": [
    {
      "alert_id": "a1b2c3d4",
      "event_id": "e1e2e3e4",
      "sensor_id": "SEINE-001",
      "timestamp": "2026-06-30T12:00:00Z",
      "severity": "CRITICAL",
      "type": "ph",
      "message": "Critical pH detected: 5.2",
      "trace_id": "trace-xyz"
    }
  ]
}
```

#### AlertStatsResponse - Statistics
```json
{
  "total_alerts": 1250,
  "critical_count": 45,
  "warning_count": 120,
  "by_sensor": {
    "SEINE-001": 320,
    "SEINE-002": 250,
    "MARNE-001": 180
  },
  "by_type": {
    "ph": 300,
    "turbidity": 450,
    "other": 500
  }
}
```

---

### 🔌 Endpoints

| Method | Endpoint | Description | Body | Response |
|--------|----------|-------------|------|----------|
| **POST** | `/alerts` | Create an alert | AlertCreate | AlertDetail |
| **GET** | `/alerts` | List alerts (pagination) | - | AlertListResponse |
| **GET** | `/alerts?option=stats` | Get alert statistics | - | AlertStatsResponse |
| **GET** | `/alerts/{alert_id}` | Get alert detail | - | AlertDetail |
| **GET** | `/alerts/sensor/{sensor_id}` | Get alerts by sensor | - | list[AlertDetail] |
| **PUT** | `/alerts/{alert_id}` | Update an alert | AlertUpdate | AlertDetail |
| **DELETE** | `/alerts/{alert_id}` | Delete an alert | - | {success: true} |

---

## IoT Service (Port 8001)

### 📦 Models

#### SensorCreate - Register a sensor
```json
{
  "sensor_id": "SEINE-001",
  "name": "Seine Sensor Pont Alma",
  "location": "Paris",
  "latitude": 48.8637,
  "longitude": 2.3017,
  "active": true,
  "metadata": {
    "model": "Hach",
    "version": "2.4.1"
  }
}
```

#### SensorUpdate - Update a sensor
```json
{
  "name": "Seine Sensor Pont Alma (Updated)",
  "active": false,
  "metadata": {}
}
```

#### SensorDetail - Sensor detail response
```json
{
  "sensor_id": "SEINE-001",
  "name": "Seine Sensor Pont Alma",
  "location": "Paris",
  "latitude": 48.8637,
  "longitude": 2.3017,
  "active": true,
  "metadata": {
    "model": "Hach"
  }
}
```

#### SensorListResponse - Sensors list
```json
{
  "total": 42,
  "sensors": [
    {
      "sensor_id": "SEINE-001",
      "name": "Seine Sensor Pont Alma",
      "location": "Paris",
      "latitude": 48.8637,
      "longitude": 2.3017,
      "active": true,
      "metadata": {}
    }
  ]
}
```

#### SensorStatsResponse - Sensor statistics
```json
{
  "total_sensors": 42,
  "active_sensors": 38,
  "inactive_sensors": 4,
  "last_update": "2026-06-30T12:00:00Z"
}
```

#### MeasurementResponse - Captured measurement
```json
{
  "sensor_id": "SEINE-001",
  "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": "2026-06-30T12:00:00Z",
  "ph": 7.4,
  "turbidity": 8.5,
  "level": 0.93,
  "flow": 252.0,
  "latitude": 48.8637,
  "longitude": 2.3017,
  "published": true
}
```

---

### 🔌 Endpoints

| Method | Endpoint | Description | Body | Response |
|--------|----------|-------------|------|----------|
| **POST** | `/sensors` | Register sensor | SensorCreate | {sensor_id, status} |
| **GET** | `/sensors` | List sensors | - | SensorListResponse |
| **GET** | `/sensors?option=stats` | Get sensor statistics | - | SensorStatsResponse |
| **GET** | `/sensors/{sensor_id}` | Get sensor detail | - | SensorDetail |
| **PUT** | `/sensors/{sensor_id}` | Update sensor | SensorUpdate | {sensor_id, status} |
| **DELETE** | `/sensors/{sensor_id}` | Delete sensor | - | {sensor_id, status} |
| **POST** | `/ingest` | Ingest from Hub'eau | - | MeasurementResponse |
| **POST** | `/simulate` | Simulate measurement | Query params | MeasurementResponse |

> Legacy aliases remain available for backward compatibility: `/alertes` maps to `/alerts`, and `/capteurs` maps to `/sensors`.

---

## 📝 HTTP Status Codes

| Code | Meaning |
|------|---------|
| **200** | ✅ OK - Request successful |
| **201** | ✅ Created - Resource created |
| **204** | ✅ No Content - Deletion successful |
| **400** | ❌ Bad Request - Invalid data |
| **404** | ❌ Not Found - Resource not found |
| **409** | ❌ Conflict - Resource already exists |
| **500** | ❌ Internal Server Error - Server error |

---

## 🧪 cURL Tests

### Alert Service

```bash
# Create an alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "a1",
    "event_id": "e1",
    "sensor_id": "SEINE-001",
    "timestamp": "2026-06-30T12:00:00Z",
    "severity": "CRITICAL",
    "type": "ph",
    "message": "Alert test",
    "trace_id": "t1"
  }'

# List alerts
curl http://localhost:8000/alerts

# Get stats
curl http://localhost:8000/alerts?option=stats

# Get alert by ID
curl http://localhost:8000/alerts/a1
```

### IoT Service

```bash
# Register a sensor
curl -X POST http://localhost:8001/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SEINE-001",
    "name": "Test Sensor",
    "location": "Paris",
    "latitude": 48.8637,
    "longitude": 2.3017,
    "active": true,
    "metadata": {}
  }'

# List sensors
curl http://localhost:8001/sensors

# Get stats
curl http://localhost:8001/sensors?option=stats

# Simulate measurement
curl -X POST "http://localhost:8001/simulate?ph=7.0&turbidity=10.0"
```

---

## 📚 Data Types

### Enums

#### Severity
- `CRITICAL` - Critical alert
- `WARNING` - Warning alert

#### Alert Type
- `ph` - pH out of range
- `turbidity` - Excessive turbidity
- `temperature` - Temperature anomaly
- `level` - Level anomaly
- `flow` - Flow anomaly

---

## 🔗 Access Links

- **Swagger Alert Service** : http://localhost:8000/docs
- **Swagger IoT Service** : http://localhost:8001/docs
- **OpenAPI JSON Alert** : http://localhost:8000/openapi.json
- **OpenAPI JSON IoT** : http://localhost:8001/openapi.json

---

**Date** : 30 June 2026  
**Version** : 2.0 (English)  
**Status** : Complete ✅
