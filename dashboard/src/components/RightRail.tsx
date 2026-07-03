import { Stats, Alert, Sensor } from '../api';
import {
  SENSOR_STATES,
  stateBarStyle,
  stateColor,
  getStateTheme,
} from '../lib/sensor-state';

interface Props {
  stats: Stats | null;
  alerts: Alert[];
  sensors: Sensor[];
  onSensorClick: (sensorId: string) => void;
}

export default function RightRail({ stats, alerts, sensors, onSensorClick }: Props) {
  const totalSensors = stats?.sensors_total ?? sensors.length;

  return (
    <div className="space-y-4">
      {/* Capteurs par état */}
      <div className="card p-4 sm:p-5 rounded-xl">
        <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-4 font-bold">
          Capteurs par état
        </h3>
        <div className="space-y-4">
          {SENSOR_STATES.map((st) => {
            const count = stats?.sensors_by_state[st] ?? 0;
            const pct = totalSensors === 0 ? 0 : (count / totalSensors) * 100;
            const theme = getStateTheme(st);
            return (
              <div key={st}>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span
                    className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider"
                    style={{ color: theme.color }}
                  >
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{ background: theme.color }}
                    />
                    {st}
                  </span>
                  <span className="text-slate-300 font-mono tabular-nums">
                    {count} / {totalSensors}
                  </span>
                </div>
                <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${pct}%`, ...stateBarStyle(st) }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top alertes (7j) */}
      <div className="card p-4 sm:p-5 rounded-xl">
        <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-4 font-bold">
          Top capteurs alertés (7j)
        </h3>
        <div className="space-y-1">
          {(!stats?.top_sensors || stats.top_sensors.length === 0) && (
            <p className="text-sm text-slate-500 italic py-2">Aucune alerte récente</p>
          )}
          {stats?.top_sensors.map((s, i) => (
            <button
              key={s.sensor_id}
              onClick={() => onSensorClick(s.sensor_id)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800/50 transition group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-[10px] font-mono text-slate-500 w-5">#{i + 1}</span>
                <span className="text-sm font-mono text-slate-200 truncate group-hover:text-white">
                  {s.sensor_id.replace('SEINE-', '')}
                </span>
              </div>
              <span className="pill bg-rose-500/15 text-rose-300 border border-rose-500/20 font-mono">
                {s.alert_count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Alertes récentes (mini) */}
      {alerts.length > 0 && (
        <div className="card p-4 sm:p-5 rounded-xl">
          <h3 className="text-[11px] uppercase tracking-widest text-slate-500 mb-4 font-bold">
            Alertes récentes
          </h3>
          <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
            {alerts.slice(0, 5).map((a) => {
              const theme = getStateTheme(a.severity);
              return (
                <button
                  key={a.id}
                  onClick={() => onSensorClick(a.sensor_id)}
                  className="w-full text-left p-3 rounded-lg hover:bg-slate-800/50 transition border-l-2"
                  style={{
                    borderColor: theme.color,
                    background: theme.bg.replace('0.10', '0.04').replace('0.12', '0.04'),
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="text-[10px] font-bold uppercase tracking-wider"
                      style={{ color: theme.color }}
                    >
                      {a.severity}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 truncate">
                      {a.sensor_id.replace('SEINE-', '')}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {a.message}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
