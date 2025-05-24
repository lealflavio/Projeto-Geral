import React, { useEffect } from 'react';
import { ResponsiveOptimizer, ResponsiveChecker } from '../components/ResponsiveUtils';

// Componente de layout responsivo aprimorado
const Layout = ({ children }) => {
  // Detectar orientação do dispositivo e ajustar layout
  useEffect(() => {
    const handleOrientationChange = () => {
      const isLandscape = window.innerWidth > window.innerHeight;
      document.body.classList.toggle('landscape', isLandscape);
      document.body.classList.toggle('portrait', !isLandscape);
    };

    // Verificar orientação inicial
    handleOrientationChange();
    
    // Adicionar listener para mudanças de orientação
    window.addEventListener('resize', handleOrientationChange);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', handleOrientationChange);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Incluir otimizador de responsividade */}
      <ResponsiveOptimizer />
      
      {/* Incluir verificador de responsividade (visível apenas em desenvolvimento) */}
      {process.env.NODE_ENV === 'development' && <ResponsiveChecker />}
      
      {/* Conteúdo principal com classes responsivas */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {children}
      </main>
    </div>
  );
};

export default Layout;
