import { Stats } from '../api';

interface Props {
  connected: boolean;
  stats: Stats | null;
  sensorCount: number;
}

export default function Header({ connected, stats, sensorCount }: Props) {
  const today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/60 bg-deep-900/75 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative w-11 h-11 rounded-xl flex items-center justify-center text-white font-extrabold text-lg shadow-glow-cyan overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-ocean-400 to-ocean-700" />
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+')]" />
            <span className="relative">UH</span>
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-white tracking-tight font-display">
              UrbanHub
            </h1>
            <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">
              Qualité de l'eau · Paris · {today}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-5 text-xs">
          <div className="hidden md:flex items-center gap-2 text-slate-400">
            <span className="text-ocean-300">🌊</span>
            <span className="font-mono text-slate-300">{sensorCount} capteurs</span>
          </div>
          <div className="hidden md:flex items-center gap-2 text-slate-400">
            <span className="text-rose-300">🚨</span>
            <span className="font-mono text-slate-300">{stats?.alerts_open ?? 0} alertes</span>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold transition-colors ${
              connected
                ? 'border-emerald-500/30 bg-emerald-950/30 text-emerald-300'
                : 'border-rose-500/30 bg-rose-950/30 text-rose-300'
            }`}
          >
            {connected ? (
              <span className="pulse-dot" />
            ) : (
              <span className="pulse-dot-rose" />
            )}
            <span>{connected ? 'Temps réel' : 'Déconnecté'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
