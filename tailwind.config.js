module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './apps/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          light: '#3b82f6',
          DEFAULT: '#2563eb',
          dark: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
