import React from 'react';

// Componente para verificar responsividade em diferentes dispositivos
const ResponsiveChecker = () => {
  return (
    <div className="fixed bottom-4 right-4 bg-white p-2 rounded-lg shadow-lg text-xs z-50 hidden md:block">
      <div className="sm:hidden">xs (mobile)</div>
      <div className="hidden sm:block md:hidden">sm (tablet)</div>
      <div className="hidden md:block lg:hidden">md (laptop)</div>
      <div className="hidden lg:block xl:hidden">lg (desktop)</div>
      <div className="hidden xl:block">xl (large desktop)</div>
    </div>
  );
};

// Componente para otimização de responsividade
const ResponsiveOptimizer = () => {
  // Função para detectar tipo de dispositivo
  const isMobileDevice = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  };

  // Aplicar otimizações específicas para dispositivos móveis
  React.useEffect(() => {
    const applyMobileOptimizations = () => {
      if (isMobileDevice()) {
        // Aumentar área de toque para elementos interativos
        document.querySelectorAll('button, a, input, select').forEach(el => {
          if (window.getComputedStyle(el).getPropertyValue('display') !== 'none') {
            el.classList.add('touch-target-optimize');
          }
        });
        
        // Adicionar classe ao body para otimizações CSS específicas
        document.body.classList.add('mobile-device');
      }
    };
    
    applyMobileOptimizations();
    
    // Reaplica otimizações quando o DOM muda
    const observer = new MutationObserver(applyMobileOptimizations);
    observer.observe(document.body, { childList: true, subtree: true });
    
    return () => observer.disconnect();
  }, []);

  return null; // Componente não renderiza nada visualmente
};

export { ResponsiveChecker, ResponsiveOptimizer };
