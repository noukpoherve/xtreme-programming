import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { Sensor } from '../api';
import { stateColor } from '../lib/sensor-state';

interface Props {
  sensors: Sensor[];
  selectedSensorId?: string | null;
  onSensorClick: (sensorId: string) => void;
}

export default function SensorMap({ sensors, selectedSensorId, onSensorClick }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.CircleMarker>>(new globalThis.Map());

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;
    const map = L.map(mapRef.current, {
      center: [48.86, 2.34],
      zoom: 12,
      zoomControl: true,
      scrollWheelZoom: true,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 19,
    }).addTo(map);
    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
      markersRef.current.clear();
    };
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    if (!map) return;

    const currentIds = new Set<string>();

    sensors.forEach((sensor) => {
      const coords = SENSOR_COORDS[sensor.sensor_id];
      if (!coords) return;
      currentIds.add(sensor.sensor_id);

      const color = stateColor(sensor.state);
      const isSelected = selectedSensorId === sensor.sensor_id;
      const radius = isSelected ? 16 : sensor.state === 'CRITICAL' ? 13 : 9;
      const weight = isSelected ? 5 : 3;

      const existing = markersRef.current.get(sensor.sensor_id);
      if (existing) {
        existing.setStyle({
          color: isSelected ? '#ffffff' : color,
          fillColor: color,
          fillOpacity: 0.85,
          weight,
          radius,
        });
        existing.setPopupContent(popupHtml(sensor));
        existing.off('click');
        existing.on('click', () => {
          existing.closePopup();
          onSensorClick(sensor.sensor_id);
        });
      } else {
        const marker = L.circleMarker(coords, {
          radius,
          color: isSelected ? '#ffffff' : color,
          fillColor: color,
          fillOpacity: 0.85,
          weight,
        })
          .addTo(map)
          .bindPopup(popupHtml(sensor), {
            className: 'sensor-popup',
            closeButton: false,
          });
        marker.on('click', () => {
          marker.closePopup();
          onSensorClick(sensor.sensor_id);
        });
        markersRef.current.set(sensor.sensor_id, marker);
      }
    });

    for (const [id, marker] of markersRef.current.entries()) {
      if (!currentIds.has(id)) {
        marker.remove();
        markersRef.current.delete(id);
      }
    }
  }, [sensors, selectedSensorId, onSensorClick]);

  return <div ref={mapRef} className="w-full h-full" />;
}

function popupHtml(sensor: Sensor & { data_source?: string }): string {
  const isReal = sensor.data_source === 'real';
  const sourceBadge = isReal
    ? `<span style="display:inline-flex; align-items:center; gap:4px; padding:3px 8px; background:rgba(14,165,233,0.15); color:#7dd3fc; border:1px solid rgba(14,165,233,0.25); border-radius:6px; font-size:10px; font-weight:700;">🌐 Hub'Eau</span>`
    : `<span style="display:inline-flex; align-items:center; gap:4px; padding:3px 8px; background:rgba(100,116,139,0.15); color:#94a3b8; border:1px solid rgba(100,116,139,0.25); border-radius:6px; font-size:10px; font-weight:700;">🎲 Simulé</span>`;
  const color = stateColor(sensor.state);
  return `
    <div style="min-width: 220px;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
        <div style="font-weight: 800; font-size: 14px; color:#f8fafc;">${sensor.sensor_id}</div>
        ${sourceBadge}
      </div>
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
        <span style="
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: ${color};
          box-shadow: 0 0 8px ${color};
        "></span>
        <span style="font-weight: 700; color:${color}; text-transform:uppercase; font-size:12px; letter-spacing:0.05em;">${sensor.state}</span>
      </div>
      <div style="font-size: 12px; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
        Anomalies cumulées : <strong style="color:#e2e8f0;">${sensor.anomaly_count}</strong>
      </div>
      <div style="font-size: 11px; color: #64748b; margin-top: 8px; padding-top: 8px; border-top: 1px solid #1e293b;">
        Cliquez le marqueur pour voir le détail →
      </div>
    </div>
  `;
}

const SENSOR_COORDS: Record<string, [number, number]> = {
  'SEINE-VITRY-001': [48.7876, 2.3926],
  'SEINE-CHARENTON-002': [48.8207, 2.4151],
  'SEINE-BERCY-003': [48.8359, 2.3823],
  'SEINE-AUSTERLITZ-004': [48.8447, 2.3655],
  'SEINE-ILES-LOUVRE-005': [48.853, 2.347],
  'SEINE-CONCORDE-006': [48.8637, 2.3017],
  'SEINE-ALMA-007': [48.8637, 2.3017],
  'SEINE-TOUR-EIFFEL-008': [48.8584, 2.2945],
  'SEINE-IENA-009': [48.8597, 2.2923],
  'SEINE-BILLANCOURT-010': [48.8412, 2.2528],
  'SEINE-SURESNES-011': [48.8714, 2.2286],
  'SEINE-COLOMBES-012': [48.9135, 2.2546],
};
