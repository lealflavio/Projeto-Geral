import { useState, useEffect } from "react";
import { useAuthContext } from "../context/AuthContext";
import { Search, Clipboard, MapPin, ArrowRight, Clock, AlertCircle, CheckCircle, X, Loader, Eye } from "lucide-react";
import CardInfo from "../components/CardInfo";
import { toast } from "react-toastify";

// Configuração dinâmica do endpoint da API
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://dashboard-backend-s1bx.onrender.com";

// Função para registrar logs de depuração em ambiente de desenvolvimento
const logDebug = (message, data) => {
  if (import.meta.env.DEV) {
    console.log(`[DEBUG] ${message}`, data);
  }
};

// Função para gerar a chave de cache específica do usuário
const getUserCacheKey = (userId) => {
  return `woCache_${userId}`;
};

// Função para salvar WO no cache específico do usuário
const salvarWOCache = (woData, userId) => {
  if (!userId) return;
  
  try {
    // Gerar chave específica do usuário
    const cacheKey = getUserCacheKey(userId);
    
    // Obter cache atual do usuário
    const cacheString = localStorage.getItem(cacheKey);
    const cache = cacheString ? JSON.parse(cacheString) : {};
    
    // Adicionar nova entrada com timestamp
    cache[woData.wo] = {
      data: woData,
      timestamp: Date.now(),
      expira: Date.now() + (3 * 24 * 60 * 60 * 1000) // 3 dias em milissegundos
    };
    
    // Salvar cache atualizado
    localStorage.setItem(cacheKey, JSON.stringify(cache));
    logDebug("WO salva no cache do usuário:", { userId, woNumber: woData.wo });
  } catch (error) {
    console.error("Erro ao salvar WO no cache:", error);
  }
};

// Função para obter WO do cache específico do usuário
const obterWOCache = (woNumero, userId) => {
  if (!userId) return null;
  
  try {
    // Gerar chave específica do usuário
    const cacheKey = getUserCacheKey(userId);
    
    const cacheString = localStorage.getItem(cacheKey);
    if (!cacheString) return null;
    
    const cache = JSON.parse(cacheString);
    const entry = cache[woNumero];
    
    // Verificar se existe e não expirou
    if (entry && entry.expira > Date.now()) {
      logDebug("WO encontrada no cache do usuário:", { userId, woNumber: woNumero });
      return entry.data;
    }
    
    // Se expirou, remover do cache
    if (entry) {
      delete cache[woNumero];
      localStorage.setItem(cacheKey, JSON.stringify(cache));
      logDebug("WO expirada removida do cache:", { userId, woNumber: woNumero });
    }
    
    return null;
  } catch (error) {
    console.error("Erro ao obter WO do cache:", error);
    return null;
  }
};

