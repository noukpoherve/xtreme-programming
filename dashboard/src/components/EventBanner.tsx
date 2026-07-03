import * as React from 'react';

interface Props {
  lastEvent: string | null;
  onDismiss: () => void;
}

export default function EventBanner({ lastEvent, onDismiss }: Props) {
  if (!lastEvent) return null;

  return (
    <div className="animate-slide-down border-b border-ocean-500/20 bg-gradient-to-r from-ocean-950/90 via-deep-800/90 to-ocean-950/90">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-2.5 flex items-center gap-3">
        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-ocean-500/15 border border-ocean-400/30">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping-slow absolute inline-flex h-full w-full rounded-full bg-ocean-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-ocean-400" />
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-[10px] font-bold uppercase tracking-widest text-ocean-300 mr-2">
            Transition détectée
          </span>
          <span className="font-mono text-xs sm:text-sm text-ocean-50 truncate">
            {lastEvent}
          </span>
        </div>
        <button
          onClick={onDismiss}
          className="shrink-0 text-ocean-300/80 hover:text-white hover:bg-ocean-500/10 rounded p-1 transition"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
