import React, { useState } from 'react';
import { MapPin, Calendar, Home, Navigation, Download, BarChart2, FileText, RefreshCw } from 'lucide-react';
import KilometersCalculator from '../components/KilometersCalculator';

const MapaKMs = () => {
  const [activeTab, setActiveTab] = useState('calculadora');
  const [isLoading, setIsLoading] = useState(false);

  // Simular carregamento ao mudar de tab
  const handleTabChange = (tab) => {
    setIsLoading(true);
    setActiveTab(tab);
    
    // Simular tempo de carregamento
    setTimeout(() => {
      setIsLoading(false);
    }, 800);
  };

  return (
    <div className="p-4 md:p-6 max-w-full">
      {/* Cabeçalho com título e ações */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-blue-100 p-2 rounded-lg">
            <Navigation size={24} className="text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[#333]">Mapa de KMs</h1>
            <p className="text-sm text-gray-500 hidden sm:block">Calcule e visualize a quilometragem entre suas WOs</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={() => alert('Exportando planilha de KMs...')}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            title="Exportar planilha"
          >
            <Download size={16} />
            <span className="hidden sm:inline">Exportar</span>
          </button>
        </div>
      </div>
      
      {/* Tabs de navegação */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex overflow-x-auto hide-scrollbar">
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap flex items-center gap-2 ${
              activeTab === 'calculadora' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => handleTabChange('calculadora')}
          >
            <BarChart2 size={16} />
            Calculadora de KMs
          </button>
          
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap flex items-center gap-2 ${
              activeTab === 'mapa' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => handleTabChange('mapa')}
          >
            <MapPin size={16} />
            Visualização no Mapa
          </button>
          
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap flex items-center gap-2 ${
              activeTab === 'historico' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => handleTabChange('historico')}
          >
            <FileText size={16} />
            Histórico de Rotas
          </button>
        </div>
      </div>
      
      {/* Estado de carregamento */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
          <p className="text-gray-500">Carregando...</p>
        </div>
      ) : (
        <>
          {/* Conteúdo da tab ativa */}
          <div className="bg-white rounded-xl shadow overflow-hidden">
            {activeTab === 'calculadora' && (
              <div className="p-4">
                <KilometersCalculator />
              </div>
            )}
            
            {activeTab === 'mapa' && (
              <div className="p-4">
                <div className="bg-gray-100 rounded-lg p-4 mb-4 flex items-center gap-3">
                  <RefreshCw size={18} className="text-blue-600" />
                  <p className="text-sm text-gray-600">Selecione as WOs na calculadora para visualizar a rota no mapa</p>
                </div>
                
                <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="text-center p-6">
                    <MapPin size={48} className="text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-500 mb-2">Mapa de Rotas</h3>
                    <p className="text-sm text-gray-500">Calcule uma rota primeiro para visualizar no mapa</p>
                  </div>
                </div>
              </div>
            )}
            
            {activeTab === 'historico' && (
              <div className="p-4">
                <div className="bg-gray-100 rounded-lg p-4 mb-4 flex items-center gap-3">
                  <Calendar size={18} className="text-blue-600" />
                  <p className="text-sm text-gray-600">Histórico das últimas rotas calculadas</p>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full min-w-full">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">Data</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">Período</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">Total KMs</th>
                        <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">WOs</th>
                        <th className="py-3 px-4 text-right text-xs font-medium text-[#555] uppercase tracking-wider">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      <tr className="hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">27/05/2025</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">20/05 - 27/05</td>
                        <td className="py-3 px-4 text-sm font-medium text-[#333] whitespace-nowrap">127.5 km</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">8 WOs</td>
                        <td className="py-3 px-4 text-sm text-right">
                          <button className="text-blue-600 hover:text-blue-800 font-medium">Ver detalhes</button>
                        </td>
                      </tr>
                      <tr className="hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">20/05/2025</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">13/05 - 20/05</td>
                        <td className="py-3 px-4 text-sm font-medium text-[#333] whitespace-nowrap">98.2 km</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">6 WOs</td>
                        <td className="py-3 px-4 text-sm text-right">
                          <button className="text-blue-600 hover:text-blue-800 font-medium">Ver detalhes</button>
                        </td>
                      </tr>
                      <tr className="hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">13/05/2025</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">06/05 - 13/05</td>
                        <td className="py-3 px-4 text-sm font-medium text-[#333] whitespace-nowrap">145.7 km</td>
                        <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">10 WOs</td>
                        <td className="py-3 px-4 text-sm text-right">
                          <button className="text-blue-600 hover:text-blue-800 font-medium">Ver detalhes</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
          
          {/* Informações adicionais e dicas - visível apenas em desktop */}
          <div className="mt-8 bg-blue-50 rounded-lg p-4 border border-blue-100 hidden md:block">
            <h3 className="text-sm font-medium text-blue-800 mb-2">Dicas para cálculo de KMs</h3>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Adicione seu endereço residencial para calcular o trajeto completo (casa-trabalho-casa)</li>
              <li>• Exporte a planilha para facilitar o controle de quilometragem</li>
              <li>• Visualize as rotas no mapa para confirmar o trajeto calculado</li>
            </ul>
          </div>
        </>
      )}
      
      {/* Estilos adicionais para esconder a barra de rolagem */}
      <style jsx>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

export default MapaKMs;
