import * as React from 'react';
import { Sensor, Stats } from '../api';

interface Props {
  stats: Stats | null;
  sensors: Sensor[];
}

function useFlashKey(value: string | number) {
  const [flash, setFlash] = React.useState(false);
  const prev = React.useRef(value);

  React.useEffect(() => {
    if (prev.current !== value) {
      prev.current = value;
      setFlash(true);
      const t = setTimeout(() => setFlash(false), 800);
      return () => clearTimeout(t);
    }
  }, [value]);

  return flash;
}

export default function StatsBar({ stats, sensors }: Props) {
  const total = stats?.sensors_total ?? sensors.length;
  const open = stats?.alerts_open ?? 0;
  const last24 = stats?.alerts_last_24h ?? 0;
  const last7 = stats?.alerts_last_7d ?? 0;

  const flashTotal = useFlashKey(total);
  const flashOpen = useFlashKey(open);
  const flash24 = useFlashKey(last24);
  const flash7 = useFlashKey(last7);

  const items = [
    {
      label: 'Capteurs suivis',
      value: total,
      accent: 'text-ocean-300',
      glow: 'shadow-glow-cyan',
      icon: '🌊',
      flash: flashTotal,
      flashClass: 'animate-flash-cyan',
    },
    {
      label: 'Alertes ouvertes',
      value: open,
      accent: 'text-rose-300',
      glow: 'shadow-glow-rose',
      icon: '🚨',
      flash: flashOpen,
      flashClass: 'animate-flash-rose',
    },
    {
      label: 'Alertes 24h',
      value: last24,
      accent: 'text-amber-300',
      glow: 'shadow-glow-amber',
      icon: '⏱️',
      flash: flash24,
      flashClass: 'animate-flash-amber',
    },
    {
      label: 'Alertes 7j',
      value: last7,
      accent: 'text-purple-300',
      glow: '',
      icon: '📅',
      flash: flash7,
      flashClass: 'animate-flash-amber',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
      {items.map((it) => (
        <div
          key={it.label}
          className={`card card-glow p-4 sm:p-5 rounded-xl overflow-hidden ${it.flash ? it.flashClass : ''}`}
        >
          <div className="relative">
            <div className="flex items-start justify-between mb-3">
              <span className="stat-label">{it.label}</span>
              <span className="text-2xl filter drop-shadow">{it.icon}</span>
            </div>
            <div className={`stat-value ${it.accent}`}>{it.value}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
