import { MeasurementPoint } from '../../api';

interface Props {
  points: MeasurementPoint[];
  loading?: boolean;
}

export default function MeasurementTable({ points, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-1.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-7 skeleton" />
        ))}
      </div>
    );
  }
  if (points.length === 0) {
    return (
      <p className="text-sm text-slate-500 italic py-4 text-center">
        Aucune mesure
      </p>
    );
  }
  // Show latest 20
  const latest = points.slice(-20).reverse();
  return (
    <div className="overflow-x-auto max-h-72 overflow-y-auto">
      <table className="w-full text-xs">
        <thead className="bg-slate-800/50 text-[10px] uppercase tracking-wider text-slate-400 sticky top-0">
          <tr>
            <th className="text-left px-3 py-2">Heure</th>
            <th className="text-right px-3 py-2">pH</th>
            <th className="text-right px-3 py-2">T°</th>
            <th className="text-right px-3 py-2">Turb.</th>
            <th className="text-right px-3 py-2">O₂</th>
            <th className="text-right px-3 py-2">Niveau</th>
            <th className="text-right px-3 py-2">Débit</th>
          </tr>
        </thead>
        <tbody>
          {latest.map((p, i) => {
            const t = new Date(p.timestamp);
            return (
              <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                <td className="px-3 py-1.5 font-mono text-slate-300">
                  {t.toLocaleTimeString('fr-FR')}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-ocean-300">
                  {p.ph.toFixed(2)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-emerald-300">
                  {p.temperature_c.toFixed(1)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-slate-300">
                  {p.turbidity_ntu.toFixed(1)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-amber-300">
                  {p.dissolved_oxygen_mgl.toFixed(2)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-purple-300">
                  {p.level_m !== undefined && p.level_m !== null ? `${p.level_m.toFixed(2)} m` : '—'}
                </td>
                <td className="px-3 py-1.5 text-right font-mono tabular-nums text-pink-300">
                  {p.flow_m3s !== undefined && p.flow_m3s !== null ? `${p.flow_m3s.toFixed(1)} m³/s` : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
