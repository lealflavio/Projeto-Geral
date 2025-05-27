import React, { useState, useEffect } from "react";
import { Search, MapPin, Share2, Download, Clipboard, ArrowRight, Copy } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://SEU_BACKEND_URL"; // Ajuste conforme seu backend

// Função para limpar e formatar a morada
const formatarMorada = (morada) => {
  if (!morada) return "N/A";
  
  // Remove colchetes, traços duplos e espaços extras
  return morada
    .replace(/[\[\]]/g, '')
    .replace(/\s-\s-\s/g, ', ')
    .replace(/\s-\s/g, ', ')
    .replace(/\s+/g, ' ')
    .trim();
};

// Função para extrair informações específicas do texto do cliente
const extrairInformacoes = (textoCliente) => {
  if (!textoCliente) return {};
  
  // Extrair Acesso (9 dígitos após "Access:")
  const accessMatch = textoCliente.match(/Access:(\d{9})/);
  const acesso = accessMatch ? accessMatch[1] : "N/A";
  
  // Extrair Nº de Box
  const boxMatch = textoCliente.match(/NUMERO_TV_BOXES:\s*(\d+)/);
  const numBox = boxMatch ? boxMatch[1] : "N/A";
  
  // Extrair Tipo de Box
  const tipoBoxMatch = textoCliente.match(/Set-Top-Boxes:\s*([^V][^\n]+?)(?=\s+Velocidade)/);
  const tipoBox = tipoBoxMatch ? tipoBoxMatch[1].trim() : "N/A";
  
  // Extrair Telefone
  const telefoneMatch = textoCliente.match(/Entrega de equipamentos:\s*([^\n]+?)(?=\s+Modelo)/);
  const telefone = telefoneMatch ? telefoneMatch[1].trim() : "N/A";
  
  // Extrair SLID (se existir no texto)
  const slidMatch = textoCliente.match(/SLID:\s*([^\s,;]+)/);
  const slid = slidMatch ? slidMatch[1] : "";
  
  return { acesso, numBox, tipoBox, telefone, slid };
};

// Função para salvar WO no cache
const salvarWOCache = (woData) => {
  try {
    // Obter cache atual
    const cacheString = localStorage.getItem('woCache');
    const cache = cacheString ? JSON.parse(cacheString) : {};
    
    // Adicionar nova entrada com timestamp
    cache[woData.numero] = {
      data: woData,
      timestamp: Date.now(),
      expira: Date.now() + (3 * 24 * 60 * 60 * 1000) // 3 dias em milissegundos
    };
    
    // Salvar cache atualizado
    localStorage.setItem('woCache', JSON.stringify(cache));
  } catch (error) {
    console.error("Erro ao salvar WO no cache:", error);
  }
};

// Função para obter WO do cache
const obterWOCache = (woNumero) => {
  try {
    const cacheString = localStorage.getItem('woCache');
    if (!cacheString) return null;
    
    const cache = JSON.parse(cacheString);
    const entry = cache[woNumero];
    
    // Verificar se existe e não expirou
    if (entry && entry.expira > Date.now()) {
      return entry.data;
    }
    
    // Se expirou, remover do cache
    if (entry) {
      delete cache[woNumero];
      localStorage.setItem('woCache', JSON.stringify(cache));
    }
    
    return null;
  } catch (error) {
    console.error("Erro ao obter WO do cache:", error);
    return null;
  }
};

