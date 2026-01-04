export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        hatchet: {
          bg: '#050510',
          surface: '#0a0a14',
          border: '#1E1E2E',
        },
        navy: {
          950: '#09090b',
          900: '#18181b',
          800: '#27272a',
          700: '#3f3f46',
        },
        accent: {
          DEFAULT: '#22d3ee',
          light: '#67e8f9',
          dark: '#06b6d4',
          glow: 'rgba(34, 211, 238, 0.5)',
        },
        success: {
          DEFAULT: '#22c55e',
          light: '#4ade80',
          dark: '#16a34a',
        },
        danger: {
          DEFAULT: '#ef4444',
          light: '#f87171',
          dark: '#dc2626',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
          dark: '#d97706',
        },
        purple: {
          DEFAULT: '#a855f7',
          light: '#c084fc',
          dark: '#9333ea',
        },
        cyan: {
          DEFAULT: '#22d3ee',
          light: '#67e8f9',
          dark: '#06b6d4',
        },
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, #1E1E2E 1px, transparent 1px), linear-gradient(to bottom, #1E1E2E 1px, transparent 1px)",
        'shiny-gradient': 'linear-gradient(to right, transparent, rgba(255, 255, 255, 0.1) 50%, transparent)',
      },
      boxShadow: {
        'glow-accent': '0 0 20px -5px rgba(34, 211, 238, 0.3)',
      },
      animation: {
        'shine': 'shine 3s infinite',
      },
      keyframes: {
        shine: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
