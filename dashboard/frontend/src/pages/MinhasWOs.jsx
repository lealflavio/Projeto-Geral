import React, { useState, useEffect } from 'react';
import { FileText, Filter, Calendar, Search, RefreshCw, List, Grid, ChevronRight, X, ChevronDown, Download, Clock, MapPin, User, Package, ArrowUpDown, Eye, CheckCircle, AlertCircle, Calendar as CalendarIcon } from 'lucide-react';
import '../styles/variables.css';

// Dados simulados para demonstração
const mockProcessedPDFs = [
  { 
    id: '12345',
    data: '22/05/2025', 
    wo: '12345', 
    tipoInstalacao: 'Fibra Óptica',
    tecnico: 'João Silva', 
    status: 'concluído', 
    observacoes: 'Instalação concluída com sucesso',
    materiais: ['Cabo fibra 50m', 'Conector SC/APC', 'Splitter 1:8'],
    endereco: 'Rua das Flores, 123 - Lisboa',
    coordenadas: '38.7223, -9.1393'
  },
  { 
    id: '12344',
    data: '21/05/2025', 
    wo: '12344', 
    tipoInstalacao: 'Manutenção ONT',
    tecnico: 'Maria Santos', 
    status: 'concluído', 
    observacoes: 'Cliente não estava presente, reagendado',
    materiais: ['Cabo fibra 30m', 'Conector SC/APC'],
    endereco: 'Avenida da Liberdade, 45 - Lisboa',
    coordenadas: '38.7196, -9.1424'
  },
  { 
    id: '12343',
    data: '20/05/2025', 
    wo: '12343', 
    tipoInstalacao: 'Reparo',
    tecnico: 'Carlos Oliveira', 
    status: 'erro', 
    observacoes: 'Endereço incorreto no sistema',
    materiais: [],
    endereco: 'Rua Augusta, 290 - Lisboa',
    coordenadas: '38.7077, -9.1366'
  },
  { 
    id: '12342',
    data: '19/05/2025', 
    wo: '12342', 
    tipoInstalacao: 'Substituição',
    tecnico: 'Ana Pereira', 
    status: 'concluído', 
    observacoes: 'Substituição de ONT realizada',
    materiais: ['ONT Huawei', 'Cabo patch 2m'],
    endereco: 'Praça do Comércio, 15 - Lisboa',
    coordenadas: '38.7075, -9.1364'
  },
  { 
    id: '12341',
    data: '18/05/2025', 
    wo: '12341', 
    tipoInstalacao: 'Fibra Óptica',
    tecnico: 'João Silva', 
    status: 'concluído', 
    observacoes: 'Instalação em prédio novo',
    materiais: ['Cabo fibra 100m', 'Conector SC/APC', 'Splitter 1:4', 'ONT Huawei'],
    endereco: 'Rua do Carmo, 71 - Lisboa',
    coordenadas: '38.7118, -9.1400'
  },
  { 
    id: '12340',
    data: '17/05/2025', 
    wo: '12340', 
    tipoInstalacao: 'Reparo',
    tecnico: 'Maria Santos', 
    status: 'pendente', 
    observacoes: 'Aguardando peças para reparo',
    materiais: [],
    endereco: 'Rua da Prata, 220 - Lisboa',
    coordenadas: '38.7103, -9.1372'
  },
  { 
    id: '12339',
    data: '16/05/2025', 
    wo: '12339', 
    tipoInstalacao: 'Fibra Óptica',
    tecnico: 'Carlos Oliveira', 
    status: 'concluído', 
    observacoes: 'Instalação realizada com sucesso',
    materiais: ['Cabo fibra 75m', 'Conector SC/APC', 'ONT Huawei'],
    endereco: 'Avenida Almirante Reis, 45 - Lisboa',
    coordenadas: '38.7235, -9.1352'
  },
  { 
    id: '12338',
    data: '15/05/2025', 
    wo: '12338', 
    tipoInstalacao: 'Manutenção',
    tecnico: 'Ana Pereira', 
    status: 'erro', 
    observacoes: 'Cliente recusou atendimento',
    materiais: [],
    endereco: 'Rua do Ouro, 128 - Lisboa',
    coordenadas: '38.7108, -9.1387'
  },
];

// Função para obter o primeiro e último dia do mês atual
const obterPeriodoMesAtual = () => {
  const hoje = new Date();
  const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
  const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
  
  return {
    inicio: primeiroDia.toISOString().split('T')[0],
    fim: ultimoDia.toISOString().split('T')[0]
  };
};

// Função para formatar data para exibição
const formatarData = (dataString) => {
  const partes = dataString.split('/');
  return `${partes[0]}/${partes[1]}/${partes[2]}`;
};

// Função para converter data do formato DD/MM/YYYY para YYYY-MM-DD
const converterDataParaISO = (dataString) => {
  const partes = dataString.split('/');
  return `${partes[2]}-${partes[1]}-${partes[0]}`;
};

// Função para converter data do formato YYYY-MM-DD para DD/MM/YYYY
const converterDataParaBR = (dataISO) => {
  const partes = dataISO.split('-');
  return `${partes[2]}/${partes[1]}/${partes[0]}`;
};

