import { useState, useEffect } from "react";
import { Calendar, BarChart2, Info, Settings, DollarSign } from "lucide-react";

const EstimativaGanhos = () => {
  // Estados para configuração de valores
  const [valorConfig, setValorConfig] = useState({
    instalacao: 0,
    suporte: 0,
    trocaDrop: 0,
    deslocacao: 0
  });

  // Estado para intervalo de datas
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  
  // Estado para WOs processadas (simulado inicialmente)
  const [wosProcessadas, setWosProcessadas] = useState([]);
  
  // Estado para modal de detalhes
  const [modalAberto, setModalAberto] = useState(false);
  const [woSelecionada, setWoSelecionada] = useState(null);

  // Carregar configurações salvas e definir intervalo de datas padrão ao iniciar
  useEffect(() => {
    // Carregar configurações do localStorage
    const configSalva = localStorage.getItem('estimativaGanhosConfig');
    if (configSalva) {
      setValorConfig(JSON.parse(configSalva));
    }
    
    // Definir intervalo de datas padrão (mês atual)
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
    const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
    
    setDataInicio(primeiroDia.toISOString().split('T')[0]);
    setDataFim(ultimoDia.toISOString().split('T')[0]);
    
    // Carregar WOs simuladas para demonstração
    carregarWOsSimuladas();
  }, []);

  // Salvar configurações quando alteradas
  useEffect(() => {
    localStorage.setItem('estimativaGanhosConfig', JSON.stringify(valorConfig));
  }, [valorConfig]);

  // Função para carregar WOs simuladas (para demonstração)
  const carregarWOsSimuladas = () => {
    const tiposTrabalho = ["Instalação", "Suporte", "Troca de Drop", "Deslocação"];
    const wosSimuladas = Array.from({ length: 15 }, (_, i) => {
      const dataAleatoria = new Date();
      dataAleatoria.setDate(dataAleatoria.getDate() - Math.floor(Math.random() * 30));
      
      const tipoTrabalho = tiposTrabalho[Math.floor(Math.random() * tiposTrabalho.length)];
      
      return {
        id: `WO-${1000 + i}`,
        tipo: tipoTrabalho,
        data: dataAleatoria.toISOString().split('T')[0],
        cliente: `Cliente ${i + 1}`,
        endereco: `Rua Exemplo, ${i + 100}, Lisboa`,
        status: "Concluído",
        detalhes: `Detalhes da ordem de trabalho ${i + 1}. Este serviço foi realizado com sucesso.`
      };
    });
    
    setWosProcessadas(wosSimuladas);
  };

  // Função para calcular valor estimado com base no tipo
  const calcularValorEstimado = (tipo) => {
    switch(tipo) {
      case "Instalação":
        return valorConfig.instalacao;
      case "Suporte":
        return valorConfig.suporte;
      case "Troca de Drop":
        return valorConfig.trocaDrop;
      case "Deslocação":
        return valorConfig.deslocacao;
      default:
        return 0;
    }
  };

  // Função para filtrar WOs pelo intervalo de datas
  const wosNoIntervalo = wosProcessadas.filter(wo => {
    return wo.data >= dataInicio && wo.data <= dataFim;
  });

  // Calcular total geral
  const totalGeral = wosNoIntervalo.reduce((total, wo) => {
    return total + calcularValorEstimado(wo.tipo);
  }, 0);

  // Função para abrir modal com detalhes da WO
  const abrirDetalhes = (wo) => {
    setWoSelecionada(wo);
    setModalAberto(true);
  };

  // Função para formatar valor em euros
  const formatarMoeda = (valor) => {
    return new Intl.NumberFormat('pt-PT', {
      style: 'currency',
      currency: 'EUR'
    }).format(valor);
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4 flex items-center gap-2">
        <BarChart2 className="text-primary" />
        Estimativa de Ganhos
      </h1>
      
      {/* Seção de configuração de valores */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-medium text-[#333] mb-4 flex items-center gap-2">
          <Settings size={20} className="text-primary" />
          Configurar Valores por Tipo de Serviço
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-[#555] mb-1">Instalação (€)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorConfig.instalacao}
              onChange={(e) => setValorConfig({...valorConfig, instalacao: parseFloat(e.target.value) || 0})}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[#555] mb-1">Suporte (€)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorConfig.suporte}
              onChange={(e) => setValorConfig({...valorConfig, suporte: parseFloat(e.target.value) || 0})}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[#555] mb-1">Troca de Drop (€)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorConfig.trocaDrop}
              onChange={(e) => setValorConfig({...valorConfig, trocaDrop: parseFloat(e.target.value) || 0})}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[#555] mb-1">Deslocação (€)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorConfig.deslocacao}
              onChange={(e) => setValorConfig({...valorConfig, deslocacao: parseFloat(e.target.value) || 0})}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>
      
      {/* Seção de filtro por data */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-medium text-[#333] mb-4 flex items-center gap-2">
          <Calendar size={20} className="text-primary" />
          Intervalo de Datas
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-[#555] mb-1">Data Inicial</label>
            <input
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <div>
            <label className="block text-sm text-[#555] mb-1">Data Final</label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>
      
      {/* Resumo de ganhos */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-medium text-[#333] mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-primary" />
          Total Estimado
        </h2>
        
        <div className="text-3xl font-bold text-primary">
          {formatarMoeda(totalGeral)}
        </div>
        <div className="text-sm text-[#555] mt-1">
          Baseado em {wosNoIntervalo.length} ordens de trabalho no período selecionado
        </div>
      </div>
      
      {/* Lista de WOs */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-medium text-[#333] mb-4">
          Ordens de Trabalho Processadas
        </h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-secondary bg-opacity-30">
                <th className="p-3 text-left rounded-l-lg">ID</th>
                <th className="p-3 text-left">Tipo</th>
                <th className="p-3 text-left">Data</th>
                <th className="p-3 text-left">Cliente</th>
                <th className="p-3 text-right">Valor Estimado</th>
                <th className="p-3 text-center rounded-r-lg">Detalhes</th>
              </tr>
            </thead>
            <tbody>
              {wosNoIntervalo.length > 0 ? (
                wosNoIntervalo.map((wo, index) => (
                  <tr key={wo.id} className={index % 2 === 0 ? "bg-gray-50" : ""}>
                    <td className="p-3">{wo.id}</td>
                    <td className="p-3">{wo.tipo}</td>
                    <td className="p-3">{wo.data}</td>
                    <td className="p-3">{wo.cliente}</td>
                    <td className="p-3 text-right font-medium">
                      {formatarMoeda(calcularValorEstimado(wo.tipo))}
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => abrirDetalhes(wo)}
                        className="p-2 rounded-lg hover:bg-secondary hover:bg-opacity-30 transition"
                      >
                        <Info size={18} className="text-primary" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="p-4 text-center text-[#555]">
                    Nenhuma ordem de trabalho encontrada no período selecionado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Modal de detalhes */}
      {modalAberto && woSelecionada && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-[#333]">
                  Detalhes da Ordem de Trabalho
                </h3>
                <button
                  onClick={() => setModalAberto(false)}
                  className="p-2 rounded-full hover:bg-gray-100"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-[#555]">ID</p>
                  <p className="font-medium">{woSelecionada.id}</p>
                </div>
                <div>
                  <p className="text-sm text-[#555]">Tipo de Trabalho</p>
                  <p className="font-medium">{woSelecionada.tipo}</p>
                </div>
                <div>
                  <p className="text-sm text-[#555]">Data</p>
                  <p className="font-medium">{woSelecionada.data}</p>
                </div>
                <div>
                  <p className="text-sm text-[#555]">Cliente</p>
                  <p className="font-medium">{woSelecionada.cliente}</p>
                </div>
                <div>
                  <p className="text-sm text-[#555]">Endereço</p>
                  <p className="font-medium">{woSelecionada.endereco}</p>
                </div>
                <div>
                  <p className="text-sm text-[#555]">Status</p>
                  <p className="font-medium">{woSelecionada.status}</p>
                </div>
                <div className="md:col-span-2">
                  <p className="text-sm text-[#555]">Valor Estimado</p>
                  <p className="font-medium text-primary text-lg">
                    {formatarMoeda(calcularValorEstimado(woSelecionada.tipo))}
                  </p>
                </div>
                <div className="md:col-span-2">
                  <p className="text-sm text-[#555]">Detalhes</p>
                  <p>{woSelecionada.detalhes}</p>
                </div>
              </div>
            </div>
            
            <div className="p-6 border-t flex justify-end">
              <button
                onClick={() => setModalAberto(false)}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EstimativaGanhos;
