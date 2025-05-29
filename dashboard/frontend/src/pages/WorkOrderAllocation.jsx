import { useState, useEffect } from "react";
import { useAuthContext } from "../context/AuthContext";
import { Search, Clipboard, MapPin, ArrowRight, Clock, AlertCircle, CheckCircle, X, Loader } from "lucide-react";
import CardInfo from "../components/CardInfo";
import { toast } from "react-toastify";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://zincoapp.pt"; // Adicionado o domínio base

const WorkOrderAllocation = () => {
  const [workOrderNumber, setWorkOrderNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResult, setSearchResult] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [workOrderData, setWorkOrderData] = useState(null);
  const [progress, setProgress] = useState(0);
  const [progressInterval, setProgressInterval] = useState(null);
  
  const { authToken, user } = useAuthContext();

  // Limpar intervalo quando componente é desmontado
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  const handleChange = (e) => {
    setWorkOrderNumber(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!workOrderNumber.trim()) {
      toast.error("Por favor, insira um número de WO válido");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setSearchResult(null);
    setProgress(0);
    
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
      // Corrigido o endpoint para incluir o domínio base
      const response = await fetch(`${API_BASE_URL}/api/wondercom/allocate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        // Corrigida a estrutura do corpo da requisição para corresponder ao esperado pela API
        body: JSON.stringify({
          work_order_id: workOrderNumber,
          credentials: {
            username: user?.usuario_portal,
            password: user?.senha_portal
          }
        }),
      });
      
      const data = await response.json();
      
      // Limpar o intervalo quando os dados retornarem
      clearInterval(interval);
      setProgressInterval(null);
      
      if (!response.ok) {
        setError(data.message || "Erro ao alocar WO");
        setProgress(100); // Completar a barra mesmo em caso de erro
        setIsLoading(false);
        return;
      }
      
      // Simular dados para demonstração
      const mockResult = {
        wo: workOrderNumber,
        slid: "CAKIBALE",
        corFibra: "Azul",
        morada: "Rua das Flores, 123, Lisboa",
        acesso: "Portão principal",
        numBox: "B-4578",
        tipoBox: "Fibra Óptica",
        telefone: "Sim",
        dataAgendamento: "28/05/2025",
        horario: "14:00 - 16:00",
        status: "pendente",
        tipoInstalacao: "Fibra + TV",
        tecnico: user?.name || "Técnico",
        endereco: "Rua das Flores, 123, Lisboa",
        coordenadas: "38.7223° N, 9.1393° W",
        observacoes: "Cliente solicitou instalação rápida. Levar equipamento extra.",
        materiais: ["Cabo de fibra 10m", "Roteador Wi-Fi", "Splitter óptico"]
      };
      
      setWorkOrderData(data);
      setSearchResult(mockResult);
      setProgress(100); // Garantir que a barra esteja completa
      
    } catch (err) {
      clearInterval(interval);
      setProgressInterval(null);
      setError("Erro de conexão. Tente novamente.");
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
    if (searchResult?.morada) {
      const endereco = encodeURIComponent(searchResult.morada);
      window.open(`https://www.google.com/maps/search/?api=1&query=${endereco}`, "_blank");
    }
  };

  const determinarCorFibra = (cor) => {
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
    
    return cores[cor] || null;
  };

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Alocar WO</h1>
      
      {/* Formulário de busca */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="workOrderNumber" className="block text-sm text-[#555] mb-1">
              Número da WO
            </label>
            <div className="relative">
              <input
                id="workOrderNumber"
                type="text"
                value={workOrderNumber}
                onChange={handleChange}
                placeholder="Ex: 12345678"
                className="w-full p-3 pl-10 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
                disabled={isLoading}
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#999]" size={18} />
            </div>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className={`w-full bg-[#7C3AED] text-white py-3 rounded-xl font-semibold hover:bg-[#6B21A8] transition flex items-center justify-center gap-2 ${
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
                  className="h-full bg-[#7C3AED] transition-all duration-500 ease-linear"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-[#777] mt-1 text-center">
                {progress < 100 ? "Processando solicitação..." : "Processamento concluído"}
              </p>
            </div>
          ) : null}
        </form>
      </div>
      
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
            <div className={`p-4 ${
              searchResult.status === 'concluído' 
                ? 'bg-emerald-50 border-b border-emerald-100' 
                : searchResult.status === 'erro'
                  ? 'bg-red-50 border-b border-red-100'
                  : 'bg-yellow-50 border-b border-yellow-100'
            }`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {searchResult.status === 'concluído' ? (
                    <CheckCircle size={20} className="text-emerald-500" />
                  ) : searchResult.status === 'erro' ? (
                    <AlertCircle size={20} className="text-red-500" />
                  ) : (
                    <Clock size={20} className="text-yellow-500" />
                  )}
                  <h3 className="font-medium">WO #{searchResult.wo}</h3>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  searchResult.status === 'concluído' 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : searchResult.status === 'erro'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {searchResult.status === 'concluído' 
                    ? 'Concluído' 
                    : searchResult.status === 'erro'
                      ? 'Erro'
                      : 'Pendente'}
                </span>
              </div>
            </div>
            
            <div className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Coluna 1 */}
                <div>
                  {/* SLID */}
                  <div className="mb-6">
                    <h3 className="text-xs text-muted mb-1">SLID</h3>
                    <div className="flex items-start gap-2">
                      <p className="text-text font-medium flex-1">{searchResult.slid || "CAKIBALE"}</p>
                      <button
                        className={`text-primary p-1 hover:bg-purple-50 rounded-full transition ${copiedField === 'slid' ? 'bg-green-50 text-green-500' : ''}`}
                        onClick={() => handleCopyToClipboard(searchResult.slid || "CAKIBALE", 'slid')}
                        title={copiedField === 'slid' ? 'Copiado!' : 'Copiar SLID'}
                      >
                        <Clipboard size={16} />
                      </button>
                    </div>
                  </div>
                  
                  {/* Fibra */}
                  <div className="mb-6">
                    <h3 className="text-xs text-muted mb-1">Fibra</h3>
                    <div className="flex items-center gap-2">
                      {determinarCorFibra(searchResult.corFibra) && (
                        <div 
                          className="w-4 h-4 rounded-full" 
                          style={{ backgroundColor: determinarCorFibra(searchResult.corFibra).hex }}
                        ></div>
                      )}
                      <p className="text-text">{searchResult.corFibra}</p>
                    </div>
                  </div>
                  
                  {/* Morada */}
                  <div className="mb-2">
                    <h3 className="text-xs text-muted mb-1">Morada</h3>
                    <div className="flex items-start gap-2">
                      <p className="text-text flex-1">{searchResult.morada}</p>
                      <button
                        className={`text-primary p-1 hover:bg-purple-50 rounded-full transition ${copiedField === 'morada' ? 'bg-green-50 text-green-500' : ''}`}
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
                      className="flex items-center gap-2 text-primary hover:underline mt-2"
                      onClick={abrirMapa}
                    >
                      <MapPin size={18} />
                      <span>Ver no mapa</span>
                      <ArrowRight size={16} />
                    </button>
                  </div>
                  
                  {/* Acesso */}
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Acesso</h3>
                    <p className="text-text font-medium">{searchResult.acesso}</p>
                  </div>
                  
                  {/* Nº de Box */}
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Nº de Box</h3>
                    <p className="text-text font-medium">{searchResult.numBox}</p>
                  </div>
                </div>
                
                {/* Coluna 2 */}
                <div>
                  {/* Tipo de Box */}
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Tipo de Box</h3>
                    <p className="text-text font-medium">{searchResult.tipoBox}</p>
                  </div>
                  
                  {/* Instalar Telefone? */}
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Instalar Telefone?</h3>
                    <p className="text-text font-medium">{searchResult.telefone}</p>
                  </div>
                  
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Data de Agendamento</h3>
                    <p className="text-text">{searchResult.dataAgendamento}</p>
                  </div>
                  
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Horário</h3>
                    <p className="text-text">{searchResult.horario}</p>
                  </div>
                  
                  {/* Observações */}
                  <div className="mb-4">
                    <h3 className="text-xs text-muted mb-1">Observações</h3>
                    <p className="text-text text-sm">{searchResult.observacoes}</p>
                  </div>
                  
                  {/* Materiais */}
                  {searchResult.materiais && searchResult.materiais.length > 0 && (
                    <div className="mb-4">
                      <h3 className="text-xs text-muted mb-1">Materiais Necessários</h3>
                      <ul className="space-y-1">
                        {searchResult.materiais.map((material, index) => (
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
              
              {/* Botões de ação - Apenas Nova Busca */}
              <div className="mt-6 flex justify-center">
                <button
                  className="w-full md:w-1/2 bg-primary text-white py-2 rounded-lg hover:bg-primary-dark transition"
                  onClick={() => setSearchResult(null)}
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