// Componente principal
const MinhasWOs = () => {
  const periodoMesAtual = obterPeriodoMesAtual();
  const [startDate, setStartDate] = useState(periodoMesAtual.inicio);
  const [endDate, setEndDate] = useState(periodoMesAtual.fim);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('todas');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedWO, setSelectedWO] = useState(null);
  const [filteredWOs, setFilteredWOs] = useState([]);
  const [sortBy, setSortBy] = useState('data');
  const [sortOrder, setSortOrder] = useState('desc');

  // Efeito para filtrar WOs com base nos critérios
  useEffect(() => {
    // Filtrar por data
    const startDateObj = new Date(startDate);
    const endDateObj = new Date(endDate);
    
    let filtered = mockProcessedPDFs.filter(wo => {
      const woDate = new Date(converterDataParaISO(wo.data));
      return woDate >= startDateObj && woDate <= endDateObj;
    });
    
    // Filtrar por status
    if (activeTab !== 'todas') {
      filtered = filtered.filter(wo => {
        if (activeTab === 'concluidas') return wo.status === 'concluído';
        if (activeTab === 'pendentes') return wo.status === 'pendente';
        if (activeTab === 'erros') return wo.status === 'erro';
        return true;
      });
    }
    
    // Filtrar por termo de busca
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(wo => 
        wo.wo.toLowerCase().includes(term) || 
        wo.tipoInstalacao.toLowerCase().includes(term) ||
        wo.endereco.toLowerCase().includes(term)
      );
    }
    
    // Ordenar resultados
    filtered.sort((a, b) => {
      if (sortBy === 'data') {
        // Converter datas para comparação (formato DD/MM/YYYY)
        const dateA = a.data.split('/').reverse().join('');
        const dateB = b.data.split('/').reverse().join('');
        return sortOrder === 'asc' ? dateA.localeCompare(dateB) : dateB.localeCompare(dateA);
      } else if (sortBy === 'wo') {
        return sortOrder === 'asc' ? a.wo.localeCompare(b.wo) : b.wo.localeCompare(a.wo);
      }
      return 0;
    });
    
    setFilteredWOs(filtered);
  }, [startDate, endDate, activeTab, searchTerm, sortBy, sortOrder]);

  // Alternar ordem de classificação
  const toggleSortOrder = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  // Simular carregamento ao mudar de tab
  const handleTabChange = (tab) => {
    setIsLoading(true);
    setActiveTab(tab);
    
    // Simular tempo de carregamento
    setTimeout(() => {
      setIsLoading(false);
    }, 600);
  };

  // Simular atualização de dados
  const handleRefresh = () => {
    setIsLoading(true);
    
    // Simular tempo de carregamento
    setTimeout(() => {
      setIsLoading(false);
    }, 800);
  };

  // Exportar histórico
  const exportHistory = (format) => {
    alert(`Exportando histórico em formato ${format}...`);
    // Implementação real conectaria com backend para gerar e baixar o arquivo
  };

  return (
    <div className="p-4 max-w-full">
      {/* Cabeçalho com título e ações */}
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="bg-purple-100 p-2 rounded-lg">
            <FileText size={20} className="text-primary" />
          </div>
          <h1 className="text-lg font-semibold text-text">Minhas WOs</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={handleRefresh}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            title="Atualizar"
            aria-label="Atualizar lista"
          >
            <RefreshCw size={18} className={`text-muted ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg border ${showFilters ? 'bg-purple-100 border-purple-200 text-primary' : 'border-gray-200 text-muted hover:bg-gray-50'}`}
            title="Filtros"
            aria-label="Mostrar filtros"
          >
            <Filter size={18} />
          </button>
        </div>
      </div>
      
      {/* Filtros expandidos */}
      {showFilters && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200 animate-fadeIn">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-text">Filtros</h2>
            <button 
              onClick={() => setShowFilters(false)}
              className="text-muted hover:text-text"
              aria-label="Fechar filtros"
            >
              <X size={16} />
            </button>
          </div>
          
          <div className="space-y-3">
            {/* Filtro de período */}
            <div>
              <label className="block text-xs font-medium text-muted mb-1">Período</label>
              <div className="grid grid-cols-2 gap-2">
                <div className="relative">
                  <input
                    type="date"
                    className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                  <CalendarIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted" />
                </div>
                <div className="relative">
                  <input
                    type="date"
                    className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                  <CalendarIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted" />
                </div>
              </div>
            </div>
            
            {/* Filtro de busca */}
            <div>
              <label className="block text-xs font-medium text-muted mb-1">Busca</label>
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Buscar por WO, tipo ou endereço..." 
                  className="w-full bg-white border border-gray-300 rounded-lg py-2 pl-9 pr-3 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted" />
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Tabs de navegação */}
      <div className="mb-4 border-b border-gray-200">
        <div className="flex overflow-x-auto hide-scrollbar">
          <button 
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap ${
              activeTab === 'todas' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('todas')}
          >
            Todas
          </button>
          
          <button 
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap ${
              activeTab === 'concluidas' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('concluidas')}
          >
            Concluídas
          </button>
          
          <button 
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap ${
              activeTab === 'pendentes' 
                ? 'text-primary border-b-2 border-primary' 
                : 'text-muted hover:text-text'
            }`}
            onClick={() => handleTabChange('pendentes')}
          >
            Pendentes
          </button>
          
          <button 
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap ${
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
          {/* Lista de WOs - Mobile First */}
          <div className="space-y-3 mb-4">
            {filteredWOs.length > 0 ? (
              filteredWOs.map((wo) => (
                <div 
                  key={wo.id} 
                  className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm"
                >
                  <div className={`px-4 py-3 flex items-center justify-between ${
                    wo.status === 'concluído' 
                      ? 'bg-emerald-50 border-b border-emerald-100' 
                      : wo.status === 'erro'
                        ? 'bg-red-50 border-b border-red-100'
                        : 'bg-yellow-50 border-b border-yellow-100'
                  }`}>
                    <div className="flex items-center gap-2">
                      {wo.status === 'concluído' ? (
                        <CheckCircle size={16} className="text-emerald-600" />
                      ) : wo.status === 'erro' ? (
                        <AlertCircle size={16} className="text-red-600" />
                      ) : (
                        <Clock size={16} className="text-yellow-600" />
                      )}
                      <span className="font-medium text-text">WO #{wo.wo}</span>
                    </div>
                    <button
                      className="text-primary hover:text-primary-dark p-1.5 rounded-full hover:bg-white/50 transition-colors"
                      onClick={() => setSelectedWO(wo)}
                      aria-label="Ver detalhes"
                    >
                      <Eye size={18} />
                    </button>
                  </div>
                  
                  <div className="p-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <p className="text-xs text-muted">Data</p>
                        <p className="text-sm font-medium text-text">{formatarData(wo.data)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted">Tipo</p>
                        <p className="text-sm font-medium text-text">{wo.tipoInstalacao}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-muted bg-white rounded-lg border border-gray-200">
                Nenhuma work order encontrada com os filtros atuais
              </div>
            )}
          </div>
          
          {/* Rodapé com contagem e exportação */}
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="text-sm text-muted">
              {filteredWOs.length} {filteredWOs.length === 1 ? 'WO encontrada' : 'WOs encontradas'}
            </div>
            <div className="flex items-center gap-2">
              <button 
                className="px-3 py-1.5 text-sm text-primary hover:text-primary-dark font-medium flex items-center gap-1 hover:bg-white rounded-lg transition-colors"
                onClick={() => exportHistory('csv')}
              >
                <Download size={16} />
                <span>Exportar</span>
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Modal de detalhes da WO */}
      {selectedWO && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col">
            <div className={`p-4 ${
              selectedWO.status === 'concluído' 
                ? 'bg-emerald-50 border-b border-emerald-100' 
                : selectedWO.status === 'erro'
                  ? 'bg-red-50 border-b border-red-100'
                  : 'bg-yellow-50 border-b border-yellow-100'
            }`}>
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-text">WO #{selectedWO.wo}</h3>
                <button 
                  onClick={() => setSelectedWO(null)}
                  className="text-muted hover:text-text p-1 rounded-full hover:bg-black/5 transition-colors"
                  aria-label="Fechar modal"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            
            <div className="p-4 overflow-y-auto">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Clock size={18} className="text-muted mt-0.5" />
                  <div>
                    <p className="text-xs text-muted">Data</p>
                    <p className="text-sm font-medium text-text">{selectedWO.data}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <Package size={18} className="text-muted mt-0.5" />
                  <div>
                    <p className="text-xs text-muted">Tipo de Instalação</p>
                    <p className="text-sm font-medium text-text">{selectedWO.tipoInstalacao}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <User size={18} className="text-muted mt-0.5" />
                  <div>
                    <p className="text-xs text-muted">Técnico</p>
                    <p className="text-sm font-medium text-text">{selectedWO.tecnico}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <MapPin size={18} className="text-muted mt-0.5" />
                  <div>
                    <p className="text-xs text-muted">Endereço</p>
                    <p className="text-sm font-medium text-text">{selectedWO.endereco}</p>
                    <p className="text-xs text-muted mt-1">{selectedWO.coordenadas}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <FileText size={18} className="text-muted mt-0.5" />
                  <div>
                    <p className="text-xs text-muted">Observações</p>
                    <p className="text-sm text-text">{selectedWO.observacoes}</p>
                  </div>
                </div>
                
                {selectedWO.materiais.length > 0 && (
                  <div className="border-t border-gray-100 pt-4 mt-4">
                    <p className="text-xs font-medium text-muted mb-2">Materiais Utilizados</p>
                    <ul className="space-y-1">
                      {selectedWO.materiais.map((material, index) => (
                        <li key={index} className="text-sm text-text flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary"></div>
                          {material}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setSelectedWO(null)}
                className="w-full py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Estilos adicionais para esconder a barra de rolagem e animações */}
      <style jsx>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default MinhasWOs;
