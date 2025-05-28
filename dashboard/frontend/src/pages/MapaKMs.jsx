import React, { useState } from "react";
import { useQuery, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { motion } from "framer-motion";
import { Search, MapPin, Info } from "lucide-react";
import '../styles/variables.css';

// Corrigindo o problema dos ícones do Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

// Cliente de consulta para React Query
const queryClient = new QueryClient();

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
  const [endereco, setEndereco] = useState("");
  const [coordenadas, setCoordenadas] = useState(null);
  const [distancia, setDistancia] = useState(null);
  const [erro, setErro] = useState("");

  // Simulação de consulta de coordenadas
  const buscarCoordenadas = async () => {
    if (!endereco.trim()) {
      setErro("Por favor, digite um endereço válido");
      return;
    }

    setErro("");
    
    try {
      // Simulando uma chamada de API para geocodificação
      // Em produção, isso seria substituído por uma chamada real
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Coordenadas simuladas para demonstração
      const novasCoordenadas = {
        lat: -23.5505 + (Math.random() * 0.02 - 0.01),
        lng: -46.6333 + (Math.random() * 0.02 - 0.01),
      };
      
      setCoordenadas(novasCoordenadas);
      
      // Simulando cálculo de distância
      const distanciaCalculada = (Math.random() * 10 + 2).toFixed(2);
      setDistancia(distanciaCalculada);
    } catch (error) {
      console.error("Erro ao buscar coordenadas:", error);
      setErro("Erro ao buscar coordenadas. Tente novamente.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-card rounded-2xl shadow-md p-6">
        <h2 className="text-lg font-medium text-text mb-4">Calculadora de Quilômetros</h2>
        
        <div className="mb-6">
          <label className="block text-sm text-muted mb-2">Endereço</label>
          <div className="flex">
            <input
              type="text"
              value={endereco}
              onChange={(e) => setEndereco(e.target.value)}
              placeholder="Digite o endereço completo"
              className="flex-1 border border-gray-300 rounded-l-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={buscarCoordenadas}
              className="bg-primary text-white px-4 py-2 rounded-r-lg hover:bg-primary-dark transition flex items-center"
            >
              <Search size={16} className="mr-1" />
              <span>Buscar</span>
            </button>
          </div>
          {erro && <p className="text-red-500 text-xs mt-1">{erro}</p>}
        </div>
        
        {distancia && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-secondary rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <p className="text-sm text-muted">Distância estimada:</p>
              <p className="text-xl font-bold text-primary">{distancia} km</p>
            </div>
            <div className="bg-primary bg-opacity-10 p-3 rounded-full">
              <MapPin size={24} className="text-primary" />
            </div>
          </motion.div>
        )}
      </div>
      
      <div className="bg-card rounded-2xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-text">Visualização no Mapa</h2>
          <div className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs flex items-center">
            <Info size={12} className="mr-1" />
            <span>Interativo</span>
          </div>
        </div>
        
        <div className="h-[400px] rounded-xl overflow-hidden border border-gray-200">
          <MapContainer
            center={coordenadas || [-23.5505, -46.6333]} // São Paulo como padrão
            zoom={13}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {coordenadas && (
              <Marker position={[coordenadas.lat, coordenadas.lng]}>
                <Popup>
                  Endereço buscado <br />
                  Distância: {distancia} km
                </Popup>
              </Marker>
            )}
          </MapContainer>
        </div>
        
        <div className="mt-4 text-xs text-muted">
          <p>* As distâncias são calculadas em linha reta e podem variar da distância real de deslocamento.</p>
          <p>* Para maior precisão, certifique-se de fornecer o endereço completo com CEP.</p>
        </div>
      </div>
    </div>
  );
};

export default MapaKMs;
