import { Alert } from '../../api';

interface Props {
  alerts: Alert[];
  loading?: boolean;
}

export default function SensorAlerts({ alerts, loading }: Props) {
  if (loading) {
    return <div className="h-20 skeleton" />;
  }
  if (alerts.length === 0) {
    return (
      <p className="text-sm text-slate-500 italic py-4 text-center">
        ✅ Aucune alerte pour ce capteur
      </p>
    );
  }
  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {alerts.map((a) => {
        const openedAt = new Date(a.opened_at);
        const isCritical = a.severity === 'CRITICAL';
        const accent = isCritical ? '#ef4444' : '#f59e0b';
        return (
          <div
            key={a.id}
            className="p-2.5 rounded border-l-2 bg-slate-800/30"
            style={{ borderColor: accent }}
          >
            <div className="flex items-center gap-2 mb-0.5">
              <span
                className="text-[10px] font-bold uppercase"
                style={{ color: isCritical ? '#fca5a5' : '#fcd34d' }}
              >
                {a.severity}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                {openedAt.toLocaleString('fr-FR')}
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-snug">{a.message}</p>
          </div>
        );
      })}
    </div>
  );
}