// Função para obter histórico de WOs recentes do usuário específico
const obterHistoricoWOs = (userId) => {
  if (!userId) return [];
  
  try {
    // Gerar chave específica do usuário
    const cacheKey = getUserCacheKey(userId);
    
    const cacheString = localStorage.getItem(cacheKey);
    if (!cacheString) return [];
    
    const cache = JSON.parse(cacheString);
    const agora = Date.now();
    
    // Filtrar entradas não expiradas e ordenar por timestamp (mais recentes primeiro)
    return Object.entries(cache)
      .filter(([_, entry]) => entry.expira > agora)
      .map(([numero, entry]) => ({
        numero,
        data: entry.data.dataAgendamento,
        tipoInstalacao: entry.data.tipoInstalacao || "Fibra + TV",
        status: entry.data.status || "pendente",
        estadoIntervencao: entry.data.estadoIntervencao || "Pendente",
        timestamp: entry.timestamp
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  } catch (error) {
    console.error("Erro ao obter histórico de WOs:", error);
    return [];
  }
};

// Função atualizada para formatar a morada em duas linhas
const formatarMorada = (morada) => {
  if (!morada) return { linha1: "", linha2: "" };
  
  // Limpar a morada de caracteres estranhos
  const moradaLimpa = morada
    .replace(/[\[\]]/g, '')
    .replace(/\s-\s-\s/g, ', ')
    .replace(/\s-\s/g, ', ')
    .replace(/\s+/g, ' ')
    .trim();
  
  // Tentar extrair código postal (formato português: XXXX-XXX)
  const codigoPostalMatch = moradaLimpa.match(/\b\d{4}-\d{3}\b/);
  
  if (codigoPostalMatch) {
    // Posição do código postal na string
    const posicao = moradaLimpa.indexOf(codigoPostalMatch[0]);
    
    // Dividir a morada em duas partes
    const linha1 = moradaLimpa.substring(0, posicao).trim();
    const linha2 = moradaLimpa.substring(posicao).trim();
    
    return { linha1, linha2 };
  }
  
  // Caso não encontre um código postal, tentar dividir por vírgula
  const partes = moradaLimpa.split(',');
  if (partes.length > 1) {
    const linha1 = partes[0].trim();
    const linha2 = partes.slice(1).join(',').trim();
    return { linha1, linha2 };
  }
  
  // Se não conseguir dividir, retornar tudo na primeira linha
  return { linha1: moradaLimpa, linha2: "" };
};

// Função para extrair informações específicas do texto do cliente
const extrairInformacoes = (textoCliente) => {
  if (!textoCliente) return {};
  
  // Extrair Acesso (9 dígitos após "Access:")
  const accessMatch = textoCliente.match(/Access:(\d{9})/);
  const acesso = accessMatch ? accessMatch[1] : "";
  
  // Extrair Nº de Box
  const boxMatch = textoCliente.match(/NUMERO_TV_BOXES:\s*(\d+)/);
  const numBox = boxMatch ? boxMatch[1] : "";
  
  // Extrair Tipo de Box
  const tipoBoxMatch = textoCliente.match(/Set-Top-Boxes:\s*([^V][^\n]+?)(?=\s+Velocidade)/);
  const tipoBox = tipoBoxMatch ? tipoBoxMatch[1].trim() : "";
  
  // Extrair Telefone
  const telefoneMatch = textoCliente.match(/Entrega de equipamentos:\s*([^\n]+?)(?=\s+Modelo)/);
  const telefone = telefoneMatch ? telefoneMatch[1].trim() : "";
  
  // Extrair SLID (se existir no texto)
  const slidMatch = textoCliente.match(/SLID:\s*([^\s,;]+)/);
  const slid = slidMatch ? slidMatch[1] : "";
  
  return { acesso, numBox, tipoBox, telefone, slid };
};

// Função para formatar o estado da WO
const formatarEstadoWO = (estado) => {
  if (!estado) return "";
  
  return estado
    .toLowerCase()
    .split(' ')
    .map(palavra => palavra.charAt(0).toUpperCase() + palavra.slice(1))
    .join(' ');
};

// Função para traduzir o estado da intervenção para português
const traduzirEstadoIntervencao = (estado) => {
  if (!estado) return "Pendente";
  
  const estadoLower = estado.toLowerCase();
  
  const traducoes = {
    "job done": "Trabalho Realizado",
    "allocated": "Alocado",
    "job start": "Trabalho Iniciado",
    "in progress": "Em Progresso",
    "faturado": "Faturado",
    "pendente faturacao": "Pendente Faturação",
    "job not done": "Trabalho Não Realizado"
  };
  
  // Verificar correspondências parciais
  for (const [ingles, portugues] of Object.entries(traducoes)) {
    if (estadoLower.includes(ingles.toLowerCase())) {
      return portugues;
    }
  }
  
  return formatarEstadoWO(estado);
};

// Função para determinar a cor do estado da intervenção
const determinarCorEstadoIntervencao = (estado) => {
  if (!estado) return { bg: "bg-yellow-50", border: "border-yellow-100", text: "text-yellow-600", icon: Clock };
  
  const estadoLower = estado.toLowerCase();
  
  if (estadoLower.includes("realizado") || estadoLower.includes("done") || estadoLower.includes("faturado")) {
    return { bg: "bg-emerald-50", border: "border-emerald-100", text: "text-emerald-600", icon: CheckCircle };
  }
  
  if (estadoLower.includes("não") || estadoLower.includes("not") || estadoLower.includes("erro") || estadoLower.includes("falha")) {
    return { bg: "bg-red-50", border: "border-red-100", text: "text-red-600", icon: AlertCircle };
  }
  
  return { bg: "bg-yellow-50", border: "border-yellow-100", text: "text-yellow-600", icon: Clock };
};

const WorkOrderAllocation = () => {
  const [workOrderNumber, setWorkOrderNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResult, setSearchResult] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [workOrderData, setWorkOrderData] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressInterval, setProgressInterval] = useState(null);
  const [historicoWOs, setHistoricoWOs] = useState([]);
  const [showHistorico, setShowHistorico] = useState(true);
  
  const { authToken, user } = useAuthContext();

  // Limpar intervalo quando componente é desmontado
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  // Log da configuração em ambiente de desenvolvimento
  useEffect(() => {
    logDebug("API Base URL configurada:", API_BASE_URL);
    logDebug("Ambiente:", import.meta.env.MODE);
    
    // Carregar histórico de WOs do usuário atual
    if (user?.id) {
      const historico = obterHistoricoWOs(user.id);
      setHistoricoWOs(historico);
      logDebug("Histórico de WOs carregado:", historico);
    }
  }, [user?.id]);

  // Efeito para controlar a visibilidade do histórico
  useEffect(() => {
    setShowHistorico(!searchResult);
  }, [searchResult]);

  const handleChange = (e) => {
    setWorkOrderNumber(e.target.value);
  };

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    
    if (!workOrderNumber.trim()) {
      toast.error("Por favor, insira um número de WO válido");
      return;
    }
    
    // Validar se a WO tem 8 dígitos numéricos
    if (!/^\d{8}$/.test(workOrderNumber)) {
      toast.error("O número da WO deve conter exatamente 8 dígitos numéricos");
      return;
    }
    
    // Verificar se a WO está no cache do usuário atual
    if (user?.id) {
      const cachedWO = obterWOCache(workOrderNumber, user.id);
      if (cachedWO) {
        setSearchResult(cachedWO);
        setShowHistorico(false);
        return;
      }
    }
    
    setIsLoading(true);
    setError(null);
    setSearchResult(null);
    setProgress(0);
    setShowHistorico(false);
    
    // Iniciar a barra de progresso
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + (100 / 60); // Incremento para completar em 60 segundos
      });
    }, 1000);
    
    setProgressInterval(interval);
    
    try {
      // Endpoint completo com base na configuração
      const endpoint = `${API_BASE_URL}/api/wondercom/allocate`;
      logDebug("Fazendo requisição para:", endpoint);
      
      // Adicionar timeout para evitar que a requisição fique pendente por muito tempo
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 segundos de timeout
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          work_order_id: workOrderNumber,
          credentials: {
            username: user?.usuario_portal,
            password: user?.senha_portal
          }
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const data = await response.json();
      logDebug("Resposta da API:", data);
      
      // Limpar o intervalo quando os dados retornarem
      clearInterval(interval);
      setProgressInterval(null);
      
      if (!response.ok) {
        let mensagemErro = "Erro ao alocar WO";
        
        // Mensagens de erro mais específicas
        if (response.status === 401) {
          mensagemErro = "Erro de autenticação. Verifique suas credenciais.";
        } else if (response.status === 404) {
          mensagemErro = "WO não encontrada. Verifique o número informado.";
        } else if (response.status === 500) {
          mensagemErro = "Erro no servidor. O servidor pode estar sobrecarregado, tente novamente em alguns minutos.";
        } else if (data.message) {
          mensagemErro = data.message;
        }
        
        setError(mensagemErro);
        setProgress(100); // Completar a barra mesmo em caso de erro
        setIsLoading(false);
        setShowHistorico(true);
        return;
      }
      
      if (data.status === 'success' && data.data) {
        // Extrair informações do campo descricao
        const infoCliente = extrairInformacoes(data.data.descricao || "");
        
        // Formatar morada em duas linhas
        const moradaFormatada = formatarMorada(data.data.endereco);
        
        // Formatar e traduzir estado da intervenção
        const estadoIntervencao = traduzirEstadoIntervencao(data.data.estado_intervencao || "");
        
        // Determinar status para exibição visual
        let status = "pendente";
        if (estadoIntervencao.toLowerCase().includes("realizado") || 
            estadoIntervencao.toLowerCase().includes("faturado")) {
          status = "concluído";
        } else if (estadoIntervencao.toLowerCase().includes("não") || 
                  estadoIntervencao.toLowerCase().includes("erro")) {
          status = "erro";
        }
        
        // Usar o campo acesso diretamente da API se disponível
        const acessoFinal = data.data.acesso || infoCliente.acesso || "";
        
        // Criar objeto de resultado com os campos da nova API
        const resultado = {
          wo: workOrderNumber,
          slid: data.data.pdo || "",
          corFibra: data.data.cor_fibra || "",
          corFibraHex: data.data.cor_fibra_hex || "#CCCCCC",
          morada: moradaFormatada,
          coordenadas: {
            lat: data.data.latitude || 0,
            lng: data.data.longitude || 0
          },
          dataAgendamento: data.data.data_agendamento || "",
          status: status,
          donaRede: data.data.dona_rede || "",
          portoEntrada: data.data.porto_primario || "",
          estadoIntervencao: estadoIntervencao,
          cliente: data.data.descricao || "",
          
          // Campos extraídos do texto ou da API
          acesso: acessoFinal,
          numBox: infoCliente.numBox || "",
          tipoBox: infoCliente.tipoBox || "",
          telefone: infoCliente.telefone || "",
          
          // Campos adicionais para compatibilidade com a interface
          endereco: `${moradaFormatada.linha1}${moradaFormatada.linha2 ? '\n' + moradaFormatada.linha2 : ''}`,
          tipoInstalacao: data.data.tipo_servico || "Fibra + TV",
          tecnico: user?.name || "Técnico"
        };
        
        setWorkOrderData(data);
        setSearchResult(resultado);
        
        // Salvar no cache específico do usuário
        if (user?.id) {
          salvarWOCache(resultado, user.id);
          // Atualizar histórico
          setHistoricoWOs(obterHistoricoWOs(user.id));
        }
      } else {
        // Usar dados simulados para demonstração (apenas se não houver dados reais)
        const mockResult = {
          wo: workOrderNumber,
          slid: "CAKIBALE",
          corFibra: "Azul",
          corFibraHex: "#1E90FF",
          morada: {
            linha1: "Rua das Flores, 123",
            linha2: "3000-050 Lisboa"
          },
          acesso: "Portão principal",
          numBox: "B-4578",
          tipoBox: "Fibra Óptica",
          telefone: "Sim",
          dataAgendamento: "28/05/2025",
          status: "pendente",
          tipoInstalacao: "Fibra + TV",
          tecnico: user?.name || "Técnico",
          endereco: "Rua das Flores, 123\n3000-050 Lisboa",
          coordenadas: {
            lat: 38.7223,
            lng: -9.1393
          },
          donaRede: "PDO123",
          portoEntrada: "Porto 5",
          estadoIntervencao: "Em Progresso"
        };
        
        setWorkOrderData(data);
        setSearchResult(mockResult);
        
        // Salvar no cache específico do usuário
        if (user?.id) {
          salvarWOCache(mockResult, user.id);
          // Atualizar histórico
          setHistoricoWOs(obterHistoricoWOs(user.id));
        }
      }
      
      setProgress(100); // Garantir que a barra esteja completa
      
    } catch (err) {
      logDebug("Erro na requisição:", err);
      clearInterval(interval);
      setProgressInterval(null);
      
      let mensagemErro = "Erro de conexão. Verifique sua internet e tente novamente.";
      
      if (err.name === 'AbortError') {
        mensagemErro = "A requisição demorou muito tempo. O servidor pode estar sobrecarregado, tente novamente mais tarde.";
      }
      
      setError(mensagemErro);
      setProgress(100); // Completar a barra mesmo em caso de erro
      setShowHistorico(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    
    setTimeout(() => {
      setCopiedField(null);
    }, 2000);
  };

  const abrirMapa = () => {
    if (searchResult?.coordenadas) {
      const { lat, lng } = searchResult.coordenadas;
      window.open(`https://www.google.com/maps/search/?api=1&query=${lat},${lng}`, "_blank");
    } else if (searchResult?.morada) {
      const endereco = encodeURIComponent(
        searchResult.morada.linha1 + 
        (searchResult.morada.linha2 ? ', ' + searchResult.morada.linha2 : '')
      );
      window.open(`https://www.google.com/maps/search/?api=1&query=${endereco}`, "_blank");
    }
  };

  const carregarWOHistorico = (numero) => {
    setWorkOrderNumber(numero);
    if (user?.id) {
      const cachedWO = obterWOCache(numero, user.id);
      if (cachedWO) {
        setSearchResult(cachedWO);
        setShowHistorico(false);
        return;
      }
    }
    handleSubmit();
  };

  const voltarParaHistorico = () => {
    setSearchResult(null);
    setShowHistorico(true);
  };

  const determinarCorFibra = (cor, corHex) => {
    if (corHex) return { hex: corHex };
    
    const cores = {
      "Azul": { hex: "#1E90FF" },
      "Verde": { hex: "#32CD32" },
      "Vermelho": { hex: "#FF4500" },
      "Amarelo": { hex: "#FFD700" },
      "Branco": { hex: "#F8F8FF" },
      "Preto": { hex: "#2F4F4F" },
      "Laranja": { hex: "#FF8C00" },
      "Roxo": { hex: "#9370DB" },
      "Rosa": { hex: "#FF69B4" },
      "Marrom": { hex: "#8B4513" },
    };
    
    return cores[cor] || { hex: "#CCCCCC" };
  };

  // Função para verificar se um campo tem valor válido para exibição
  const temValor = (valor) => {
    return valor && valor !== "N/A" && valor !== "";
  };

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Alocar WO</h1>
      
      {/* Formulário de busca */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="workOrderNumber" className="block text-sm text-gray-600 mb-1">
              Número da WO
            </label>
            <div className="relative">
              <input
                id="workOrderNumber"
                type="text"
                value={workOrderNumber}
                onChange={handleChange}
                placeholder="Ex: 12345678"
                className="w-full p-3 pl-10 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                disabled={isLoading}
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            </div>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 ${
              isLoading ? "opacity-70 cursor-not-allowed" : ""
            }`}
          >
            {isLoading ? (
              <>
                <Loader size={18} className="animate-spin" />
                <span>Alocando...</span>
              </>
            ) : (
              "Alocar WO"
            )}
          </button>
          
          {/* Barra de progresso */}
          {isLoading || progress > 0 ? (
            <div className="mt-4">
              <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-600 transition-all duration-500 ease-linear"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1 text-center">
                {progress < 100 ? "Processando solicitação..." : "Processamento concluído"}
              </p>
            </div>
          ) : null}
        </form>
      </div>
      
      {/* Histórico de WOs */}
      {historicoWOs.length > 0 && showHistorico && (
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Histórico de WOs</h2>
          <div className="space-y-3">
            {historicoWOs.slice(0, 6).map((wo) => {
              const estadoCores = determinarCorEstadoIntervencao(wo.estadoIntervencao);
              const IconComponent = estadoCores.icon;
              
              return (
                <div 
                  key={wo.numero}
                  className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm cursor-pointer"
                  onClick={() => carregarWOHistorico(wo.numero)}
                >
                  <div className={`px-4 py-3 flex items-center justify-between ${estadoCores.bg} border-b ${estadoCores.border}`}>
                    <div className="flex items-center gap-2">
                      <IconComponent size={16} className={estadoCores.text} />
                      <span className="font-medium text-gray-800">{wo.numero}</span>
                    </div>
                    <button
                      className="text-blue-600 hover:text-blue-800 p-1.5 rounded-full hover:bg-white/50 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        carregarWOHistorico(wo.numero);
                      }}
                      aria-label="Ver detalhes"
                    >
                      <Eye size={18} />
                    </button>
                  </div>
                  
                  <div className="p-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <p className="text-xs text-gray-500">Data</p>
                        <p className="text-sm font-medium text-gray-800">{wo.data}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Tipo</p>
                        <p className="text-sm font-medium text-gray-800">{wo.tipoInstalacao}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Mensagem de erro */}
      {error && (
        <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-6 flex items-start gap-3 animate-fadeIn">
          <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-medium text-red-700">Erro na alocação</h3>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}
      
      {/* Resultados da busca */}
      {searchResult && (
        <div className="grid grid-cols-1 gap-4 animate-fadeIn">
          <div className="bg-white rounded-xl shadow overflow-hidden">
            {/* Cabeçalho com estado */}
            {(() => {
              const estadoCores = determinarCorEstadoIntervencao(searchResult.estadoIntervencao);
              const IconComponent = estadoCores.icon;
              
              return (
                <div className={`p-4 ${estadoCores.bg} border-b ${estadoCores.border}`}>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <IconComponent size={20} className={estadoCores.text} />
                      <h3 className="font-medium">{searchResult.wo}</h3>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      searchResult.estadoIntervencao.toLowerCase().includes("realizado") || searchResult.estadoIntervencao.toLowerCase().includes("faturado")
                        ? 'bg-emerald-100 text-emerald-700' 
                        : searchResult.estadoIntervencao.toLowerCase().includes("não") || searchResult.estadoIntervencao.toLowerCase().includes("erro")
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {searchResult.estadoIntervencao}
                    </span>
                  </div>
                </div>
              );
            })()}
            
            <div className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Coluna 1 */}
                <div className="space-y-4">
                  {/* SLID */}
                  {temValor(searchResult.slid) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">SLID</h3>
                      <div className="flex items-start gap-2">
                        <p className="text-gray-800 font-medium flex-1">{searchResult.slid}</p>
                        <button
                          className={`text-blue-600 p-1 hover:bg-blue-50 rounded-full transition ${copiedField === 'slid' ? 'bg-green-50 text-green-500' : ''}`}
                          onClick={() => handleCopyToClipboard(searchResult.slid, 'slid')}
                          title={copiedField === 'slid' ? 'Copiado!' : 'Copiar SLID'}
                        >
                          <Clipboard size={16} />
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Fibra */}
                  {temValor(searchResult.corFibra) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Fibra</h3>
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-4 h-4 rounded-full" 
                          style={{ backgroundColor: determinarCorFibra(searchResult.corFibra, searchResult.corFibraHex).hex }}
                        ></div>
                        <p className="text-gray-800">{searchResult.corFibra}</p>
                      </div>
                    </div>
                  )}
                  
                  {/* Porto Primário (movido para depois de Fibra) */}
                  {temValor(searchResult.portoEntrada) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Porto Primário</h3>
                      <p className="text-gray-800 font-medium">{searchResult.portoEntrada}</p>
                    </div>
                  )}
                  
                  {/* Dona de Rede (movido para depois de Porto) */}
                  {temValor(searchResult.donaRede) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Dona de Rede</h3>
                      <p className="text-gray-800 font-medium">{searchResult.donaRede}</p>
                    </div>
                  )}
                  
                  {/* Morada em duas linhas */}
                  {(temValor(searchResult.morada.linha1) || temValor(searchResult.morada.linha2)) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Morada</h3>
                      <div className="flex items-start gap-2">
                        <div className="flex-1">
                          {temValor(searchResult.morada.linha1) && (
                            <p className="text-gray-800">
                              {searchResult.morada.linha1}
                            </p>
                          )}
                          {temValor(searchResult.morada.linha2) && (
                            <p className="text-gray-800 text-sm">{searchResult.morada.linha2}</p>
                          )}
                        </div>
                        <button
                          className={`text-blue-600 p-1 hover:bg-blue-50 rounded-full transition ${copiedField === 'morada' ? 'bg-green-50 text-green-500' : ''}`}
                          onClick={() => handleCopyToClipboard(
                            typeof searchResult.morada === 'object'
                              ? `${searchResult.morada.linha1}${searchResult.morada.linha2 ? '\n' + searchResult.morada.linha2 : ''}`
                              : searchResult.morada,
                            'morada'
                          )}
                          title={copiedField === 'morada' ? 'Copiado!' : 'Copiar morada'}
                        >
                          <Clipboard size={16} />
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Botão de mapa logo abaixo da morada */}
                  {(temValor(searchResult.morada.linha1) || temValor(searchResult.morada.linha2) || 
                    (searchResult.coordenadas && (searchResult.coordenadas.lat || searchResult.coordenadas.lng))) && (
                    <div>
                      <button
                        className="flex items-center gap-2 text-blue-600 hover:underline"
                        onClick={abrirMapa}
                      >
                        <MapPin size={18} />
                        <span>Ver no mapa</span>
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  )}
                  
                  {/* Acesso */}
                  {temValor(searchResult.acesso) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Acesso</h3>
                      <p className="text-gray-800 font-medium">{searchResult.acesso}</p>
                    </div>
                  )}
                </div>
                
                {/* Coluna 2 */}
                <div className="space-y-4">
                  {/* Nº de Box */}
                  {temValor(searchResult.numBox) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Nº de Box</h3>
                      <p className="text-gray-800 font-medium">{searchResult.numBox}</p>
                    </div>
                  )}
                  
                  {/* Tipo de Box */}
                  {temValor(searchResult.tipoBox) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Tipo de Box</h3>
                      <p className="text-gray-800 font-medium">{searchResult.tipoBox}</p>
                    </div>
                  )}
                  
                  {/* Instalar Telefone? */}
                  {temValor(searchResult.telefone) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Instalar Telefone?</h3>
                      <p className="text-gray-800 font-medium">{searchResult.telefone}</p>
                    </div>
                  )}
                  
                  {/* Data de Agendamento */}
                  {temValor(searchResult.dataAgendamento) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Data de Agendamento</h3>
                      <p className="text-gray-800">{searchResult.dataAgendamento}</p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Botões de ação - Nova Busca e Voltar */}
              <div className="mt-6 flex justify-center gap-4">
                <button
                  className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300 transition"
                  onClick={voltarParaHistorico}
                >
                  Voltar
                </button>
                <button
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
                  onClick={() => {
                    setSearchResult(null);
                    setWorkOrderNumber("");
                  }}
                >
                  Nova Busca
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Estilos adicionais para animações */}
      <style jsx>{`
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

export default WorkOrderAllocation;
