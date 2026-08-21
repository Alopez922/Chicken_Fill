/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cfa: {
          red: '#E51636',
          darkred: '#B80028',
          lightred: '#FEE2E2',
          navy: '#0B2341',
          gold: '#D97706',
          bg: '#F8FAFC'
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
