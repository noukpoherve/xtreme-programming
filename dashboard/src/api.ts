/**
 * API client + WebSocket hook for UrbanHub.
 *
 * Uses /api/* proxy in dev (Vite proxies to alert-service:8000).
 */

import * as React from 'react';

const API_BASE = '/api';

export interface Sensor {
  sensor_id: string;
  state: 'NORMAL' | 'WARNING' | 'CRITICAL';
  anomaly_count: number;
  previous_state?: string | null;
}

export interface SensorMetadata {
  sensor_id: string;
  name: string;
  latitude: number;
  longitude: number;
  point_reference: string;
  state: 'NORMAL' | 'WARNING' | 'CRITICAL';
  anomaly_count: number;
  previous_state: 'NORMAL' | 'WARNING' | 'CRITICAL' | null;
  data_source: 'real' | 'simulated';
  firmware_version: string | null;
  last_measurement_at: string | null;
}

export interface MeasurementPoint {
  timestamp: string;
  ph: number;
  temperature_c: number;
  turbidity_ntu: number;
  dissolved_oxygen_mgl: number;
  level_m?: number;
  flow_m3s?: number;
  signal_quality: string | null;
}

export interface MeasurementSeries {
  sensor_id: string;
  hours: number;
  count: number;
  points: MeasurementPoint[];
}

export interface Stats {
  sensors_total: number;
  sensors_by_state: { NORMAL: number; WARNING: number; CRITICAL: number };
  alerts_open: number;
  alerts_last_24h: number;
  alerts_last_7d: number;
  top_sensors: Array<{ sensor_id: string; alert_count: number }>;
}

export interface Alert {
  id: string;
  severity: string;
  message: string;
  opened_at: string;
  sensor_id: string;
  sensor_name: string;
}

export interface WSEvent {
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface WSStateTransition {
  event_type: 'state_transition';
  data: {
    sensor_id: string;
    previous_state: 'NORMAL' | 'WARNING' | 'CRITICAL';
    new_state: 'NORMAL' | 'WARNING' | 'CRITICAL';
    anomaly_count: number;
  };
  timestamp: string;
}

export function isStateTransition(evt: WSEvent): evt is WSStateTransition {
  return evt.event_type === 'state_transition' && typeof evt.data === 'object' && evt.data !== null;
}

async function http<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${path}`);
  return r.json() as Promise<T>;
}

export const api = {
  health: () => http<{ status: string; version: string }>(`/health`),
  stats: () => http<Stats>(`/stats`),
  sensors: () => http<{ sensors: Sensor[]; count: number }>(`/sensors`),
  alerts: (limit = 50) => http<{ alerts: Alert[]; count: number }>(`/alerts?limit=${limit}`),
  // ── Drill-down ──
  sensorMetadata: (sensorId: string) =>
    http<SensorMetadata>(`/sensors/${encodeURIComponent(sensorId)}/metadata`),
  sensorMeasurements: (sensorId: string, hours = 24) =>
    http<MeasurementSeries>(
      `/sensors/${encodeURIComponent(sensorId)}/measurements?hours=${hours}`,
    ),
  sensorAlerts: (sensorId: string, limit = 20, onlyOpen = false) =>
    http<{ alerts: Alert[]; count: number }>(
      `/sensors/${encodeURIComponent(sensorId)}/alerts?limit=${limit}&only_open=${onlyOpen}`,
    ),
};

/**
 * Subscribe to the WebSocket /ws endpoint.
 * Returns the connection status.
 */
export function useWebSocket(onEvent: (evt: WSEvent) => void): { connected: boolean } {
  const [connected, setConnected] = React.useState(false);

  React.useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/api/stream`;
    let ws: WebSocket | null = null;
    let stopped = false;
    let retryDelay = 1000;

    const connect = () => {
      if (stopped) return;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        retryDelay = 1000;
      };
      ws.onmessage = (msg) => {
        try {
          const evt = JSON.parse(msg.data) as WSEvent;
          onEvent(evt);
        } catch {
          /* ignore malformed messages */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!stopped) {
          setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30000);
        }
      };
      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      stopped = true;
      ws?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { connected };
}