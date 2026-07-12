/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          0: 'var(--color-surface-0)',
          1: 'var(--color-surface-1)',
          2: 'var(--color-surface-2)',
        },
        line: 'var(--color-line)',
        ink: {
          DEFAULT: 'var(--color-ink)',
          mute: 'var(--color-ink-mute)',
        },
        signal: 'var(--color-signal)',
        ok: 'var(--color-ok)',
        info: 'var(--color-info)',
        warn: 'var(--color-warn)',
        danger: 'var(--color-danger)',
        neutral: 'var(--color-neutral)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Barlow Semi Condensed', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '8px',
      },
    },
  },
  plugins: [],
};
