/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif']
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(59,130,246,0.2), 0 12px 30px rgba(59,130,246,0.2)',
        panel: '0 18px 50px rgba(15, 23, 42, 0.45)'
      },
      colors: {
        bg: {
          base: '#020817',
          surface: '#0f172a',
          panel: '#111827',
          soft: '#0b1220'
        },
        brand: {
          50: '#e0f2fe',
          100: '#bae6fd',
          200: '#7dd3fc',
          300: '#38bdf8',
          400: '#0ea5e9',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#172554'
        },
        accent: {
          violet: '#8b5cf6',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#ef4444'
        }
      },
      backgroundImage: {
        'hero-glow': 'radial-gradient(circle at top left, rgba(59,130,246,0.25), transparent 45%), radial-gradient(circle at bottom right, rgba(139,92,246,0.18), transparent 40%)'
      },
      animation: {
        float: 'float 18s ease-in-out infinite',
        pulseSoft: 'pulseSoft 2s ease-in-out infinite'
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' }
        },
        pulseSoft: {
          '0%, 100%': { opacity: '0.65' },
          '50%': { opacity: '1' }
        }
      }
    }
  },
  plugins: []
};
