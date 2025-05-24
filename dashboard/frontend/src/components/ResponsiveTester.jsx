import React from 'react';
import { useMediaQuery } from 'react-responsive';

// Componente para testes de responsividade em diferentes dispositivos
const ResponsiveTester = () => {
  // Definição de breakpoints
  const isMobile = useMediaQuery({ maxWidth: 640 });
  const isTablet = useMediaQuery({ minWidth: 641, maxWidth: 1024 });
  const isDesktop = useMediaQuery({ minWidth: 1025 });
  
  // Exemplos de componentes com diferentes layouts para cada dispositivo
  return (
    <div className="p-4 md:p-6 bg-white rounded-xl shadow mb-6">
      <h2 className="text-lg font-semibold text-[#333] mb-4">Teste de Responsividade</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Card responsivo para mobile */}
        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-md font-medium text-[#7C3AED] mb-2">Layout Mobile</h3>
          <p className="text-sm text-[#555]">
            {isMobile ? 
              "✅ Você está visualizando em um dispositivo móvel" : 
              "Este conteúdo é otimizado para dispositivos móveis"}
          </p>
          <div className="mt-3 flex flex-col space-y-2">
            <button className="bg-[#7C3AED] text-white py-3 px-4 rounded-lg text-sm font-medium">
              Botão adaptado para toque
            </button>
            <div className="text-xs text-[#777] mt-1">
              Área de toque aumentada para melhor usabilidade
            </div>
          </div>
        </div>
        
        {/* Card responsivo para tablet */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-md font-medium text-blue-600 mb-2">Layout Tablet</h3>
          <p className="text-sm text-[#555]">
            {isTablet ? 
              "✅ Você está visualizando em um tablet" : 
              "Este conteúdo é otimizado para tablets"}
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button className="bg-blue-600 text-white py-2 px-3 rounded-lg text-sm font-medium">
              Opção 1
            </button>
            <button className="bg-blue-600 text-white py-2 px-3 rounded-lg text-sm font-medium">
              Opção 2
            </button>
          </div>
        </div>
        
        {/* Card responsivo para desktop */}
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-md font-medium text-green-600 mb-2">Layout Desktop</h3>
          <p className="text-sm text-[#555]">
            {isDesktop ? 
              "✅ Você está visualizando em um desktop" : 
              "Este conteúdo é otimizado para desktop"}
          </p>
          <div className="mt-3 flex items-center justify-between">
            <button className="bg-green-600 text-white py-2 px-3 rounded-lg text-sm font-medium">
              Ação Principal
            </button>
            <div className="flex space-x-2">
              <button className="bg-green-100 text-green-700 py-1 px-2 rounded text-xs">
                Opção A
              </button>
              <button className="bg-green-100 text-green-700 py-1 px-2 rounded text-xs">
                Opção B
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-md font-medium text-[#333] mb-2">Informações do Dispositivo</h3>
        <ul className="text-sm text-[#555] space-y-1">
          <li>
            <span className="font-medium">Tipo:</span> 
            {isMobile ? " Mobile" : isTablet ? " Tablet" : " Desktop"}
          </li>
          <li>
            <span className="font-medium">Largura da viewport:</span> 
            <span className="inline-block" id="viewport-width">
              Carregando...
            </span>
          </li>
          <li>
            <span className="font-medium">Altura da viewport:</span> 
            <span className="inline-block" id="viewport-height">
              Carregando...
            </span>
          </li>
          <li>
            <span className="font-medium">Densidade de pixels:</span> 
            <span className="inline-block" id="pixel-ratio">
              Carregando...
            </span>
          </li>
        </ul>
      </div>
      
      {/* Script para atualizar informações da viewport */}
      <script dangerouslySetInnerHTML={{
        __html: `
          function updateViewportInfo() {
            document.getElementById('viewport-width').textContent = window.innerWidth + 'px';
            document.getElementById('viewport-height').textContent = window.innerHeight + 'px';
            document.getElementById('pixel-ratio').textContent = window.devicePixelRatio;
          }
          
          // Atualizar inicialmente
          updateViewportInfo();
          
          // Atualizar quando a janela for redimensionada
          window.addEventListener('resize', updateViewportInfo);
        `
      }} />
    </div>
  );
};

export default ResponsiveTester;
