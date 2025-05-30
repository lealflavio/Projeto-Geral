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

// Função para determinar a cor da fibra com base no texto e regras específicas
const determinarCorFibra = (corTexto, corHex) => {
  // Valores padrão
  let resultado = {
    nome: corTexto || "Cinza",
    hex: corHex || "#CCCCCC",
    confianca: "baixa"
  };
  
  // Mapeamento de cores em inglês para português
  const traducaoCores = {
    "blue": "Azul",
    "red": "Vermelho",
    "green": "Verde",
    "yellow": "Amarelo",
    "white": "Branco",
    "black": "Preto",
    "brown": "Marrom",
    "orange": "Laranja",
    "purple": "Roxo",
    "pink": "Rosa",
    "gray": "Cinza",
    "grey": "Cinza"
  };
  
  // Mapeamento de cores para códigos hexadecimais
  const coresHex = {
    "azul": "#1E90FF",
    "vermelho": "#FF4136",
    "verde": "#2ECC40",
    "amarelo": "#FFDC00",
    "branco": "#FFFFFF",
    "preto": "#111111",
    "marrom": "#A52A2A",
    "laranja": "#FF851B",
    "roxo": "#B10DC9",
    "rosa": "#FF80CC",
    "cinza": "#AAAAAA"
  };
  
  // Se já temos um valor hexadecimal, usá-lo
  if (corHex && corHex.startsWith('#')) {
    resultado.hex = corHex;
  }
  
  // Processar texto da cor
  if (corTexto) {
    // Converter para minúsculas para facilitar comparação
    const textoLower = corTexto.toLowerCase();
    
    // Verificar se é uma cor em inglês e traduzir
    for (const [ingles, portugues] of Object.entries(traducaoCores)) {
      if (textoLower.includes(ingles.toLowerCase())) {
        resultado.nome = portugues;
        resultado.hex = coresHex[portugues.toLowerCase()] || resultado.hex;
        resultado.confianca = "média";
        break;
      }
    }
    
    // Verificar se já é uma cor em português
    for (const [portugues, hex] of Object.entries(coresHex)) {
      if (textoLower.includes(portugues)) {
        resultado.nome = portugues.charAt(0).toUpperCase() + portugues.slice(1);
        resultado.hex = hex;
        resultado.confianca = "alta";
        break;
      }
    }
  }
  
  return resultado;
};

