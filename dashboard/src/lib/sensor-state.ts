/**
 * Single source of truth for sensor states and their visual theme.
 *
 * Every component that needs a color, badge style, or sort order for
 * NORMAL / WARNING / CRITICAL must import from here. No local
 * STATE_COLORS maps allowed.
 */

export type SensorState = 'NORMAL' | 'WARNING' | 'CRITICAL';

export const SENSOR_STATES: SensorState[] = ['NORMAL', 'WARNING', 'CRITICAL'];

export interface StateTheme {
  /** Hex color used for badges, markers, charts. */
  color: string;
  /** RGBA background used for badges and table highlights. */
  bg: string;
  /** RGBA border used for badges. */
  border: string;
  /** Tailwind text color class. */
  textClass: string;
  /** Sort rank: lower = calmer. */
  rank: number;
  /** Human-readable label. */
  label: string;
}

export const STATE_THEME: Record<SensorState, StateTheme> = {
  NORMAL: {
    color: '#22d3ee',
    bg: 'rgba(34, 211, 238, 0.10)',
    border: 'rgba(34, 211, 238, 0.25)',
    textClass: 'text-cyan-300',
    rank: 0,
    label: 'Normal',
  },
  WARNING: {
    color: '#fbbf24',
    bg: 'rgba(251, 191, 36, 0.10)',
    border: 'rgba(251, 191, 36, 0.25)',
    textClass: 'text-amber-300',
    rank: 1,
    label: 'Attention',
  },
  CRITICAL: {
    color: '#fb7185',
    bg: 'rgba(251, 113, 133, 0.12)',
    border: 'rgba(251, 113, 133, 0.30)',
    textClass: 'text-rose-300',
    rank: 2,
    label: 'Critique',
  },
};

export function isSensorState(value: string): value is SensorState {
  return SENSOR_STATES.includes(value as SensorState);
}

export function getStateTheme(state: string): StateTheme {
  if (isSensorState(state)) return STATE_THEME[state];
  return {
    color: '#94a3b8',
    bg: 'rgba(148, 163, 184, 0.10)',
    border: 'rgba(148, 163, 184, 0.25)',
    textClass: 'text-slate-400',
    rank: 99,
    label: state,
  };
}

/** Sort sensors from most severe to least severe. */
export function sortBySeverity<S extends { state: string }>(sensors: S[]): S[] {
  return [...sensors].sort(
    (a, b) => getStateTheme(b.state).rank - getStateTheme(a.state).rank,
  );
}

/** React inline-styles for a state badge. */
export function stateBadgeStyle(state: string): React.CSSProperties {
  const theme = getStateTheme(state);
  return {
    background: theme.bg,
    color: theme.color,
    borderColor: theme.border,
  };
}

/** React inline-style for a glowing dot. */
export function stateDotStyle(state: string): React.CSSProperties {
  const theme = getStateTheme(state);
  return {
    background: theme.color,
    color: theme.color,
    boxShadow: `0 0 8px ${theme.color}`,
  };
}

/** React inline-style for a progress bar. */
export function stateBarStyle(state: string): React.CSSProperties {
  const theme = getStateTheme(state);
  return {
    background: theme.color,
    boxShadow: `0 0 12px ${theme.color}`,
  };
}

/** Color to use in chart libraries (Recharts, Leaflet, etc.). */
export function stateColor(state: string): string {
  return getStateTheme(state).color;
}
