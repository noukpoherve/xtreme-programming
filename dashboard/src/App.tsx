import * as React from 'react';
import { api, useWebSocket, Sensor, Stats, Alert, WSEvent, isStateTransition } from './api';
import Header from './components/Header';
import EventBanner from './components/EventBanner';
import StatsBar from './components/StatsBar';
import SensorMap from './components/SensorMap';
import RightRail from './components/RightRail';
import SensorTable from './components/SensorTable';
import SensorDetailDrawer from './components/sensor-detail/SensorDetailDrawer';

export default function App() {
  const [sensors, setSensors] = React.useState<Sensor[]>([]);
  const [stats, setStats] = React.useState<Stats | null>(null);
  const [alerts, setAlerts] = React.useState<Alert[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [lastEvent, setLastEvent] = React.useState<string | null>(null);
  const [selectedSensorId, setSelectedSensorId] = React.useState<string | null>(null);

  // Initial + periodic load
  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, st, a] = await Promise.all([
          api.sensors(),
          api.stats(),
          api.alerts(50),
        ]);
        if (!cancelled) {
          setSensors(s.sensors);
          setStats(st);
          setAlerts(a.alerts);
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    }
    load();
    const interval = setInterval(load, 10_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // WebSocket: patch state locally on every transition — truly real-time.
  const { connected } = useWebSocket(
    React.useCallback((evt: WSEvent) => {
      if (!isStateTransition(evt)) return;

      const { sensor_id, previous_state, new_state, anomaly_count } = evt.data;
      setLastEvent(`${sensor_id}: ${previous_state} → ${new_state}`);

      // 1. Patch the sensor in-place (no full refetch)
      setSensors((prev) =>
        prev.map((s) =>
          s.sensor_id === sensor_id
            ? {
                ...s,
                state: new_state,
                previous_state: previous_state,
                anomaly_count,
              }
            : s,
        ),
      );

      // 2. Patch stats counts in-place
      setStats((prev) => {
        if (!prev) return prev;
        const by_state = { ...prev.sensors_by_state };
        by_state[previous_state] = Math.max(0, by_state[previous_state] - 1);
        by_state[new_state] = (by_state[new_state] ?? 0) + 1;
        return { ...prev, sensors_by_state: by_state };
      });

      // 3. Refetch only alerts (we don't have the alert payload in the WS event)
      api.alerts(50)
        .then((r) => setAlerts(r.alerts))
        .catch(() => {});
    }, []),
  );

  const openSensor = React.useCallback((sensorId: string) => {
    setSelectedSensorId(sensorId);
  }, []);
  const closeSensor = React.useCallback(() => {
    setSelectedSensorId(null);
  }, []);

  return (
    <div className="min-h-screen flex flex-col relative overflow-x-hidden">
      {/* Atmospheric background */}
      <div className="fixed inset-0 -z-10 bg-deep-900" />
      <div
        className="fixed inset-0 -z-10 opacity-30"
        style={{
          backgroundImage:
            'radial-gradient(circle at 20% 0%, rgba(14, 165, 233, 0.18), transparent 45%), radial-gradient(circle at 80% 100%, rgba(251, 113, 133, 0.10), transparent 40%)',
        }}
      />
      <div
        className="fixed inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(148, 163, 184, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.5) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <Header connected={connected} stats={stats} sensorCount={sensors.length} />
      <EventBanner lastEvent={lastEvent} onDismiss={() => setLastEvent(null)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        {error && (
          <div className="card p-4 border-rose-500/30 bg-rose-950/20 rounded-xl">
            <p className="text-rose-200 text-sm font-medium">⚠️ {error}</p>
          </div>
        )}

        <StatsBar stats={stats} sensors={sensors} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          <div className="lg:col-span-2 card card-glow p-1 h-[520px] sm:h-[580px] flex flex-col rounded-2xl">
            <div className="px-4 py-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2 font-display">
                <span>🗺️</span> Carte des capteurs · Seine
              </h2>
              <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">
                Cliquez un marqueur pour le détail
              </span>
            </div>
            <div className="flex-1 rounded-xl overflow-hidden min-h-0 px-1 pb-1">
              <SensorMap
                sensors={sensors}
                selectedSensorId={selectedSensorId}
                onSensorClick={openSensor}
              />
            </div>
          </div>

          <RightRail
            stats={stats}
            alerts={alerts}
            sensors={sensors}
            onSensorClick={openSensor}
          />
        </div>

        <SensorTable sensors={sensors} onSensorClick={openSensor} />
      </main>

      <footer className="border-t border-slate-800/60 bg-deep-900/60 backdrop-blur-md py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
          <span className="font-medium tracking-wide">UrbanHub v0.1.0 · EC01 Architecture · Master EADL</span>
          <span className="font-mono">
            {sensors.length} capteurs · {stats?.alerts_open ?? 0} alertes ouvertes
          </span>
        </div>
      </footer>

      <SensorDetailDrawer
        sensorId={selectedSensorId}
        onClose={closeSensor}
      />
    </div>
  );
}
