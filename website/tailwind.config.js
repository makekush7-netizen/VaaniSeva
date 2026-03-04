/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          50:  '#FDF3E3',
          100: '#FDE8B8',
          200: '#F7C87A',
          300: '#F0A832',
          400: '#E0931A',
          500: '#D4860B',
          600: '#B8720A',
          700: '#9A5E09',
        },
        surface: {
          primary:   '#FFFFFF',
          secondary: '#F8F9FA',
          tertiary:  '#F1F3F5',
        },
        content: {
          primary:   '#1A1A2E',
          secondary: '#6B7280',
          tertiary:  '#9CA3AF',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        hindi: ['Noto Sans Devanagari', 'sans-serif'],
        tamil: ['Noto Sans Tamil', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-ring': 'pulseRing 2s ease-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseRing: {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '100%': { transform: 'scale(1.5)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}