// Função para determinar a cor da fibra com base na dona de rede e porto primário
const determinarCorFibraPorRegras = (donaRede, portoEntrada, fibra) => {
  // Valores padrão
  let resultado = {
    nome: "Cinza",
    hex: "#CCCCCC",
    confianca: "baixa",
    mensagem: ""
  };
  
  // Regras para NOS
  if (donaRede && donaRede.toUpperCase() === "NOS" && portoEntrada) {
    // Mapeamento de portos para cores na NOS
    const mapaPortosCores = {
      "1": { nome: "Azul", hex: "#1E90FF" },
      "2": { nome: "Laranja", hex: "#FF851B" },
      "3": { nome: "Verde", hex: "#2ECC40" },
      "4": { nome: "Marrom", hex: "#A52A2A" },
      "5": { nome: "Cinza", hex: "#AAAAAA" },
      "6": { nome: "Branco", hex: "#FFFFFF" },
      "7": { nome: "Vermelho", hex: "#FF4136" },
      "8": { nome: "Preto", hex: "#111111" }
    };
    
    // Extrair número do porto
    const numeroPorto = portoEntrada.replace(/\D/g, '');
    
    if (numeroPorto && mapaPortosCores[numeroPorto]) {
      resultado = {
        ...mapaPortosCores[numeroPorto],
        confianca: "alta",
        mensagem: "A cor mostrada é provavelmente a correta, mas o ideal será confirmar com o suporte de construção de rede."
      };
    } else {
      resultado.mensagem = "Não foi possível determinar a cor com base no porto. Consulte o suporte de construção de rede.";
    }
  }
  // Regras para VDF
  else if (donaRede && donaRede.toUpperCase() === "VDF" && fibra) {
    // Para VDF, as duas últimas palavras do campo fibra indicam a cor do tubo e da fibra
    const palavras = fibra.split(/\s+/);
    if (palavras.length >= 2) {
      const corTubo = palavras[palavras.length - 2];
      const corFibra = palavras[palavras.length - 1];
      
      // Determinar cor com base nas palavras extraídas
      const corTuboInfo = determinarCorFibra(corTubo);
      const corFibraInfo = determinarCorFibra(corFibra);
      
      resultado = {
        nome: `${corTuboInfo.nome} / ${corFibraInfo.nome}`,
        hex: corFibraInfo.hex, // Usamos a cor da fibra como principal
        confianca: "média",
        mensagem: "Cores extraídas do campo Fibra. Tubo: " + corTuboInfo.nome + ", Fibra: " + corFibraInfo.nome
      };
    }
  }
  
  return resultado;
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
  const [inputError, setInputError] = useState(false);
  const [tentativas, setTentativas] = useState(0);
  
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

  // Validação em tempo real do formato da WO
  const handleChange = (e) => {
    // Remover espaços antes e depois
    const valorLimpo = e.target.value.trim();
    
    // Permitir apenas dígitos
    const apenasDigitos = valorLimpo.replace(/\D/g, '');
    
    // Limitar a 8 dígitos
    const valorFinal = apenasDigitos.slice(0, 8);
    
    setWorkOrderNumber(valorFinal);
    
    // Validar formato e mostrar feedback visual
    setInputError(valorFinal.length > 0 && valorFinal.length !== 8);
  };

  // Função para lidar com colagem (paste) no campo
  const handlePaste = (e) => {
    // Prevenir o comportamento padrão
    e.preventDefault();
    
    // Obter o texto colado
    const textoColado = e.clipboardData.getData('text');
    
    // Limpar o texto (remover espaços e caracteres não numéricos)
    const textoLimpo = textoColado.trim().replace(/\D/g, '').slice(0, 8);
    
    // Atualizar o estado
    setWorkOrderNumber(textoLimpo);
    
    // Validar formato e mostrar feedback visual
    setInputError(textoLimpo.length > 0 && textoLimpo.length !== 8);
  };

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
        if (!workOrderNumber.trim()) {
      toast.warning("Por favor, insira um número de WO para pesquisar");
      setError("Por favor, insira um número de WO para pesquisar");
      return;
    }
    
    // Validar se a WO tem 8 dígitos numéricos
    if (!validarFormatoWO(workOrderNumber)) {
      toast.warning("O número da WO deve conter exatamente 8 dígitos numéricos");
      setError("O número da WO deve conter exatamente 8 dígitos numéricos");
      return;
    }
    
    // Verificar se o usuário está autenticado
    if (!authToken || !user) {
      toast.error("Sessão expirada. Por favor, faça login novamente");
      setError("Sessão expirada. Por favor, faça login novamente");
      return;
    }}
    
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
    
    // Incrementar contador de tentativas para esta WO
    setTentativas(prev => prev + 1);
    const tentativaAtual = tentativas + 1;
    
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
      logDebug("Token de autenticação:", authToken ? "Presente" : "Ausente");
      logDebug("Credenciais do usuário:", {
        username: user?.usuario_portal ? "Presente" : "Ausente",
        password: user?.senha_portal ? "Presente" : "Ausente"
      });
      
      // Adicionar timeout para evitar que a requisição fique pendente por muito tempo
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000); // 45 segundos de timeout
      
      // Garantir que o token seja enviado com o prefixo Bearer
      const tokenFormatado = authToken.startsWith('Bearer ') ? authToken : `Bearer ${authToken}`;
      
      // Adicionar cabeçalhos CORS
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": tokenFormatado,
          "Accept": "application/json",
          "Origin": window.location.origin,
        },
        body: JSON.stringify({
          work_order_id: workOrderNumber,
          credentials: {
            username: user?.usuario_portal || "",
            password: user?.senha_portal || ""
          }
        }),
        signal: controller.signal,
        mode: "cors", // Garantir que a requisição use CORS
        credentials: "include" // Incluir cookies na requisição
      });
      
      clearTimeout(timeoutId);
      
      // Tentar obter o corpo da resposta como JSON
      let data;
      try {
        data = await response.json();
        logDebug("Resposta da API:", data);
      } catch (jsonError) {
        logDebug("Erro ao parsear resposta como JSON:", jsonError);
        data = { status: 'error', message: 'Erro ao processar resposta do servidor' };
      }
      
      // Limpar o intervalo quando os dados retornarem
      clearInterval(interval);
      setProgressInterval(null);
      
      if (!response.ok) {
        let mensagemErro = "Erro ao alocar WO";
        
        // Verificar se a mensagem de erro contém indicação de WO não encontrada
        if (response.status === 404 || 
            (data && isWoNaoEncontradaError(data.message)) || 
            (data && data.error && isWoNaoEncontradaError(data.error))) {
          mensagemErro = `WO ${workOrderNumber} não encontrada. Verifique o número informado.`;
          toast.warning(mensagemErro);
        }
        // Mensagens de erro mais específicas
        else if (response.status === 401) {
          mensagemErro = "Sessão expirada. Por favor, faça login novamente.";
          toast.error(mensagemErro);
        } else if (response.status === 500) {
          // Verificar se o erro 500 contém mensagem sobre WO não encontrada
          if (data && data.message && isWoNaoEncontradaError(data.message)) {
            mensagemErro = `WO ${workOrderNumber} não encontrada. Verifique o número informado.`;
            toast.warning(mensagemErro);
          } else {
            mensagemErro = "Erro no servidor. Tente novamente em alguns minutos.";
            toast.error(mensagemErro);
          }
        } else if (data && data.message) {
          mensagemErro = data.message;
          toast.error(mensagemErro);
        }
        
        setError(mensagemErro);
        setProgress(100); // Completar a barra mesmo em caso de erro
        setIsLoading(false);
        return;
      }
      
      if (data && data.status === 'success' && data.data) {
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
        
        // Limpar qualquer erro anterior e mostrar mensagem de sucesso
        setError(null);
        toast.success(`WO ${workOrderNumber} alocada com sucesso!`);
        
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
          acesso: "188067988",
          numBox: "1",
          tipoBox: "Smart",
          telefone: "Sim",
          dataAgendamento: "28/05/2025",
          status: "Alocado",
          tipoInstalacao: "Instalacao FTTH",
          tecnico: user?.name || "Técnico",
          endereco: "Rua das Flores, 123\n3000-050 Lisboa",
          coordenadas: {
            lat: 38.7223,
            lng: -9.1393
          },
          donaRede: "NOS",
          portoEntrada: "Porto 5",
          estadoIntervencao: "Em Progresso"
        };
        
        setWorkOrderData(data);
        setSearchResult(mockResult);
        
        // Resetar contador de tentativas após sucesso
        setTentativas(0);
      } 
      
      // Se a resposta for success mas não tiver dados, tratar como WO não encontrada
      if (!data || Object.keys(data).length === 0) {
        setError(`WO ${workOrderNumber} não encontrada ou sem dados disponíveis.`);
      }
      
      setProgress(100); // Garantir que a barra esteja completa
      
    } catch (err) {
      logDebug("Erro na requisição:", err);
      clearInterval(interval);
      setProgressInterval(null);
      
      let mensagemErro = "Erro de conexão. Verifique sua internet e tente novamente.";
      
      // Verificar se é um erro de CORS
      if (err.message && err.message.includes('CORS')) {
        mensagemErro = "Erro de permissão de acesso entre domínios (CORS). Por favor, contate o suporte técnico.";
        toast.error(mensagemErro);
      } 
      // Verificar se é um erro de timeout
      else if (err.name === 'AbortError') {
        // Se já tentou mais de 2 vezes e continua dando timeout, sugerir que a WO não existe
        if (tentativaAtual > 2) {
          mensagemErro = `WO ${workOrderNumber} não encontrada ou o servidor está demorando muito para responder. Verifique o número informado.`;
          toast.warning(mensagemErro);
        } else {
          mensagemErro = "A requisição demorou muito tempo. Tente novamente em alguns instantes.";
          toast.warning(mensagemErro);
        }
      } else {
        toast.error(mensagemErro);
      }
      
      setError(mensagemErro);
      setProgress(100); // Completar a barra mesmo em caso de erro
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
                onPaste={handlePaste}
                placeholder="Ex: 12345678"
                className={`w-full p-3 pl-10 border rounded-xl text-sm focus:outline-none focus:ring-2 ${
                  inputError 
                    ? "border-red-300 focus:ring-red-500 bg-red-50" 
                    : "focus:ring-blue-600"
                }`}
                disabled={isLoading}
                maxLength={8}
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            </div>
            {inputError && (
              <p className="text-red-500 text-xs mt-1">
                O número da WO deve conter exatamente 8 dígitos numéricos
              </p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isLoading || inputError}
            className={`w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 ${
              (isLoading || inputError) ? "opacity-70 cursor-not-allowed" : ""
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
      
      {/* Mensagem de erro - Reposicionada para ficar logo abaixo do formulário */}
      {error && (
        <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-6 flex items-start gap-3 animate-fadeIn">
          <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-medium text-red-700">Erro na alocação</h3>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}
      
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
                  
                  {/* Fibra - sem círculo de cor */}
                  {temValor(searchResult.corFibra) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Fibra</h3>
                      <p className="text-gray-800">{searchResult.corFibra}</p>
                    </div>
                  )}
                  
                  {/* Porto Primário com indicação de cor da fibra */}
                  {temValor(searchResult.portoEntrada) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Porto Primário</h3>
                      <div className="flex items-center gap-2">
                        <p className="text-gray-800 font-medium">{searchResult.portoEntrada}</p>
                        
                        {/* Indicador de cor da fibra baseado nas regras */}
                        {(() => {
                          const corInfo = determinarCorFibraPorRegras(
                            searchResult.donaRede, 
                            searchResult.portoEntrada,
                            searchResult.corFibra
                          );
                          
                          return (
                            <div className="flex items-center gap-2 ml-2">
                              <div 
                                className="w-4 h-4 rounded-full border border-gray-200" 
                                style={{ backgroundColor: corInfo.hex }}
                                title={corInfo.nome}
                              ></div>
                              <span className="text-sm text-gray-700">{corInfo.nome}</span>
                              
                              {/* Ícone de informação com tooltip */}
                              {corInfo.mensagem && (
                                <div className="relative group">
                                  <AlertCircle size={16} className="text-amber-500 cursor-help" />
                                  <div className="absolute z-10 invisible group-hover:visible bg-white border border-gray-200 p-2 rounded-md shadow-md w-64 text-xs text-gray-700 top-full left-0 mt-1">
                                    {corInfo.mensagem}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                  
                  {/* Dona de Rede (movido para depois de Porto) */}
                  {temValor(searchResult.donaRede) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Dona de Rede</h3>
                      <p className="text-gray-800 font-medium">{searchResult.donaRede}</p>
                    </div>
                  )}
                  
                  {/* Morada em duas linhas - simplificada quando anonimizada */}
                  {(temValor(searchResult.morada.linha1) || temValor(searchResult.morada.linha2)) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Morada</h3>
                      <div className="flex items-start gap-2">
                        <div className="flex-1">
                          {/* Verificar se contém "Anonimizado" e simplificar */}
                          {temValor(searchResult.morada.linha1) && searchResult.morada.linha1.includes("Anonimizado") ? (
                            <p className="text-gray-800">Anonimizado</p>
                          ) : temValor(searchResult.morada.linha1) && (
                            <p className="text-gray-800">
                              {searchResult.morada.linha1}
                            </p>
                          )}
                          {temValor(searchResult.morada.linha2) && !searchResult.morada.linha1.includes("Anonimizado") && (
                            <p className="text-gray-800 text-sm">{searchResult.morada.linha2}</p>
                          )}
                        </div>
                        <button
                          className={`text-blue-600 p-1 hover:bg-blue-50 rounded-full transition ${copiedField === 'morada' ? 'bg-green-50 text-green-500' : ''}`}
                          onClick={() => handleCopyToClipboard(searchResult.endereco, 'morada')}
                          title={copiedField === 'morada' ? 'Copiado!' : 'Copiar Morada'}
                        >
                          <Clipboard size={16} />
                        </button>
                      </div>
                    </div>
                  )}         )}
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
                  
                  {/* Entregar Telefone - apenas Sim ou Não */}
                  {temValor(searchResult.telefone) && (searchResult.telefone.toLowerCase() === "sim" || searchResult.telefone.toLowerCase() === "não" || searchResult.telefone.toLowerCase() === "nao") && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Entregar Telefone?</h3>
                      <p className="text-gray-800 font-medium">
                        {searchResult.telefone.toLowerCase() === "sim" ? "Sim" : "Não"}
                      </p>
                    </div>
                  )}}
                              {/* Data de Agendamento - sem segundos */}
                  {temValor(searchResult.dataAgendamento) && (
                    <div>
                      <h3 className="text-xs text-gray-500 mb-1">Data de Agendamento</h3>
                      <p className="text-gray-800 font-medium">
                        {(() => {
                          // Formatar data para remover segundos
                          const dataCompleta = searchResult.dataAgendamento;
                          if (dataCompleta.includes(':')) {
                            // Se tem formato com hora (HH:MM:SS)
                            const partes = dataCompleta.split(' ');
                            if (partes.length >= 2) {
                              const data = partes[0];
                              const horaCompleta = partes[1];
                              // Extrair apenas hora e minuto (HH:MM)
                              const horaSemSegundos = horaCompleta.split(':').slice(0, 2).join(':');
                              return `${data} ${horaSemSegundos}`;
                            }
                          }
                          return dataCompleta; // Retorna original se não conseguir formatar
                        })()}
                      </p>
                    </div>
                  )}            </div>
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
                    setInputError(false);
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
