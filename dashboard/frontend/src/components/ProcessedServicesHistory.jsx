import React, { useState } from 'react';
import { FileText, Search, Filter, Download, Calendar, ArrowUpDown } from 'lucide-react';

const mockProcessedPDFs = [
  { 
    id: '12345',
    data: '22/05/2025', 
    wo: '12345', 
    tecnico: 'João Silva', 
    status: 'concluído', 
    observacoes: 'Instalação concluída com sucesso',
    materiais: ['Cabo fibra 50m', 'Conector SC/APC', 'Splitter 1:8']
  },
  { 
    id: '12344',
    data: '21/05/2025', 
    wo: '12344', 
    tecnico: 'Maria Santos', 
    status: 'concluído', 
    observacoes: 'Cliente não estava presente, reagendado',
    materiais: ['Cabo fibra 30m', 'Conector SC/APC']
  },
  { 
    id: '12343',
    data: '20/05/2025', 
    wo: '12343', 
    tecnico: 'Carlos Oliveira', 
    status: 'erro', 
    observacoes: 'Endereço incorreto no sistema',
    materiais: []
  },
  { 
    id: '12342',
    data: '19/05/2025', 
    wo: '12342', 
    tecnico: 'Ana Pereira', 
    status: 'concluído', 
    observacoes: 'Substituição de ONT realizada',
    materiais: ['ONT Huawei', 'Cabo patch 2m']
  },
  { 
    id: '12341',
    data: '18/05/2025', 
    wo: '12341', 
    tecnico: 'João Silva', 
    status: 'concluído', 
    observacoes: 'Instalação em prédio novo',
    materiais: ['Cabo fibra 100m', 'Conector SC/APC', 'Splitter 1:4', 'ONT Huawei']
  },
];

const ProcessedServicesHistory = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('todos');
  const [dateRange, setDateRange] = useState('30dias');
  const [sortBy, setSortBy] = useState('data');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedService, setSelectedService] = useState(null);
  
  // Filtrar serviços com base nos critérios
  const filteredServices = mockProcessedPDFs.filter(service => {
    // Filtro de pesquisa
    const matchesSearch = service.wo.includes(searchTerm) || 
                          service.tecnico.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          service.observacoes.toLowerCase().includes(searchTerm.toLowerCase());
    
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
  
  return (
    <div className="bg-white rounded-xl shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText size={20} className="text-[#7C3AED]" />
          <h2 className="text-lg font-semibold text-[#333]">Histórico de Serviços Processados</h2>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <select 
              className="appearance-none bg-gray-50 border border-gray-200 rounded-lg py-2 pl-3 pr-10 text-sm text-[#555]"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
            >
              <option value="7dias">Últimos 7 dias</option>
              <option value="30dias">Últimos 30 dias</option>
              <option value="90dias">Últimos 90 dias</option>
              <option value="todos">Todos</option>
            </select>
            <Calendar size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#777]" />
          </div>
          
          <div className="relative">
            <select 
              className="appearance-none bg-gray-50 border border-gray-200 rounded-lg py-2 pl-3 pr-10 text-sm text-[#555]"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="todos">Todos os status</option>
              <option value="concluído">Concluídos</option>
              <option value="erro">Com erro</option>
            </select>
            <Filter size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#777]" />
          </div>
          
          <div className="relative">
            <input 
              type="text" 
              placeholder="Buscar WO, técnico..." 
              className="bg-gray-50 border border-gray-200 rounded-lg py-2 pl-9 pr-3 text-sm text-[#555] w-48"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#777]" />
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full min-w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-3 text-left text-sm font-medium text-[#555]">
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
              <th className="py-3 text-left text-sm font-medium text-[#555]">
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
              <th className="py-3 text-left text-sm font-medium text-[#555]">
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
              <th className="py-3 text-left text-sm font-medium text-[#555]">Status</th>
              <th className="py-3 text-left text-sm font-medium text-[#555]">Ações</th>
            </tr>
          </thead>
          <tbody>
            {sortedServices.map((service) => (
              <tr key={service.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 text-sm text-[#555]">{service.data}</td>
                <td className="py-3 text-sm text-[#555]">#{service.wo}</td>
                <td className="py-3 text-sm text-[#555]">{service.tecnico}</td>
                <td className="py-3 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    service.status === 'concluído' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {service.status === 'concluído' ? 'Concluído' : 'Erro'}
                  </span>
                </td>
                <td className="py-3 text-sm">
                  <button 
                    className="text-[#7C3AED] hover:underline"
                    onClick={() => setSelectedService(service)}
                  >
                    Ver detalhes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 flex justify-between items-center">
        <div className="text-sm text-[#777]">
          Exibindo {sortedServices.length} de {mockProcessedPDFs.length} serviços
        </div>
        <div className="flex items-center gap-2">
          <button 
            className="text-sm text-[#7C3AED] hover:underline flex items-center gap-1"
            onClick={() => exportHistory('csv')}
          >
            <Download size={16} />
            <span>Exportar CSV</span>
          </button>
          <button 
            className="text-sm text-[#7C3AED] hover:underline flex items-center gap-1"
            onClick={() => exportHistory('pdf')}
          >
            <Download size={16} />
            <span>Exportar PDF</span>
          </button>
        </div>
      </div>
      
      {/* Modal de detalhes do serviço */}
      {selectedService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-semibold text-[#333]">Detalhes do Serviço</h2>
                <p className="text-sm text-[#777]">WO #{selectedService.wo}</p>
              </div>
              <button 
                className="text-[#777] hover:text-[#333]"
                onClick={() => setSelectedService(null)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-sm text-[#777]">Data</p>
                <p className="text-[#333]">{selectedService.data}</p>
              </div>
              <div>
                <p className="text-sm text-[#777]">Técnico</p>
                <p className="text-[#333]">{selectedService.tecnico}</p>
              </div>
              <div>
                <p className="text-sm text-[#777]">Status</p>
                <p>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    selectedService.status === 'concluído' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedService.status === 'concluído' ? 'Concluído' : 'Erro'}
                  </span>
                </p>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-sm text-[#777] mb-1">Observações</p>
              <p className="text-[#333] p-3 bg-gray-50 rounded-lg">{selectedService.observacoes}</p>
            </div>
            
            <div>
              <p className="text-sm text-[#777] mb-1">Materiais Utilizados</p>
              {selectedService.materiais.length > 0 ? (
                <ul className="list-disc list-inside p-3 bg-gray-50 rounded-lg">
                  {selectedService.materiais.map((material, index) => (
                    <li key={index} className="text-[#333]">{material}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-[#333] p-3 bg-gray-50 rounded-lg">Nenhum material registrado</p>
              )}
            </div>
            
            <div className="mt-6 flex justify-end gap-3">
              <button 
                className="border border-gray-200 px-4 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition"
                onClick={() => setSelectedService(null)}
              >
                Fechar
              </button>
              <button 
                className="bg-[#7C3AED] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#6B21A8] transition flex items-center gap-2"
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
