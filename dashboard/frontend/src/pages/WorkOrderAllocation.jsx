import React, { useState, useEffect } from "react";
import { Search, MapPin, Share2, Download, Clipboard, ArrowRight, Copy, Navigation } from "lucide-react";

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

// Função para formatar o estado da WO (primeira letra maiúscula de cada palavra)
const formatarEstadoWO = (estado) => {
  if (!estado) return "N/A";
  
  return estado
    .toLowerCase()
    .split(' ')
    .map(palavra => palavra.charAt(0).toUpperCase() + palavra.slice(1))
    .join(' ');
};

// Função para determinar a cor da fibra
const determinarCorFibra = (nomeFibra) => {
  if (!nomeFibra || nomeFibra === "N/A") return null;
  
  const cores = {
    'azul': '#1E90FF',
    'amarelo': '#FFD700',
    'vermelho': '#FF4500',
    'preto': '#000000',
    'laranja': '#FFA500',
    'ciano': '#00FFFF',
    'castanho': '#8B4513',
    'cinza': '#808080',
    'branco': '#FFFFFF',
    'verde': '#32CD32',
    'violeta': '#8A2BE2',
    'rosa': '#FF69B4',
    'turquesa': '#40E0D0'
  };
  
  // Verificar se o nome da fibra contém alguma das cores
  for (const [cor, hex] of Object.entries(cores)) {
    if (nomeFibra.toLowerCase().includes(cor)) {
      return { nome: cor, hex };
    }
  }
  
  return null;
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
  const [showMapOptions, setShowMapOptions] = useState(false);
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
      // Obter token de autenticação
      const token = localStorage.getItem("authToken");
      if (!token) {
        alert("Token de autenticação não encontrado. Faça login novamente.");
        setIsSearching(false);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/wondercom/allocate`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Incluir token de autenticação
        },
        body: JSON.stringify({
          work_order_id: searchTerm,
          credentials: {
            username: usuario.usuario_portal,
            password: usuario.senha_portal
          }
        })
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          alert("Sessão expirada. Por favor, faça login novamente.");
          // Redirecionar para login ou limpar token
          localStorage.removeItem("authToken");
          window.location.href = "/login";
          return;
        }
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.status === 'success' && data.data) {
        // Extrair informações do cliente
        const infoCliente = extrairInformacoes(data.data.descricao || "");
        
        // Formatar morada
        const moradaFormatada = formatarMorada(data.data.endereco);
        
        // Formatar estado da WO
        const estadoFormatado = formatarEstadoWO(data.data.estado || data.data.observacoes || "");
        
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
          observacoes: estadoFormatado,
          // Informações extraídas
          acesso: infoCliente.acesso,
          numBox: infoCliente.numBox,
          tipoBox: infoCliente.tipoBox,
          telefone: infoCliente.telefone,
          slid: infoCliente.slid || data.data.slid || "CAKIBALE" // Valor fixo temporário
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
      Fibra: ${searchResult.corFibra}
      Data: ${searchResult.dataAgendamento}
      Horário: ${searchResult.horario}
      ${searchResult.slid ? `SLID: ${searchResult.slid}` : ''}
    `;
    if (navigator.share) {
      navigator.share({
        title: `WO ${searchResult.numero}`,
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

  const abrirMapa = (app) => {
    if (!searchResult) return;
    
    const { lat, lng } = searchResult.coordenadas;
    let url = '';
    
    switch(app) {
      case 'google':
        url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
        break;
      case 'waze':
        url = `https://waze.com/ul?ll=${lat},${lng}&navigate=yes`;
        break;
      case 'apple':
        url = `http://maps.apple.com/?ll=${lat},${lng}`;
        break;
      case 'osm':
        url = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}`;
        break;
      default:
        url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
    }
    
    window.open(url, '_blank');
    setShowMapOptions(false);
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
                <p className="font-medium text-[#7C3AED]">WO {wo.numero}</p>
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
              <h2 className="text-lg font-semibold">WO {searchResult.numero}</h2>
              <p className="text-sm text-purple-200">{searchResult.observacoes}</p>
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
              {/* Coluna 1 */}
              <div>
                {/* SLID */}
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">SLID</h3>
                  <div className="flex items-start gap-2">
                    <p className="text-[#333] font-medium flex-1">{searchResult.slid || "CAKIBALE"}</p>
                    <button
                      className={`text-[#7C3AED] p-1 hover:bg-purple-50 rounded-full transition ${copiedField === 'slid' ? 'bg-green-50 text-green-500' : ''}`}
                      onClick={() => handleCopyToClipboard(searchResult.slid || "CAKIBALE", 'slid')}
                      title={copiedField === 'slid' ? 'Copiado!' : 'Copiar SLID'}
                    >
                      <Clipboard size={16} />
                    </button>
                  </div>
                </div>
                
                {/* Fibra */}
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Fibra</h3>
                  <div className="flex items-center gap-2">
                    {determinarCorFibra(searchResult.corFibra) && (
                      <div 
                        className="w-4 h-4 rounded-full" 
                        style={{ backgroundColor: determinarCorFibra(searchResult.corFibra).hex }}
                      ></div>
                    )}
                    <p className="text-[#333]">{searchResult.corFibra}</p>
                  </div>
                </div>
                
                {/* Morada */}
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
                
                {/* Informações */}
                <div className="mb-6 bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-[#555] mb-3">Informações</h3>
                  
                  <div className="mb-2">
                    <span className="text-xs text-[#777]">Acesso</span>
                    <p className="text-[#333] font-medium">{searchResult.acesso}</p>
                  </div>
                  
                  <div className="mb-2">
                    <span className="text-xs text-[#777]">Nº de Box</span>
                    <p className="text-[#333] font-medium">{searchResult.numBox}</p>
                  </div>
                  
                  <div className="mb-2">
                    <span className="text-xs text-[#777]">Tipo de Box</span>
                    <p className="text-[#333] font-medium">{searchResult.tipoBox}</p>
                  </div>
                  
                  <div className="mb-2">
                    <span className="text-xs text-[#777]">Instalar Telefone?</span>
                    <p className="text-[#333] font-medium">{searchResult.telefone}</p>
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
                
                {/* Mapa - Melhorado com opções de aplicativos */}
                <div className="mt-4">
                  <button
                    className="flex items-center gap-2 text-[#7C3AED] hover:underline"
                    onClick={() => {
                      setShowMap(!showMap);
                      setShowMapOptions(false);
                    }}
                  >
                    <MapPin size={18} />
                    <span>{showMap ? 'Ocultar mapa' : 'Ver no mapa'}</span>
                    <ArrowRight size={16} className={`transition-transform ${showMap ? 'rotate-90' : ''}`} />
                  </button>
                  
                  {showMap && (
                    <div className="mt-4 bg-gray-100 rounded-lg p-4 h-auto">
                      <div className="text-center mb-4">
                        <MapPin size={32} className="mx-auto mb-2 text-[#7C3AED]" />
                        <p className="text-[#555] mb-4">
                          Selecione um aplicativo para abrir as coordenadas
                        </p>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          <button
                            className="flex flex-col items-center justify-center p-3 bg-white rounded-lg hover:bg-gray-50 transition"
                            onClick={() => abrirMapa('google')}
                          >
                            <img 
                              src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Google_Maps_icon_%282020%29.svg/120px-Google_Maps_icon_%282020%29.svg.png" 
                              alt="Google Maps"
                              className="w-8 h-8 mb-2"
                            />
                            <span className="text-sm">Google Maps</span>
                          </button>
                          
                          <button
                            className="flex flex-col items-center justify-center p-3 bg-white rounded-lg hover:bg-gray-50 transition"
                            onClick={() => abrirMapa('waze')}
                          >
                            <img 
                              src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Waze_logo.svg/120px-Waze_logo.svg.png" 
                              alt="Waze"
                              className="w-8 h-8 mb-2"
                            />
                            <span className="text-sm">Waze</span>
                          </button>
                          
                          <button
                            className="flex flex-col items-center justify-center p-3 bg-white rounded-lg hover:bg-gray-50 transition"
                            onClick={() => abrirMapa('apple')}
                          >
                            <img 
                              src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Apple_Maps_logo.svg/120px-Apple_Maps_logo.svg.png" 
                              alt="Apple Maps"
                              className="w-8 h-8 mb-2"
                            />
                            <span className="text-sm">Apple Maps</span>
                          </button>
                          
                          <button
                            className="flex flex-col items-center justify-center p-3 bg-white rounded-lg hover:bg-gray-50 transition"
                            onClick={() => abrirMapa('osm')}
                          >
                            <img 
                              src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Openstreetmap_logo.svg/120px-Openstreetmap_logo.svg.png" 
                              alt="OpenStreetMap"
                              className="w-8 h-8 mb-2"
                            />
                            <span className="text-sm">OpenStreetMap</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Botões de ação - Removido "Alocar para Processamento" */}
            <div className="mt-6 flex justify-center">
              <button
                className="w-full md:w-1/2 border border-gray-200 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition"
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
