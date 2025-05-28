import React, { useState } from 'react';
import { FileText, Filter, Calendar, Search, RefreshCw, List, Grid } from 'lucide-react';
import ProcessedServicesHistory from '../components/ProcessedServicesHistory';
import '../styles/variables.css';

const MinhasWOs = () => {
  const [viewMode, setViewMode] = useState('list');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('todas');

  // Simular carregamento ao mudar de tab
  const handleTabChange = (tab) => {
    setIsLoading(true);
    setActiveTab(tab);
    
    // Simular tempo de carregamento
    setTimeout(() => {
      setIsLoading(false);
    }, 800);
  };

  // Simular atualização de dados
  const handleRefresh = () => {
    setIsLoading(true);
    
    // Simular tempo de carregamento
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="p-4 md:p-6 max-w-full">
      {/* Cabeçalho com título e ações */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="bg-purple-100 p-2 rounded-lg">
            <FileText size={24} className="text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-text">Minhas Work Orders</h1>
            <p className="text-sm text-muted hidden sm:block">Gerencie e acompanhe suas ordens de serviço</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={handleRefresh}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            title="Atualizar"
          >
            <RefreshCw size={18} className={`text-muted ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <div className="border-l border-gray-200 h-6 mx-1"></div>
          
          <button 
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-purple-100 text-primary' : 'text-muted hover:bg-gray-50'}`}
            title="Visualização em lista"
          >
            <List size={18} />
          </button>
          
          <button 
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-purple-100 text-primary' : 'text-muted hover:bg-gray-50'}`}
            title="Visualização em grade"
          >
            <Grid size={18} />
          </button>
        </div>
      </div>
      
      {/* Tabs de navegação */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex overflow-x-auto hide-scrollbar">
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${
              activeTab === 'todas' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('todas')}
          >
            Todas as WOs
          </button>
          
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${
              activeTab === 'concluidas' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('concluidas')}
          >
            Concluídas
          </button>
          
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${
              activeTab === 'pendentes' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('pendentes')}
          >
            Pendentes
          </button>
          
          <button 
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap ${
              activeTab === 'erros' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('erros')}
          >
            Com Erro
          </button>
        </div>
      </div>
      
      {/* Estado de carregamento */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-primary rounded-full animate-spin mb-4"></div>
          <p className="text-muted">Carregando work orders...</p>
        </div>
      ) : (
        <>
          {/* Componente de histórico de serviços processados */}
          <ProcessedServicesHistory viewMode={viewMode} filterStatus={activeTab} />
          
          {/* Informações adicionais e dicas - visível apenas em desktop */}
          <div className="mt-8 bg-blue-50 rounded-lg p-4 border border-blue-100 hidden md:block">
            <h3 className="text-sm font-medium text-blue-800 mb-2">Dicas para gerenciamento de WOs</h3>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Mantenha suas WOs organizadas utilizando os filtros disponíveis</li>
              <li>• Exporte relatórios regularmente para acompanhamento</li>
              <li>• Verifique WOs com erro para resolução rápida de problemas</li>
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

export default MinhasWOs;
