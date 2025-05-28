import React, { useState, useEffect } from "react";
import { useQuery, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { motion } from "framer-motion";
import { 
  Search, 
  MapPin, 
  Info, 
  Calendar, 
  Home, 
  Navigation, 
  Download, 
  BarChart2, 
  FileText, 
  RefreshCw, 
  Calculator,
  ChevronDown
} from "lucide-react";
import '../styles/variables.css';

// Corrigindo o problema dos ícones do Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

// Ícones personalizados para o mapa
const homeIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const woIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Cliente de consulta para React Query
const queryClient = new QueryClient();

// Função para calcular distância entre dois pontos usando a fórmula de Haversine
const calcularDistancia = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Raio da Terra em km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const d = R * c; // Distância em km
  return d;
};

// Função para obter o primeiro e último dia do mês atual
const obterPeriodoMesAtual = () => {
  const hoje = new Date();
  const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
  const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
  
  return {
    inicio: primeiroDia.toISOString().split('T')[0],
    fim: ultimoDia.toISOString().split('T')[0]
  };
};

// Componente principal
const MapaKMs = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <MapaKMsContent />
    </QueryClientProvider>
  );
};

// Componente de conteúdo
const MapaKMsContent = () => {
  const periodoMesAtual = obterPeriodoMesAtual();
  const [startDate, setStartDate] = useState(periodoMesAtual.inicio);
  const [endDate, setEndDate] = useState(periodoMesAtual.fim);
  const [homeAddress, setHomeAddress] = useState("");
  const [homeCoordenadas, setHomeCoordenadas] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showMap, setShowMap] = useState(false);
  const [erro, setErro] = useState("");
  const [rotasPorDia, setRotasPorDia] = useState({});
  const [diaSelecionado, setDiaSelecionado] = useState(null);
  const [rotaAtual, setRotaAtual] = useState([]);
  const [bounds, setBounds] = useState(null);

  // Simulação de geocodificação do endereço residencial
  const geocodificarEndereco = async (endereco) => {
    if (!endereco.trim()) {
      setErro("Por favor, digite um endereço válido");
      return null;
    }

    setErro("");
    
    try {
      // Simulando uma chamada de API para geocodificação
      // Em produção, isso seria substituído por uma chamada real à API de geocodificação
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Coordenadas simuladas para demonstração
      // Em produção, estas seriam as coordenadas reais retornadas pela API
      const coordenadas = {
        lat: -23.5505 + (Math.random() * 0.02 - 0.01),
        lng: -46.6333 + (Math.random() * 0.02 - 0.01),
      };
      
      return coordenadas;
    } catch (error) {
      console.error("Erro ao geocodificar endereço:", error);
      setErro("Erro ao buscar coordenadas. Tente novamente.");
      return null;
    }
  };

  // Função para obter WOs simuladas para o período selecionado
  const obterWOsPeriodo = async (dataInicio, dataFim) => {
    // Em produção, esta seria uma chamada à API real para obter as WOs do período
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    // Gerar datas dentro do intervalo selecionado
    const datas = [];
    const inicio = new Date(dataInicio);
    const fim = new Date(dataFim);
    
    for (let d = new Date(inicio); d <= fim; d.setDate(d.getDate() + 1)) {
      // Apenas dias úteis (segunda a sexta)
      if (d.getDay() > 0 && d.getDay() < 6) {
        datas.push(new Date(d));
      }
    }
    
    // Gerar WOs simuladas para cada data
    const wosPorDia = {};
    
    datas.forEach(data => {
      const dataFormatada = data.toISOString().split('T')[0];
      const numWOs = Math.floor(Math.random() * 5) + 3; // 3 a 7 WOs por dia
      const wos = [];
      
      for (let i = 0; i < numWOs; i++) {
        wos.push({
          id: `WO-${dataFormatada}-${i+1}`,
          descricao: `Manutenção #${i+1} - ${dataFormatada}`,
          endereco: `Rua Exemplo ${i+1}, São Paulo`,
          coordenadas: {
            lat: -23.5505 + (Math.random() * 0.1 - 0.05),
            lng: -46.6333 + (Math.random() * 0.1 - 0.05)
          }
        });
      }
      
      wosPorDia[dataFormatada] = wos;
    });
    
    return wosPorDia;
  };

  // Função para calcular rotas e distâncias
  const calcularRotas = (wosPorDia, coordenadasCasa) => {
    if (!coordenadasCasa) return {};
    
    const rotasPorDia = {};
    let totalKm = 0;
    
    // Para cada dia com WOs
    Object.keys(wosPorDia).forEach(data => {
      const wos = wosPorDia[data];
      
      if (wos.length === 0) return;
      
      const rota = [];
      const detalhes = [];
      let kmDia = 0;
      
      // Adicionar casa como ponto inicial
      rota.push({
        tipo: 'casa',
        descricao: 'Residência',
        coordenadas: coordenadasCasa
      });
      
      // Calcular distância da casa até a primeira WO
      const primeiraWO = wos[0];
      const distanciaCasaPrimeiraWO = calcularDistancia(
        coordenadasCasa.lat, coordenadasCasa.lng,
        primeiraWO.coordenadas.lat, primeiraWO.coordenadas.lng
      );
      
      kmDia += distanciaCasaPrimeiraWO;
      
      detalhes.push({
        origem: 'Residência',
        destino: `${primeiraWO.id} - ${primeiraWO.endereco}`,
        distancia: distanciaCasaPrimeiraWO
      });
      
      // Adicionar primeira WO à rota
      rota.push({
        tipo: 'wo',
        descricao: primeiraWO.id,
        coordenadas: primeiraWO.coordenadas
      });
      
      // Calcular distâncias entre WOs consecutivas
      for (let i = 0; i < wos.length - 1; i++) {
        const woAtual = wos[i];
        const woProxima = wos[i + 1];
        
        const distancia = calcularDistancia(
          woAtual.coordenadas.lat, woAtual.coordenadas.lng,
          woProxima.coordenadas.lat, woProxima.coordenadas.lng
        );
        
        kmDia += distancia;
        
        detalhes.push({
          origem: `${woAtual.id}`,
          destino: `${woProxima.id} - ${woProxima.endereco}`,
          distancia: distancia
        });
        
        // Adicionar próxima WO à rota
        rota.push({
          tipo: 'wo',
          descricao: woProxima.id,
          coordenadas: woProxima.coordenadas
        });
      }
      
      // Calcular distância da última WO até a casa
      const ultimaWO = wos[wos.length - 1];
      const distanciaUltimaCasa = calcularDistancia(
        ultimaWO.coordenadas.lat, ultimaWO.coordenadas.lng,
        coordenadasCasa.lat, coordenadasCasa.lng
      );
      
      kmDia += distanciaUltimaCasa;
      
      detalhes.push({
        origem: `${ultimaWO.id}`,
        destino: 'Residência',
        distancia: distanciaUltimaCasa
      });
      
      // Adicionar casa como ponto final
      rota.push({
        tipo: 'casa',
        descricao: 'Residência (retorno)',
        coordenadas: coordenadasCasa
      });
      
      // Armazenar resultados do dia
      rotasPorDia[data] = {
        rota: rota,
        detalhes: detalhes,
        kmTotal: kmDia
      };
      
      totalKm += kmDia;
    });
    
    return {
      rotasPorDia: rotasPorDia,
      kmTotal: totalKm
    };
  };

  // Função para gerar dados para exportação
  const gerarDadosExportacao = () => {
    if (!result) return null;
    
    const linhas = [];
    
    // Cabeçalho
    linhas.push(['Data', 'Origem', 'Destino', 'Distância (km)']);
    
    // Dados por dia
    Object.keys(result.rotasPorDia).sort().forEach(data => {
      const { detalhes, kmTotal } = result.rotasPorDia[data];
      
      // Formatar data para exibição
      const dataFormatada = new Date(data).toLocaleDateString('pt-BR');
      
      // Adicionar detalhes do dia
      detalhes.forEach(detalhe => {
        linhas.push([
          dataFormatada,
          detalhe.origem,
          detalhe.destino,
          detalhe.distancia.toFixed(1)
        ]);
      });
      
      // Adicionar total do dia
      linhas.push([
        `${dataFormatada} - TOTAL`,
        '',
        '',
        kmTotal.toFixed(1)
      ]);
      
      // Linha em branco entre dias
      linhas.push(['', '', '', '']);
    });
    
    // Adicionar total geral
    linhas.push(['TOTAL GERAL', '', '', result.kmTotal.toFixed(1)]);
    
    return linhas;
  };

  // Função para exportar dados para CSV
  const exportarCSV = () => {
    if (!result) return;
    
    const dados = gerarDadosExportacao();
    const csvContent = dados.map(linha => linha.join(',')).join('\n');
    
    // Criar blob e link para download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.setAttribute('href', url);
    link.setAttribute('download', `mapa-kms-${startDate}-a-${endDate}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Função para exportar dados para Excel (simulado como CSV)
  const exportarExcel = () => {
    if (!result) return;
    
    const dados = gerarDadosExportacao();
    const csvContent = dados.map(linha => linha.join(',')).join('\n');
    
    // Criar blob e link para download
    const blob = new Blob([csvContent], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.setAttribute('href', url);
    link.setAttribute('download', `mapa-kms-${startDate}-a-${endDate}.xls`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Função para calcular KMs
  const calcularKMs = async () => {
    if (!startDate || !endDate) {
      setErro("Por favor, selecione as datas inicial e final.");
      return;
    }
    
    if (!homeAddress.trim()) {
      setErro("Por favor, informe seu endereço residencial para o cálculo completo.");
      return;
    }
    
    setLoading(true);
    setErro("");
    
    try {
      // Geocodificar endereço residencial
      const coordenadasCasa = await geocodificarEndereco(homeAddress);
      
      if (!coordenadasCasa) {
        setErro("Não foi possível obter as coordenadas do endereço residencial.");
        setLoading(false);
        return;
      }
      
      setHomeCoordenadas(coordenadasCasa);
      
      // Obter WOs do período
      const wosPorDia = await obterWOsPeriodo(startDate, endDate);
      
      // Calcular rotas e distâncias
      const resultado = calcularRotas(wosPorDia, coordenadasCasa);
      
      setResult(resultado);
      setRotasPorDia(resultado.rotasPorDia);
      
      // Selecionar o primeiro dia por padrão
      const primeiroData = Object.keys(resultado.rotasPorDia).sort()[0];
      setDiaSelecionado(primeiroData);
      setRotaAtual(resultado.rotasPorDia[primeiroData]?.rota || []);
      
      // Calcular bounds para o mapa
      if (primeiroData && resultado.rotasPorDia[primeiroData]) {
        const pontos = resultado.rotasPorDia[primeiroData].rota.map(ponto => [
          ponto.coordenadas.lat,
          ponto.coordenadas.lng
        ]);
        setBounds(pontos);
      }
      
      setShowMap(true);
    } catch (error) {
      console.error("Erro ao calcular KMs:", error);
      setErro("Ocorreu um erro ao calcular os quilômetros. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  // Efeito para atualizar a rota quando o dia selecionado muda
  useEffect(() => {
    if (diaSelecionado && rotasPorDia[diaSelecionado]) {
      setRotaAtual(rotasPorDia[diaSelecionado].rota);
      
      // Atualizar bounds do mapa
      const pontos = rotasPorDia[diaSelecionado].rota.map(ponto => [
        ponto.coordenadas.lat,
        ponto.coordenadas.lng
      ]);
      setBounds(pontos);
    }
  }, [diaSelecionado, rotasPorDia]);

  // Função para formatar moeda
  const formatarMoeda = (valor) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'EUR'
    }).format(valor);
  };

  return (
    <div className="space-y-6">
      {/* Formulário de cálculo */}
      <div className="bg-card rounded-lg p-6 border border-gray-200 shadow-sm">
        <h2 className="text-lg font-medium text-text mb-4 flex items-center gap-2">
          <Calculator size={20} className="text-primary" />
          Mapa de KMs
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-muted mb-1">
              Data Inicial
            </label>
            <div className="relative">
              <input
                type="date"
                id="startDate"
                className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={loading}
              />
              <Calendar size={18} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted" />
            </div>
          </div>
          
          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-muted mb-1">
              Data Final
            </label>
            <div className="relative">
              <input
                type="date"
                id="endDate"
                className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={loading}
              />
              <Calendar size={18} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted" />
            </div>
          </div>
        </div>
        
        <div className="mb-4">
          <label htmlFor="homeAddress" className="block text-sm font-medium text-muted mb-1">
            Endereço Residencial
          </label>
          <div className="relative">
            <input
              type="text"
              id="homeAddress"
              className="w-full rounded-md border border-gray-300 py-2 pl-3 pr-10 text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              value={homeAddress}
              onChange={(e) => setHomeAddress(e.target.value)}
              placeholder="Digite seu endereço residencial para cálculo completo"
              disabled={loading}
            />
            <Home size={18} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted" />
          </div>
          <p className="mt-1 text-xs text-muted">
            Informe seu endereço para calcular o trajeto completo (casa-trabalho-casa)
          </p>
          {erro && <p className="mt-1 text-xs text-red-500">{erro}</p>}
        </div>
        
        <div className="flex justify-end">
          <button
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={calcularKMs}
            disabled={loading || !startDate || !endDate || !homeAddress.trim()}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                <span>Calculando...</span>
              </>
            ) : (
              <>
                <Navigation size={18} />
                <span>Calcular Rotas</span>
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Resultados do cálculo */}
      {result && (
        <div className="bg-card rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <h2 className="text-lg font-medium text-text flex items-center gap-2">
              <BarChart2 size={20} className="text-primary" />
              Resultado do Cálculo
            </h2>
            
            <div className="flex items-center gap-2">
              <button
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-muted hover:bg-gray-50 transition-colors flex items-center gap-2"
                onClick={exportarCSV}
              >
                <Download size={16} />
                <span>CSV</span>
              </button>
              <button
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-muted hover:bg-gray-50 transition-colors flex items-center gap-2"
                onClick={exportarExcel}
              >
                <Download size={16} />
                <span>Excel</span>
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <p className="text-sm text-blue-600 mb-1">Total de KMs percorridos</p>
              <p className="text-2xl font-bold text-blue-700">{result.kmTotal.toFixed(1)} km</p>
            </div>
            
            <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100">
              <p className="text-sm text-emerald-600 mb-1">Valor a receber (€0,36/km)</p>
              <p className="text-2xl font-bold text-emerald-700">{formatarMoeda(result.kmTotal * 0.36)}</p>
            </div>
          </div>
          
          <h3 className="text-md font-medium text-text mb-3">Detalhes por Dia</h3>
          
          <div className="mb-6 space-y-3">
            {Object.keys(result.rotasPorDia).sort().map(data => {
              const { kmTotal } = result.rotasPorDia[data];
              const dataFormatada = new Date(data).toLocaleDateString('pt-BR', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              });
              
              return (
                <motion.div
                  key={data}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`border rounded-lg overflow-hidden cursor-pointer transition-colors ${
                    diaSelecionado === data ? 'border-primary bg-primary bg-opacity-5' : 'border-gray-200'
                  }`}
                  onClick={() => setDiaSelecionado(data)}
                >
                  <div className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-text capitalize">{dataFormatada}</p>
                      <p className="text-sm text-muted">
                        {result.rotasPorDia[data].detalhes.length - 1} paradas • {kmTotal.toFixed(1)} km
                      </p>
                    </div>
                    <div className="flex items-center">
                      <span className="text-lg font-semibold text-primary mr-2">
                        {formatarMoeda(kmTotal * 0.36)}
                      </span>
                      <ChevronDown 
                        size={18} 
                        className={`text-muted transition-transform ${
                          diaSelecionado === data ? 'transform rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  
                  {diaSelecionado === data && (
                    <div className="bg-white border-t border-gray-100 p-4">
                      <table className="w-full min-w-full">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="py-2 px-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Origem</th>
                            <th className="py-2 px-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Destino</th>
                            <th className="py-2 px-3 text-right text-xs font-medium text-muted uppercase tracking-wider">Distância</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {result.rotasPorDia[data].detalhes.map((item, index) => (
                            <tr key={index} className="hover:bg-gray-50 transition-colors">
                              <td className="py-2 px-3 text-sm text-muted">{item.origem}</td>
                              <td className="py-2 px-3 text-sm text-muted">{item.destino}</td>
                              <td className="py-2 px-3 text-sm font-medium text-text text-right">{item.distancia.toFixed(1)} km</td>
                            </tr>
                          ))}
                          <tr className="bg-gray-50">
                            <td className="py-2 px-3 text-sm font-medium text-text" colSpan="2">Total</td>
                            <td className="py-2 px-3 text-sm font-bold text-primary text-right">{kmTotal.toFixed(1)} km</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Visualização do mapa */}
      {showMap && (
        <div className="bg-card rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-text flex items-center gap-2">
              <MapPin size={20} className="text-primary" />
              Visualização da Rota
            </h2>
            <div className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs flex items-center">
              <Info size={12} className="mr-1" />
              <span>Interativo</span>
            </div>
          </div>
          
          <div className="h-[500px] rounded-xl overflow-hidden border border-gray-200">
            {bounds && (
              <MapContainer
                bounds={bounds}
                style={{ height: "100%", width: "100%" }}
                zoomControl={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {/* Marcadores para cada ponto da rota */}
                {rotaAtual.map((ponto, index) => (
                  <Marker 
                    key={`marker-${index}`}
                    position={[ponto.coordenadas.lat, ponto.coordenadas.lng]}
                    icon={ponto.tipo === 'casa' ? homeIcon : woIcon}
                  >
                    <Popup>
                      {ponto.descricao}
                    </Popup>
                  </Marker>
                ))}
                
                {/* Linha conectando os pontos da rota */}
                <Polyline
                  positions={rotaAtual.map(ponto => [ponto.coordenadas.lat, ponto.coordenadas.lng])}
                  color="#3B82F6"
                  weight={4}
                  opacity={0.7}
                />
              </MapContainer>
            )}
          </div>
          
          <div className="mt-4 text-xs text-muted">
            <p>* As distâncias são calculadas considerando o trajeto em linha reta entre os pontos.</p>
            <p>* Para maior precisão, certifique-se de fornecer o endereço residencial completo com CEP.</p>
            <p>* Os valores são calculados com base na taxa de €0,36 por quilômetro percorrido.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapaKMs;