// Função para obter histórico de WOs recentes
const obterHistoricoWOs = () => {
  try {
    const cacheString = localStorage.getItem('woCache');
    if (!cacheString) return [];
    
    const cache = JSON.parse(cacheString);
    const agora = Date.now();
    
    // Filtrar entradas não expiradas e ordenar por timestamp (mais recentes primeiro)
    return Object.entries(cache)
      .filter(([_, entry]) => entry.expira > agora)
      .map(([numero, entry]) => ({
        numero,
        morada: entry.data.morada,
        timestamp: entry.timestamp
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  } catch (error) {
    console.error("Erro ao obter histórico de WOs:", error);
    return [];
  }
};

const WorkOrderAllocation = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [usuario, setUsuario] = useState(null);
  const [historicoWOs, setHistoricoWOs] = useState([]);
  const [copiedField, setCopiedField] = useState('');

  // Carrega sempre o usuário atualizado da API ao montar o componente
  useEffect(() => {
    const fetchUsuario = async () => {
      try {
        const token = localStorage.getItem("authToken");
        if (!token) {
          alert("Token de autenticação não encontrado. Faça login novamente.");
          return;
        }
        const response = await fetch(`${API_BASE_URL}/usuarios/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) throw new Error("Erro ao buscar usuário");
        const dados = await response.json();
        setUsuario(dados);
        // Atualiza o localStorage para manter sincronizado
        localStorage.setItem("usuario", JSON.stringify(dados));
      } catch (err) {
        alert("Erro ao buscar usuário. Faça login novamente.");
      }
    };
    
    fetchUsuario();
    
    // Carregar histórico de WOs
    setHistoricoWOs(obterHistoricoWOs());
  }, []);

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      alert("Informe o número da WO.");
      return;
    }
    if (!usuario?.usuario_portal || !usuario?.senha_portal) {
      alert("Credenciais do portal Wondercom não cadastradas. Cadastre no Perfil antes de usar esta função.");
      return;
    }
    
    // Verificar se a WO está no cache
    const cachedWO = obterWOCache(searchTerm);
    if (cachedWO) {
      setSearchResult(cachedWO);
      return;
    }

    setIsSearching(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/wondercom/allocate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          work_order_id: searchTerm,
          credentials: {
            username: usuario.usuario_portal,
            password: usuario.senha_portal
          }
        })
      });
      const data = await response.json();
      if (data.status === 'success' && data.data) {
        // Extrair informações do cliente
        const infoCliente = extrairInformacoes(data.data.descricao || "");
        
        // Formatar morada
        const moradaFormatada = formatarMorada(data.data.endereco);
        
        // Criar objeto de resultado
        const resultado = {
          numero: searchTerm,
          cliente: data.data.descricao || "N/A",
          morada: moradaFormatada,
          coordenadas: {
            lat: data.data.latitude || 0,
            lng: data.data.longitude || 0
          },
          corFibra: data.data.cor_fibra || "N/A",
          tipoServico: data.data.tipo_servico || "N/A",
          dataAgendamento: data.data.data_agendamento || "N/A",
          horario: data.data.horario || "N/A",
          observacoes: data.data.estado || data.data.observacoes || "",
          // Informações extraídas
          acesso: infoCliente.acesso,
          numBox: infoCliente.numBox,
          tipoBox: infoCliente.tipoBox,
          telefone: infoCliente.telefone,
          slid: infoCliente.slid || data.data.slid || ""
        };
        
        setSearchResult(resultado);
        
        // Salvar no cache
        salvarWOCache(resultado);
        
        // Atualizar histórico
        setHistoricoWOs(obterHistoricoWOs());
      } else {
        alert('Erro ao alocar WO: ' + (data.error || data.message || 'Erro desconhecido'));
        setSearchResult(null);
      }
    } catch (error) {
      alert("Erro: " + error.message);
      setSearchResult(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleCopyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopiedField(field);
        setTimeout(() => setCopiedField(''), 2000);
      })
      .catch(err => console.error('Erro ao copiar: ', err));
  };

  const handleShare = () => {
    if (!searchResult) return;
    const shareText = `
      WO: ${searchResult.numero}
      Acesso: ${searchResult.acesso}
      Nº de Box: ${searchResult.numBox}
      Tipo de Box: ${searchResult.tipoBox}
      Morada: ${searchResult.morada}
      Cor da Fibra: ${searchResult.corFibra}
      Data: ${searchResult.dataAgendamento}
      Horário: ${searchResult.horario}
      ${searchResult.slid ? `SLID: ${searchResult.slid}` : ''}
    `;
    if (navigator.share) {
      navigator.share({
        title: `WO #${searchResult.numero}`,
        text: shareText,
      }).catch(err => console.error('Erro ao compartilhar: ', err));
    } else {
      handleCopyToClipboard(shareText, 'compartilhamento');
    }
  };

  const carregarWOHistorico = (numero) => {
    setSearchTerm(numero);
    const cachedWO = obterWOCache(numero);
    if (cachedWO) {
      setSearchResult(cachedWO);
    } else {
      handleSearch();
    }
  };

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Alocação de Work Order</h1>
      {/* Formulário de busca */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <label htmlFor="wo-search" className="block text-sm text-[#555] mb-2">
              Número da Work Order
            </label>
            <input
              id="wo-search"
              type="text"
              placeholder="Ex: 12345678"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg py-2 pl-3 pr-10 text-[#333]"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <div className="md:self-end">
            <button
              className="w-full md:w-auto bg-[#7C3AED] text-white px-6 py-2 rounded-lg font-medium hover:bg-[#6B21A8] transition flex items-center justify-center gap-2"
              onClick={handleSearch}
              disabled={isSearching}
            >
              {isSearching ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Buscando...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Buscar</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Histórico de WOs */}
      {historicoWOs.length > 0 && !searchResult && (
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-[#333] mb-3">Histórico de WOs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {historicoWOs.slice(0, 6).map((wo) => (
              <div 
                key={wo.numero}
                className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition"
                onClick={() => carregarWOHistorico(wo.numero)}
              >
                <p className="font-medium text-[#7C3AED]">WO #{wo.numero}</p>
                <p className="text-sm text-[#555] truncate">{wo.morada}</p>
                <p className="text-xs text-[#777] mt-1">
                  {new Date(wo.timestamp).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Resultado da busca */}
      {searchResult && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          {/* Cabeçalho */}
          <div className="bg-[#7C3AED] p-4 text-white flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">WO #{searchResult.numero}</h2>
              <p className="text-sm text-purple-200">{searchResult.tipoServico}</p>
            </div>
            <div className="flex gap-2">
              <button
                className="p-2 rounded-full hover:bg-purple-700 transition"
                onClick={handleShare}
                title="Compartilhar"
              >
                <Share2 size={20} />
              </button>
              <button
                className="p-2 rounded-full hover:bg-purple-700 transition"
                onClick={() => alert('Download do PDF iniciado')}
                title="Baixar PDF"
              >
                <Download size={20} />
              </button>
            </div>
          </div>
          {/* Conteúdo */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Coluna 1 - Informações Essenciais */}
              <div>
                {/* Informações do Cliente - Apenas as essenciais */}
                <div className="mb-6 bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-[#555] mb-3">Informações Essenciais</h3>
                  
                  <div className="mb-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-[#777]">Acesso</span>
                      <button
                        className={`text-xs ${copiedField === 'acesso' ? 'text-green-500' : 'text-[#7C3AED]'} hover:text-purple-700`}
                        onClick={() => handleCopyToClipboard(searchResult.acesso, 'acesso')}
                      >
                        {copiedField === 'acesso' ? 'Copiado!' : 'Copiar'}
                      </button>
                    </div>
                    <p className="text-[#333] font-medium">{searchResult.acesso}</p>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-[#777]">Nº de Box</span>
                      <button
                        className={`text-xs ${copiedField === 'numBox' ? 'text-green-500' : 'text-[#7C3AED]'} hover:text-purple-700`}
                        onClick={() => handleCopyToClipboard(searchResult.numBox, 'numBox')}
                      >
                        {copiedField === 'numBox' ? 'Copiado!' : 'Copiar'}
                      </button>
                    </div>
                    <p className="text-[#333] font-medium">{searchResult.numBox}</p>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-[#777]">Tipo de Box</span>
                      <button
                        className={`text-xs ${copiedField === 'tipoBox' ? 'text-green-500' : 'text-[#7C3AED]'} hover:text-purple-700`}
                        onClick={() => handleCopyToClipboard(searchResult.tipoBox, 'tipoBox')}
                      >
                        {copiedField === 'tipoBox' ? 'Copiado!' : 'Copiar'}
                      </button>
                    </div>
                    <p className="text-[#333] font-medium">{searchResult.tipoBox}</p>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-[#777]">Telefone</span>
                      <button
                        className={`text-xs ${copiedField === 'telefone' ? 'text-green-500' : 'text-[#7C3AED]'} hover:text-purple-700`}
                        onClick={() => handleCopyToClipboard(searchResult.telefone, 'telefone')}
                      >
                        {copiedField === 'telefone' ? 'Copiado!' : 'Copiar'}
                      </button>
                    </div>
                    <p className="text-[#333] font-medium">{searchResult.telefone}</p>
                  </div>
                  
                  {searchResult.slid && (
                    <div className="mt-4 pt-3 border-t border-gray-200">
                      <div className="flex justify-between">
                        <span className="text-xs text-[#777]">SLID</span>
                        <button
                          className={`text-xs ${copiedField === 'slid' ? 'text-green-500' : 'text-[#7C3AED]'} hover:text-purple-700`}
                          onClick={() => handleCopyToClipboard(searchResult.slid, 'slid')}
                        >
                          {copiedField === 'slid' ? 'Copiado!' : 'Copiar'}
                        </button>
                      </div>
                      <p className="text-[#333] font-medium">{searchResult.slid}</p>
                    </div>
                  )}
                </div>
                
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Morada</h3>
                  <div className="flex items-start gap-2">
                    <p className="text-[#333] flex-1">{searchResult.morada}</p>
                    <button
                      className={`text-[#7C3AED] p-1 hover:bg-purple-50 rounded-full transition ${copiedField === 'morada' ? 'bg-green-50 text-green-500' : ''}`}
                      onClick={() => handleCopyToClipboard(searchResult.morada, 'morada')}
                      title={copiedField === 'morada' ? 'Copiado!' : 'Copiar morada'}
                    >
                      <Clipboard size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Cor da Fibra</h3>
                  <div className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full bg-blue-500`}></div>
                    <p className="text-[#333]">{searchResult.corFibra}</p>
                  </div>
                </div>
              </div>
              
              {/* Coluna 2 */}
              <div>
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Data de Agendamento</h3>
                  <p className="text-[#333]">{searchResult.dataAgendamento}</p>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Horário</h3>
                  <p className="text-[#333]">{searchResult.horario}</p>
                </div>
                
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Estado da WO</h3>
                  <p className="text-[#333] p-3 bg-gray-50 rounded-lg text-sm">
                    {searchResult.observacoes}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Mapa - Oculto por padrão, sem mostrar coordenadas */}
            <div className="mt-4">
              <button
                className="flex items-center gap-2 text-[#7C3AED] hover:underline"
                onClick={() => setShowMap(!showMap)}
              >
                <MapPin size={18} />
                <span>{showMap ? 'Ocultar mapa' : 'Ver no mapa'}</span>
                <ArrowRight size={16} className={`transition-transform ${showMap ? 'rotate-90' : ''}`} />
              </button>
              {showMap && (
                <div className="mt-4 bg-gray-100 rounded-lg p-2 h-64 flex items-center justify-center">
                  <div className="text-center">
                    <MapPin size={32} className="mx-auto mb-2 text-[#7C3AED]" />
                    <p className="text-[#555]">
                      Mapa interativo seria exibido aqui
                    </p>
                    <button
                      className="mt-2 text-sm text-[#7C3AED] hover:underline"
                      onClick={() => window.open(`https://www.google.com/maps/search/?api=1&query=${searchResult.coordenadas.lat},${searchResult.coordenadas.lng}`, '_blank')}
                    >
                      Abrir no Google Maps
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {/* Botões de ação */}
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <button
                className="flex-1 bg-[#7C3AED] text-white py-2 rounded-lg font-medium hover:bg-[#6B21A8] transition"
                onClick={() => alert('Alocando WO para processamento...')}
              >
                Alocar para Processamento
              </button>
              <button
                className="flex-1 border border-gray-200 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition"
                onClick={() => setSearchResult(null)}
              >
                Nova Busca
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkOrderAllocation;
