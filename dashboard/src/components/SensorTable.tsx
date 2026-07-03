import * as React from 'react';
import { Sensor } from '../api';
import { sortBySeverity, stateBadgeStyle, stateDotStyle, stateColor } from '../lib/sensor-state';

interface Props {
  sensors: Sensor[];
  onSensorClick: (sensorId: string) => void;
}

export default function SensorTable({ sensors, onSensorClick }: Props) {
  const sorted = sortBySeverity(sensors);

  return (
    <div className="card overflow-hidden rounded-xl">
      <div className="px-5 py-3.5 border-b border-slate-800/80 flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2 font-display">
          <span>📡</span> Tous les capteurs
        </h2>
        <span className="text-[11px] text-slate-500 font-mono uppercase tracking-wider">
          {sensors.length} capteurs
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-deep-700/50 text-[10px] uppercase tracking-widest text-slate-500">
            <tr>
              <th className="text-left px-5 py-3 font-bold">Capteur</th>
              <th className="text-left px-5 py-3 font-bold">État</th>
              <th className="text-left px-5 py-3 font-bold">Anomalies</th>
              <th className="text-left px-5 py-3 font-bold hidden sm:table-cell">Précédent</th>
              <th className="text-right px-5 py-3 font-bold"></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => {
              const color = stateColor(s.state);
              return (
                <tr
                  key={s.sensor_id}
                  onClick={() => onSensorClick(s.sensor_id)}
                  className="border-t border-slate-800/60 hover:bg-ocean-500/5 cursor-pointer transition-colors group"
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <span
                        className="inline-block w-2 h-2 rounded-full"
                        style={stateDotStyle(s.state)}
                      />
                      <span className="font-mono text-slate-200 text-xs sm:text-sm">
                        {s.sensor_id}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border"
                      style={stateBadgeStyle(s.state)}
                    >
                      {s.state}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-300 tabular-nums">
                    {s.anomaly_count}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-500 text-xs hidden sm:table-cell">
                    {s.previous_state ?? '—'}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-slate-600 group-hover:text-ocean-300 text-xs font-semibold transition">
                      Voir →
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
