/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: '#eff8ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        sensor: {
          normal: '#22d3ee',   // cyan-400
          warning: '#fbbf24',  // amber-400
          critical: '#fb7185', // rose-400
          unknown: '#94a3b8',  // slate-400
        },
        deep: {
          900: '#050c14',
          800: '#08101a',
          700: '#0c1824',
        },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'flash-cyan': 'flashCyan 0.8s ease-out',
        'flash-amber': 'flashAmber 0.8s ease-out',
        'flash-rose': 'flashRose 0.8s ease-out',
        'ping-slow': 'ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite',
        'slide-down': 'slideDown 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        flashCyan: {
          '0%': { backgroundColor: 'rgba(34, 211, 238, 0.25)' },
          '100%': { backgroundColor: 'transparent' },
        },
        flashAmber: {
          '0%': { backgroundColor: 'rgba(251, 191, 36, 0.25)' },
          '100%': { backgroundColor: 'transparent' },
        },
        flashRose: {
          '0%': { backgroundColor: 'rgba(251, 113, 133, 0.25)' },
          '100%': { backgroundColor: 'transparent' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(34, 211, 238, 0.15)',
        'glow-amber': '0 0 20px rgba(251, 191, 36, 0.15)',
        'glow-rose': '0 0 24px rgba(251, 113, 133, 0.2)',
        'panel': '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
      },
    },
  },
  plugins: [],
};
