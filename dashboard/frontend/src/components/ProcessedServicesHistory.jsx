import React, { useState } from 'react';
import { FileText, Search, Filter, Download, Calendar, ArrowUpDown, Clock, MapPin, User, Package } from 'lucide-react';

const mockProcessedPDFs = [
  { 
    id: '12345',
    data: '22/05/2025', 
    wo: '12345', 
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
    tecnico: 'João Silva', 
    status: 'concluído', 
    observacoes: 'Instalação em prédio novo',
    materiais: ['Cabo fibra 100m', 'Conector SC/APC', 'Splitter 1:4', 'ONT Huawei'],
    endereco: 'Rua do Carmo, 71 - Lisboa',
    coordenadas: '38.7118, -9.1400'
  },
];

const ProcessedServicesHistory = ({ viewMode = 'list', filterStatus = 'todas' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [dateRange, setDateRange] = useState('30dias');
  const [sortBy, setSortBy] = useState('data');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedService, setSelectedService] = useState(null);
  
  // Aplicar filtros com base nos parâmetros
  React.useEffect(() => {
    if (filterStatus === 'todas') {
      setStatusFilter('todos');
    } else if (filterStatus === 'concluidas') {
      setStatusFilter('concluído');
    } else if (filterStatus === 'erros') {
      setStatusFilter('erro');
    } else if (filterStatus === 'pendentes') {
      setStatusFilter('pendente');
    }
  }, [filterStatus]);
  
  // Filtrar serviços com base nos critérios
  const filteredServices = mockProcessedPDFs.filter(service => {
    // Filtro de pesquisa
    const matchesSearch = service.wo.includes(searchTerm) || 
                          service.tecnico.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          service.observacoes.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          service.endereco.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Filtro de status
    const matchesStatus = statusFilter === 'todos' || service.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });
  
  // Ordenar serviços
  const sortedServices = [...filteredServices].sort((a, b) => {
    if (sortBy === 'data') {
      // Converter datas para comparação (formato DD/MM/YYYY)
      const dateA = a.data.split('/').reverse().join('');
      const dateB = b.data.split('/').reverse().join('');
      return sortOrder === 'asc' ? dateA.localeCompare(dateB) : dateB.localeCompare(dateA);
    } else if (sortBy === 'wo') {
      return sortOrder === 'asc' ? a.wo.localeCompare(b.wo) : b.wo.localeCompare(a.wo);
    } else if (sortBy === 'tecnico') {
      return sortOrder === 'asc' ? a.tecnico.localeCompare(b.tecnico) : b.tecnico.localeCompare(a.tecnico);
    }
    return 0;
  });
  
  // Alternar ordem de classificação
  const toggleSortOrder = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };
  
  // Exportar histórico
  const exportHistory = (format) => {
    alert(`Exportando histórico em formato ${format}...`);
    // Implementação real conectaria com backend para gerar e baixar o arquivo
  };

  // Função para abrir mapa
  const openMap = (coordinates) => {
    window.open(`https://www.google.com/maps/search/?api=1&query=${coordinates}`, '_blank');
  };
  
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      {/* Barra de filtros e pesquisa */}
      <div className="p-4 border-b border-gray-100 bg-gray-50">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input 
              type="text" 
              placeholder="Buscar WO, técnico, endereço..." 
              className="w-full bg-white border border-gray-200 rounded-lg py-2 pl-9 pr-3 text-sm text-[#555]"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#777]" />
          </div>
          
          <div className="flex gap-2">
            <div className="relative">
              <select 
                className="appearance-none bg-white border border-gray-200 rounded-lg py-2 pl-3 pr-10 text-sm text-[#555]"
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
              >
                <option value="7dias">7 dias</option>
                <option value="30dias">30 dias</option>
                <option value="90dias">90 dias</option>
                <option value="todos">Todos</option>
              </select>
              <Calendar size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#777]" />
            </div>
          </div>
        </div>
      </div>
      
      {/* Visualização em lista */}
      {viewMode === 'list' && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">
                    <button 
                      className="flex items-center gap-1"
                      onClick={() => toggleSortOrder('data')}
                    >
                      Data
                      {sortBy === 'data' && (
                        <ArrowUpDown size={14} className={`${sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform`} />
                      )}
                    </button>
                  </th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">
                    <button 
                      className="flex items-center gap-1"
                      onClick={() => toggleSortOrder('wo')}
                    >
                      WO
                      {sortBy === 'wo' && (
                        <ArrowUpDown size={14} className={`${sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform`} />
                      )}
                    </button>
                  </th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider hidden md:table-cell">
                    <button 
                      className="flex items-center gap-1"
                      onClick={() => toggleSortOrder('tecnico')}
                    >
                      Técnico
                      {sortBy === 'tecnico' && (
                        <ArrowUpDown size={14} className={`${sortOrder === 'asc' ? 'rotate-180' : ''} transition-transform`} />
                      )}
                    </button>
                  </th>
                  <th className="py-3 px-4 text-left text-xs font-medium text-[#555] uppercase tracking-wider">Status</th>
                  <th className="py-3 px-4 text-right text-xs font-medium text-[#555] uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sortedServices.length > 0 ? (
                  sortedServices.map((service) => (
                    <tr key={service.id} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap">{service.data}</td>
                      <td className="py-3 px-4 text-sm font-medium text-[#333] whitespace-nowrap">#{service.wo}</td>
                      <td className="py-3 px-4 text-sm text-[#555] whitespace-nowrap hidden md:table-cell">{service.tecnico}</td>
                      <td className="py-3 px-4 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          service.status === 'concluído' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {service.status === 'concluído' ? 'Concluído' : 'Erro'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-right">
                        <button 
                          className="text-purple-600 hover:text-purple-800 font-medium"
                          onClick={() => setSelectedService(service)}
                        >
                          Ver detalhes
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="py-8 text-center text-gray-500">
                      Nenhuma work order encontrada com os filtros atuais
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="p-4 border-t border-gray-100 bg-gray-50 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="text-sm text-[#777]">
              Exibindo {sortedServices.length} de {mockProcessedPDFs.length} serviços
            </div>
            <div className="flex items-center gap-2">
              <button 
                className="text-sm text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                onClick={() => exportHistory('csv')}
              >
                <Download size={16} />
                <span>CSV</span>
              </button>
              <button 
                className="text-sm text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                onClick={() => exportHistory('pdf')}
              >
                <Download size={16} />
                <span>PDF</span>
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Visualização em grade */}
      {viewMode === 'grid' && (
        <>
          <div className="p-4">
            {sortedServices.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedServices.map((service) => (
                  <div 
                    key={service.id} 
                    className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                  >
                    <div className={`p-3 ${
                      service.status === 'concluído' 
                        ? 'bg-green-50 border-b border-green-100' 
                        : 'bg-red-50 border-b border-red-100'
                    }`}>
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-[#333]">WO #{service.wo}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          service.status === 'concluído' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {service.status === 'concluído' ? 'Concluído' : 'Erro'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="p-4">
                      <div className="flex items-start gap-3 mb-3">
                        <Clock size={16} className="text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500">Data</p>
                          <p className="text-sm text-[#333]">{service.data}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3 mb-3">
                        <User size={16} className="text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500">Técnico</p>
                          <p className="text-sm text-[#333]">{service.tecnico}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start gap-3">
                        <MapPin size={16} className="text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500">Endereço</p>
                          <p className="text-sm text-[#333] truncate" title={service.endereco}>
                            {service.endereco}
                          </p>
                        </div>
                      </div>
                      
                      <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end">
                        <button 
                          className="text-purple-600 hover:text-purple-800 font-medium text-sm"
                          onClick={() => setSelectedService(service)}
                        >
                          Ver detalhes
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-gray-500">
                Nenhuma work order encontrada com os filtros atuais
              </div>
            )}
          </div>
          
          <div className="p-4 border-t border-gray-100 bg-gray-50 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="text-sm text-[#777]">
              Exibindo {sortedServices.length} de {mockProcessedPDFs.length} serviços
            </div>
            <div className="flex items-center gap-2">
              <button 
                className="text-sm text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                onClick={() => exportHistory('csv')}
              >
                <Download size={16} />
                <span>CSV</span>
              </button>
              <button 
                className="text-sm text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                onClick={() => exportHistory('pdf')}
              >
                <Download size={16} />
                <span>PDF</span>
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Modal de detalhes do serviço - redesenhado para melhor experiência mobile */}
      {selectedService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Cabeçalho do modal */}
            <div className={`p-4 ${
              selectedService.status === 'concluído' 
                ? 'bg-green-50' 
                : 'bg-red-50'
            }`}>
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold text-[#333]">WO #{selectedService.wo}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      selectedService.status === 'concluído' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {selectedService.status === 'concluído' ? 'Concluído' : 'Erro'}
                    </span>
                    <span className="text-xs text-gray-500">{selectedService.data}</span>
                  </div>
                </div>
                <button 
                  className="text-gray-400 hover:text-gray-600 p-1"
                  onClick={() => setSelectedService(null)}
                  aria-label="Fechar"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Conteúdo do modal com scroll */}
            <div className="p-4 overflow-y-auto flex-1">
              {/* Informações principais */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="flex items-start gap-3">
                  <User size={18} className="text-purple-600 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Técnico</p>
                    <p className="text-[#333] font-medium">{selectedService.tecnico}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <MapPin size={18} className="text-purple-600 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Endereço</p>
                    <p className="text-[#333]">{selectedService.endereco}</p>
                    <button 
                      className="text-xs text-purple-600 hover:text-purple-800 mt-1 flex items-center gap-1"
                      onClick={() => openMap(selectedService.coordenadas)}
                    >
                      Ver no mapa
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Observações */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-[#333] mb-2 flex items-center gap-2">
                  <FileText size={16} className="text-purple-600" />
                  Observações
                </h3>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                  <p className="text-sm text-[#555]">{selectedService.observacoes}</p>
                </div>
              </div>
              
              {/* Materiais */}
              <div>
                <h3 className="text-sm font-medium text-[#333] mb-2 flex items-center gap-2">
                  <Package size={16} className="text-purple-600" />
                  Materiais Utilizados
                </h3>
                {selectedService.materiais.length > 0 ? (
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <ul className="space-y-1">
                      {selectedService.materiais.map((material, index) => (
                        <li key={index} className="text-sm text-[#555] flex items-center gap-2">
                          <span className="w-1.5 h-1.5 bg-purple-600 rounded-full"></span>
                          {material}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <p className="text-sm text-[#555]">Nenhum material registrado</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Rodapé do modal */}
            <div className="p-4 border-t border-gray-100 bg-gray-50 flex flex-col sm:flex-row gap-3 justify-end">
              <button 
                className="px-4 py-2 border border-gray-200 rounded-lg text-[#555] hover:bg-gray-100 transition-colors text-sm font-medium"
                onClick={() => setSelectedService(null)}
              >
                Fechar
              </button>
              <button 
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                onClick={() => alert(`Baixando PDF da WO #${selectedService.wo}`)}
              >
                <Download size={16} />
                <span>Baixar PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessedServicesHistory;
