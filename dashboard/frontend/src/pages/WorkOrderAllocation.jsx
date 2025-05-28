import React, { useState, useEffect } from "react";
import { Search, MapPin, Share2, Clipboard, ArrowRight, X, Clock, Phone, Package, FileText, RefreshCw, History, ChevronRight } from "lucide-react";

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
  const [usuario, setUsuario] = useState(null);
  const [historicoWOs, setHistoricoWOs] = useState([]);
  const [copiedField, setCopiedField] = useState('');
  const [progress, setProgress] = useState(0);
  const [showCompletionEffect, setShowCompletionEffect] = useState(false);

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

  // Efeito para simular o progresso durante a busca
  useEffect(() => {
    let progressInterval;
    
    if (isSearching) {
      setProgress(0);
      
      // Simular progresso ao longo de 60 segundos
      progressInterval = setInterval(() => {
        setProgress(prevProgress => {
          // Aumentar o progresso de forma não linear para parecer mais natural
          const newProgress = prevProgress + (100 - prevProgress) / 60;
          return newProgress >= 99 ? 99 : newProgress;
        });
      }, 1000);
    } else if (progress > 0 && progress < 100) {
      // Quando a busca termina, completar o progresso e mostrar efeito
      setProgress(100);
      setTimeout(() => {
        setShowCompletionEffect(true);
        setTimeout(() => setShowCompletionEffect(false), 1000);
      }, 300);
    }
    
    return () => {
      if (progressInterval) clearInterval(progressInterval);
    };
  }, [isSearching, progress]);

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

  const abrirMapa = () => {
    if (!searchResult) return;
    
    const { lat, lng } = searchResult.coordenadas;
    // Usar a API de geolocalização do navegador para abrir o app de mapas padrão do dispositivo
    window.open(`geo:${lat},${lng}?q=${lat},${lng}`, '_system');
    
    // Fallback para navegadores desktop ou que não suportam o protocolo geo:
    if (!navigator.userAgent.match(/Android|iPhone|iPad|iPod/i)) {
      window.open(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`, '_blank');
    }
  };

  return (
    <div className="p-4 max-w-full">
      {/* Cabeçalho com título e ações */}
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="bg-purple-100 p-2 rounded-lg">
            <FileText size={20} className="text-primary" />
          </div>
          <h1 className="text-lg font-semibold text-text">Alocação de WO</h1>
        </div>
      </div>
      
      {/* Formulário de busca */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-4">
        <div className="flex flex-col gap-3">
          <div className="flex-1">
            <label htmlFor="wo-search" className="block text-sm font-medium text-muted mb-2">
              Número da Work Order
            </label>
            <div className="relative">
              <input
                id="wo-search"
                type="text"
                placeholder="Ex: 12345678"
                className="w-full bg-gray-50 border border-gray-200 rounded-lg py-3 pl-3 pr-10 text-text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              />
              {searchTerm && (
                <button 
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  onClick={() => setSearchTerm('')}
                >
                  <X size={16} />
                </button>
              )}
            </div>
          </div>
          <div>
            <button
              className="w-full bg-primary text-white py-3 rounded-lg font-medium hover:bg-primary-dark transition-colors flex items-center justify-center gap-2"
              onClick={handleSearch}
              disabled={isSearching}
            >
              {isSearching ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  <span>Buscando...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Buscar WO</span>
                </>
              )}
            </button>
            <p className="text-xs text-muted mt-1 text-center">Esse processo costuma levar 1 minuto</p>
          </div>
        </div>
        
        {/* Barra de progresso */}
        {isSearching && (
          <div className="mt-4">
            <div className="w-full bg-gray-100 rounded-full h-2 mb-1 overflow-hidden">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted">Buscando informações...</p>
              <p className="text-xs text-muted">{Math.round(progress)}%</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Histórico de WOs */}
      {historicoWOs.length > 0 && !searchResult && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden mb-4">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History size={18} className="text-primary" />
              <h2 className="text-base font-medium text-text">Histórico de WOs</h2>
            </div>
          </div>
          
          <div className="p-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {historicoWOs.slice(0, 6).map((wo) => (
                <div 
                  key={wo.numero}
                  className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors flex items-center justify-between"
                  onClick={() => carregarWOHistorico(wo.numero)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-primary">WO {wo.numero}</p>
                    <p className="text-sm text-muted truncate">{wo.morada}</p>
                    <p className="text-xs text-muted mt-1">
                      {new Date(wo.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-muted flex-shrink-0 ml-2" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Resultado da busca */}
      {searchResult && (
        <div className={`bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden relative ${showCompletionEffect ? 'animate-pulse' : ''}`}>
          {/* Efeito de conclusão */}
          {showCompletionEffect && (
            <div className="absolute inset-0 bg-purple-100 opacity-30 animate-ping rounded-lg"></div>
          )}
          
          {/* Cabeçalho */}
          <div className="bg-primary p-4 text-white flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">WO {searchResult.numero}</h2>
              <p className="text-sm opacity-90">{searchResult.observacoes}</p>
            </div>
            <div className="flex gap-2">
              <button
                className="p-2 rounded-full hover:bg-purple-700 transition-colors"
                onClick={handleShare}
                title="Compartilhar"
                aria-label="Compartilhar detalhes da WO"
              >
                <Share2 size={20} />
              </button>
              <button
                className="p-2 rounded-full hover:bg-purple-700 transition-colors"
                onClick={abrirMapa}
                title="Abrir no mapa"
                aria-label="Abrir localização no mapa"
              >
                <MapPin size={20} />
              </button>
            </div>
          </div>
          {/* Conteúdo */}
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Coluna 1 */}
              <div>
                {/* SLID */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-muted">SLID</label>
                    <button 
                      className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                      onClick={() => handleCopyToClipboard(searchResult.slid, 'slid')}
                    >
                      <Clipboard size={14} />
                      <span>{copiedField === 'slid' ? 'Copiado!' : 'Copiar'}</span>
                    </button>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 font-medium text-text">
                    {searchResult.slid}
                  </div>
                </div>
                {/* Acesso */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-muted">Acesso</label>
                    <button 
                      className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                      onClick={() => handleCopyToClipboard(searchResult.acesso, 'acesso')}
                    >
                      <Clipboard size={14} />
                      <span>{copiedField === 'acesso' ? 'Copiado!' : 'Copiar'}</span>
                    </button>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 font-medium text-text">
                    {searchResult.acesso}
                  </div>
                </div>
                
                {/* Morada */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-muted">Morada</label>
                    <button 
                      className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                      onClick={() => handleCopyToClipboard(searchResult.morada, 'morada')}
                    >
                      <Clipboard size={14} />
                      <span>{copiedField === 'morada' ? 'Copiado!' : 'Copiar'}</span>
                    </button>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-text">
                    {searchResult.morada}
                  </div>
                </div>
                
                {/* Fibra */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-muted">Fibra</label>
                    <button 
                      className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                      onClick={() => handleCopyToClipboard(searchResult.corFibra, 'fibra')}
                    >
                      <Clipboard size={14} />
                      <span>{copiedField === 'fibra' ? 'Copiado!' : 'Copiar'}</span>
                    </button>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 font-medium text-text flex items-center gap-2">
                    {determinarCorFibra(searchResult.corFibra) && (
                      <div 
                        className="w-4 h-4 rounded-full" 
                        style={{ backgroundColor: determinarCorFibra(searchResult.corFibra).hex }}
                      ></div>
                    )}
                    {searchResult.corFibra}
                  </div>
                </div>
                
                {/* Coluna 2 */}
                <div>
                  {/* Tipo de Box */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-muted">Tipo de Box</label>
                      <button 
                        className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                        onClick={() => handleCopyToClipboard(searchResult.tipoBox, 'tipoBox')}
                      >
                        <Clipboard size={14} />
                        <span>{copiedField === 'tipoBox' ? 'Copiado!' : 'Copiar'}</span>
                      </button>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-text">
                      {searchResult.tipoBox}
                    </div>
                  </div>
                  
                  {/* Número de Box */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-muted">Número de Box</label>
                      <button 
                        className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                        onClick={() => handleCopyToClipboard(searchResult.numBox, 'numBox')}
                      >
                        <Clipboard size={14} />
                        <span>{copiedField === 'numBox' ? 'Copiado!' : 'Copiar'}</span>
                      </button>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 font-medium text-text">
                      {searchResult.numBox}
                    </div>
                  </div>
                  
                  {/* Telefone */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-muted">Telefone</label>
                      <button 
                        className="text-primary hover:text-primary-dark text-sm flex items-center gap-1"
                        onClick={() => handleCopyToClipboard(searchResult.telefone, 'telefone')}
                      >
                        <Clipboard size={14} />
                        <span>{copiedField === 'telefone' ? 'Copiado!' : 'Copiar'}</span>
                      </button>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-text">
                      {searchResult.telefone}
                    </div>
                  </div>
                  
                  {/* Data e Horário */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-muted">Agendamento</label>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-text flex items-center gap-2">
                      <Clock size={16} className="text-primary" />
                      <span>{searchResult.dataAgendamento} - {searchResult.horario}</span>
                    </div>
                  </div>
                  </div>
                </div>
                
                {/* Morada */}
                <div className="mb-2">
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
                
                {/* Botão de mapa logo abaixo da morada */}
                <div className="mb-6">
                  <button
                    className="flex items-center gap-2 text-[#7C3AED] hover:underline mt-2"
                    onClick={abrirMapa}
                  >
                    <MapPin size={18} />
                    <span>Ver no mapa</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
                
                {/* Acesso */}
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Acesso</h3>
                  <p className="text-[#333] font-medium">{searchResult.acesso}</p>
                </div>
                
                {/* Nº de Box */}
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Nº de Box</h3>
                  <p className="text-[#333] font-medium">{searchResult.numBox}</p>
                </div>
              </div>
              
              {/* Coluna 2 */}
              <div>
                {/* Tipo de Box */}
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Tipo de Box</h3>
                  <p className="text-[#333] font-medium">{searchResult.tipoBox}</p>
                </div>
                
                {/* Instalar Telefone? */}
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Instalar Telefone?</h3>
                  <p className="text-[#333] font-medium">{searchResult.telefone}</p>
                </div>
                
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Data de Agendamento</h3>
                  <p className="text-[#333]">{searchResult.dataAgendamento}</p>
                </div>
                
                <div className="mb-4">
                  <h3 className="text-sm text-[#777] mb-1">Horário</h3>
                  <p className="text-[#333]">{searchResult.horario}</p>
                </div>
              </div>
            </div>
            
            {/* Botões de ação - Apenas Nova Busca */}
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
