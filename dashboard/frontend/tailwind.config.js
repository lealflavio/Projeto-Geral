// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Cores principais
        primary: {
          DEFAULT: "#6C63FF",     // botão principal, destaque
          light: "#8A83FF",       // versão mais clara para hover
          dark: "#5A52E0",        // versão mais escura para active/pressed
          50: "#F5F4FF",          // variação muito clara
          100: "#ECEBFF",         // variação clara
          200: "#D8D6FF",         // variação média-clara
          300: "#B7B3FF",         // variação média
          400: "#9690FF",         // variação média-escura
          500: "#6C63FF",         // cor base
          600: "#5A52E0",         // variação escura
          700: "#4A43C2",         // variação mais escura
          800: "#3A34A3",         // variação muito escura
          900: "#2A2585",         // variação extremamente escura
        },
        secondary: {
          DEFAULT: "#ECEBFF",     // plano de fundo leve
          dark: "#D8D6FF",        // versão mais escura
          light: "#F5F4FF",       // versão mais clara
        },
        background: {
          DEFAULT: "#FAFAFA",     // fundo geral
          alt: "#F0F0F0",         // fundo alternativo
          dark: "#E8E8E8",        // fundo escuro
        },
        text: {
          DEFAULT: "#2E2E2E",     // texto principal
          light: "#4A4A4A",       // texto secundário claro
          dark: "#1A1A1A",        // texto enfatizado
        },
        muted: {
          DEFAULT: "#888888",     // texto secundário
          light: "#AAAAAA",       // texto terciário
          dark: "#666666",        // texto muted enfatizado
        },
        card: {
          DEFAULT: "#FFFFFF",     // fundo dos cards
          hover: "#F9F9F9",       // hover dos cards
          border: "#EEEEEE",      // borda dos cards
        },
        danger: {
          DEFAULT: "#FF6F61",     // sair ou erros
          light: "#FF8C82",       // versão mais clara
          dark: "#E55A4D",        // versão mais escura
        },
        success: {
          DEFAULT: "#4CAF50",     // sucesso
          light: "#66BB6A",       // versão mais clara
          dark: "#388E3C",        // versão mais escura
        },
        warning: {
          DEFAULT: "#FFC107",     // alerta
          light: "#FFCA28",       // versão mais clara
          dark: "#FFA000",        // versão mais escura
        },
        info: {
          DEFAULT: "#2196F3",     // informação
          light: "#42A5F5",       // versão mais clara
          dark: "#1976D2",        // versão mais escura
        },
      },
      borderRadius: {
        'sm': '0.125rem',
        DEFAULT: '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        'card': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.12)',
        'none': 'none',
      },
      spacing: {
        'xs': '0.25rem',    // 4px
        'sm': '0.5rem',     // 8px
        'md': '1rem',       // 16px
        'lg': '1.5rem',     // 24px
        'xl': '2rem',       // 32px
        '2xl': '3rem',      // 48px
        '3xl': '4rem',      // 64px
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      fontFamily: {
        'sans': ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        'serif': ['ui-serif', 'Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
        'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
        'width': 'width',
        'position': 'top, right, bottom, left',
      },
      transitionDuration: {
        'DEFAULT': '150ms',
        'fast': '100ms',
        'normal': '200ms',
        'slow': '300ms',
        'slower': '500ms',
      },
      transitionTimingFunction: {
        'DEFAULT': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'linear': 'linear',
        'in': 'cubic-bezier(0.4, 0, 1, 1)',
        'out': 'cubic-bezier(0, 0, 0.2, 1)',
        'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      animation: {
        'spin': 'spin 1s linear infinite',
        'ping': 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce': 'bounce 1s infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'fade-out': 'fadeOut 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-in-out',
        'slide-out': 'slideOut 0.3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideOut: {
          '0%': { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-10px)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};
