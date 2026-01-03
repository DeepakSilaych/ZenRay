/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      colors: {
        xray: {
          bg: '#09090b',
          surface: '#18181b',
          elevated: '#27272a',
          border: '#3f3f46',
          text: '#fafafa',
          muted: '#a1a1aa',
          dim: '#71717a',
          accent: '#3b82f6',
          accentHover: '#2563eb',
          success: '#22c55e',
          danger: '#ef4444',
          warning: '#f59e0b',
        }
      },
      fontSize: {
        '2xs': '0.65rem',
      }
    },
  },
  plugins: [],
}
