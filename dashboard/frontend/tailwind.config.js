// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#6C63FF",       // botão principal, destaque
        secondary: "#ECEBFF",     // plano de fundo leve
        background: "#FAFAFA",    // fundo geral
        text: "#2E2E2E",          // texto principal
        muted: "#888888",         // texto secundário
        card: "#FFFFFF",          // fundo dos cards
        danger: "#FF6F61",        // sair ou erros
      },
    },
  },
  plugins: [],
};
