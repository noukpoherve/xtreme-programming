import { useEffect, useState } from 'react';
import { api, SensorMetadata, MeasurementPoint, Alert as ApiAlert } from '../../api';
import { stateBadgeStyle, stateColor } from '../../lib/sensor-state';
import Drawer from '../Drawer';
import MeasurementChart from './MeasurementChart';
import MeasurementTable from './MeasurementTable';
import SensorAlerts from './SensorAlerts';

interface Props {
  sensorId: string | null;
  onClose: () => void;
}

export default function SensorDetailDrawer({ sensorId, onClose }: Props) {
  const [metadata, setMetadata] = useState<SensorMetadata | null>(null);
  const [measurements, setMeasurements] = useState<MeasurementPoint[]>([]);
  const [alerts, setAlerts] = useState<ApiAlert[]>([]);
  const [metaLoading, setMetaLoading] = useState(true);
  const [measLoading, setMeasLoading] = useState(true);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sensorId) return;
    let cancelled = false;

    setMetaLoading(true);
    setMeasLoading(true);
    setAlertsLoading(true);
    setError(null);

    (async () => {
      try {
        const [m, ms, al] = await Promise.all([
          api.sensorMetadata(sensorId),
          api.sensorMeasurements(sensorId, 24),
          api.sensorAlerts(sensorId, 10, false),
        ]);
        if (cancelled) return;
        setMetadata(m);
        setMeasurements(ms.points);
        setAlerts(al.alerts);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) {
          setMetaLoading(false);
          setMeasLoading(false);
          setAlertsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sensorId]);

  return (
    <Drawer open={!!sensorId} onClose={onClose} title={metadata?.name ?? 'Capteur'}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800/80 flex items-start justify-between bg-deep-800/50">
        <div className="flex-1 min-w-0">
          {metaLoading || !metadata ? (
            <div className="space-y-2">
              <div className="h-5 w-40 skeleton" />
              <div className="h-3 w-56 skeleton" />
            </div>
          ) : (
            <>
              <div className="flex items-center flex-wrap gap-2 mb-1">
                <h2 className="text-base font-extrabold text-white font-mono truncate">
                  {metadata.sensor_id}
                </h2>
                <span
                  className="inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border"
                  style={stateBadgeStyle(metadata.state)}
                >
                  {metadata.state}
                </span>
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    background: metadata.data_source === 'real' ? 'rgba(14,165,233,0.15)' : 'rgba(100,116,139,0.15)',
                    color: metadata.data_source === 'real' ? '#7dd3fc' : '#94a3b8',
                    border: `1px solid ${metadata.data_source === 'real' ? 'rgba(14,165,233,0.25)' : 'rgba(100,116,139,0.25)'}`,
                  }}
                >
                  {metadata.data_source === 'real' ? "🌐 Hub'Eau" : '🎲 Simulé'}
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate">
                {metadata.name} · {metadata.point_reference}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                {metadata.anomaly_count} anomalie(s) · firmware {metadata.firmware_version ?? '—'}
              </p>
            </>
          )}
        </div>
        <button
          onClick={onClose}
          className="ml-3 text-slate-500 hover:text-white hover:bg-slate-800 rounded p-1 text-xl leading-none transition"
          aria-label="Fermer"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="m-4 p-3 rounded-lg border border-rose-700/50 bg-rose-950/20 text-rose-200 text-sm">
            ⚠️ {error}
          </div>
        )}

        {!metaLoading && metadata && (
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 p-4 border-b border-slate-800/80">
            <KpiCell label="pH" value={measurements.at(-1)?.ph?.toFixed(2)} color="#38bdf8" />
            <KpiCell label="T°C" value={measurements.at(-1)?.temperature_c?.toFixed(1)} color="#34d399" />
            <KpiCell label="Turb." value={measurements.at(-1)?.turbidity_ntu?.toFixed(1)} color="#94a3b8" />
            <KpiCell label="O₂" value={measurements.at(-1)?.dissolved_oxygen_mgl?.toFixed(2)} color="#fbbf24" />
            <KpiCell label="Niveau" value={measurements.at(-1)?.level_m !== undefined ? `${measurements.at(-1)?.level_m?.toFixed(2)} m` : undefined} color="#a78bfa" />
            <KpiCell label="Débit" value={measurements.at(-1)?.flow_m3s !== undefined ? `${measurements.at(-1)?.flow_m3s?.toFixed(1)} m³/s` : undefined} color="#f472b6" />
          </div>
        )}

        <section className="p-4 border-b border-slate-800/80">
          <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-3 font-bold">
            Mesures — dernières 24h
          </h3>
          <MeasurementChart points={measurements} loading={measLoading} />
        </section>

        <section className="p-4 border-b border-slate-800/80">
          <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-3 font-bold">
            Mesures récentes
          </h3>
          <MeasurementTable points={measurements} loading={measLoading} />
        </section>

        <section className="p-4">
          <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-3 font-bold">
            Alertes du capteur
          </h3>
          <SensorAlerts alerts={alerts} loading={alertsLoading} />
        </section>
      </div>
    </Drawer>
  );
}

function KpiCell({ label, value, color }: { label: string; value?: string; color: string }) {
  return (
    <div className="bg-deep-700/40 rounded-lg p-2.5 border border-slate-800/80">
      <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1 font-bold">
        {label}
      </div>
      <div className="text-base sm:text-lg font-bold font-mono tabular-nums" style={{ color }}>
        {value ?? '—'}
      </div>
    </div>
  );
}
