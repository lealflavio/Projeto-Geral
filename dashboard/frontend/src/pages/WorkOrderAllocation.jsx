import React, { useState, useEffect } from "react";
import { Search, MapPin, Share2, Download, Clipboard, ArrowRight } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://SEU_BACKEND_URL"; // Ajuste conforme seu backend

const WorkOrderAllocation = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [usuario, setUsuario] = useState(null);

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
        setSearchResult({
          numero: searchTerm,
          cliente: data.data.descricao || "N/A",
          morada: data.data.endereco || "N/A",
          coordenadas: {
            lat: data.data.latitude || 0,
            lng: data.data.longitude || 0
          },
          corFibra: data.data.cor_fibra || "N/A",
          tipoServico: data.data.tipo_servico || "N/A",
          dataAgendamento: data.data.data_agendamento || "N/A",
          horario: data.data.horario || "N/A",
          observacoes: data.data.estado || data.data.observacoes || "",
        });
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

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => alert('Informação copiada para a área de transferência!'))
      .catch(err => console.error('Erro ao copiar: ', err));
  };

  const handleShare = () => {
    if (!searchResult) return;
    const shareText = `
      WO: ${searchResult.numero}
      Cliente: ${searchResult.cliente}
      Morada: ${searchResult.morada}
      Coordenadas: ${searchResult.coordenadas.lat}, ${searchResult.coordenadas.lng}
      Cor da Fibra: ${searchResult.corFibra}
      Data: ${searchResult.dataAgendamento}
      Horário: ${searchResult.horario}
    `;
    if (navigator.share) {
      navigator.share({
        title: `WO #${searchResult.numero}`,
        text: shareText,
      }).catch(err => console.error('Erro ao compartilhar: ', err));
    } else {
      handleCopyToClipboard(shareText);
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
              {/* Coluna 1 */}
              <div>
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Cliente</h3>
                  <p className="text-[#333] font-medium">{searchResult.cliente}</p>
                </div>
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Morada</h3>
                  <div className="flex items-start gap-2">
                    <p className="text-[#333] flex-1">{searchResult.morada}</p>
                    <button
                      className="text-[#7C3AED] p-1 hover:bg-purple-50 rounded-full transition"
                      onClick={() => handleCopyToClipboard(searchResult.morada)}
                      title="Copiar morada"
                    >
                      <Clipboard size={16} />
                    </button>
                  </div>
                </div>
                <div className="mb-6">
                  <h3 className="text-sm text-[#777] mb-1">Coordenadas</h3>
                  <div className="flex items-center gap-2">
                    <p className="text-[#333]">
                      {searchResult.coordenadas.lat}, {searchResult.coordenadas.lng}
                    </p>
                    <button
                      className="text-[#7C3AED] p-1 hover:bg-purple-50 rounded-full transition"
                      onClick={() => handleCopyToClipboard(`${searchResult.coordenadas.lat}, ${searchResult.coordenadas.lng}`)}
                      title="Copiar coordenadas"
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
                  <h3 className="text-sm text-[#777] mb-1">Observações</h3>
                  <p className="text-[#333] p-3 bg-gray-50 rounded-lg text-sm">
                    {searchResult.observacoes}
                  </p>
                </div>
              </div>
            </div>
            {/* Mapa */}
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
                      Mapa interativo seria exibido aqui com as coordenadas:<br />
                      <span className="font-medium">{searchResult.coordenadas.lat}, {searchResult.coordenadas.lng}</span>
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
