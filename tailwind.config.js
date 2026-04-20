export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#000000',
        secondary: '#666666',
        border: '#e5e5e5',
        bg: '#f9f9f9'
      },
      spacing: {
        'safe-bottom': 'max(1rem, env(safe-area-inset-bottom))'
      }
    }
  },
  plugins: []
}