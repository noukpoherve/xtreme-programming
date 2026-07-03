import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { MeasurementPoint } from '../../api';

interface Props {
  points: MeasurementPoint[];
  loading?: boolean;
}

export default function MeasurementChart({ points, loading }: Props) {
  const data = useMemo(
    () =>
      points.map((p) => ({
        time: new Date(p.timestamp).getTime(),
        ph: p.ph,
        temp: p.temperature_c,
        o2: p.dissolved_oxygen_mgl,
        turb: p.turbidity_ntu,
      })),
    [points],
  );

  if (loading) {
    return <div className="h-64 skeleton" />;
  }
  if (data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 text-sm italic">
        Aucune mesure disponible sur cette période
      </div>
    );
  }

  const tickFmt = (t: number) =>
    new Date(t).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  const tooltipFmt = (t: number) => new Date(t).toLocaleString('fr-FR');

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="time"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={tickFmt}
            stroke="#64748b"
            style={{ fontSize: 11 }}
            minTickGap={40}
          />
          <YAxis
            yAxisId="left"
            stroke="#0ea5e9"
            style={{ fontSize: 11 }}
            domain={[6, 9]}
            label={{ value: 'pH', angle: -90, position: 'insideLeft', fill: '#0ea5e9', fontSize: 11 }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#10b981"
            style={{ fontSize: 11 }}
            domain={[0, 25]}
            label={{ value: 'T°°C', angle: 90, position: 'insideRight', fill: '#10b981', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: 6,
              fontSize: 12,
            }}
            labelFormatter={tooltipFmt}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
            iconType="circle"
            iconSize={8}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="ph"
            stroke="#0ea5e9"
            strokeWidth={2}
            dot={false}
            name="pH"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="temp"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            name="Temp (°C)"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="o2"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            name="O₂ (mg/L)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
