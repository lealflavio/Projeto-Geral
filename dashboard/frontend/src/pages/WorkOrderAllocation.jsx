import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, Loader2, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

// Componente de Card padronizado
const Card = ({ children, className = "" }) => (
  <div className={`bg-white shadow-md rounded-lg p-6 ${className}`}>
    {children}
  </div>
);

// Componente de Status Badge
const StatusBadge = ({ status }) => {
  const getStatusConfig = () => {
    switch (status?.toUpperCase()) {
      case 'ALLOCATED':
        return { bg: 'bg-green-100', text: 'text-green-800', label: 'ALOCADA' };
      case 'IN PROGRESS':
        return { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'EM PROGRESSO' };
      case 'JOB START':
        return { bg: 'bg-blue-100', text: 'text-blue-800', label: 'INICIADA' };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-800', label: status || 'N/A' };
    }
  };

  const { bg, text, label } = getStatusConfig();

  return (
    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${bg} ${text}`}>
      {label}
    </span>
  );
};

const WorkOrderAllocation = () => {
  const [workOrderId, setWorkOrderId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const [mapApp, setMapApp] = useState('google'); // 'google', 'waze', 'apple'
  const [recentWOs, setRecentWOs] = useState([]);

  // Carregar WOs recentes do localStorage ao iniciar
  useEffect(() => {
    const savedWOs = localStorage.getItem('recentWOs');
    if (savedWOs) {
      try {
        setRecentWOs(JSON.parse(savedWOs));
      } catch (e) {
        console.error('Erro ao carregar WOs recentes:', e);
      }
    }
  }, []);

  // Salvar WO no histórico recente
  const saveToRecent = (woData) => {
    if (!woData || !woData.id) return;
    
    const newRecentWOs = [
      { 
        id: woData.id, 
        estado: woData.estado,
        pdo: woData.pdo,
        timestamp: new Date().toISOString()
      },
      ...recentWOs.filter(wo => wo.id !== woData.id)
    ].slice(0, 5); // Manter apenas as 5 mais recentes
    
    setRecentWOs(newRecentWOs);
    localStorage.setItem('recentWOs', JSON.stringify(newRecentWOs));
  };

  // Verificar cache antes de fazer requisição
  const checkCache = (id) => {
    const cacheKey = `wo_${id}`;
    const cached = localStorage.getItem(cacheKey);
    
    if (cached) {
      try {
        const parsedCache = JSON.parse(cached);
        const cacheTime = new Date(parsedCache.timestamp);
        const now = new Date();
        
        // Cache válido por 30 minutos
        if ((now - cacheTime) < 30 * 60 * 1000) {
          return parsedCache.data;
        }
      } catch (e) {
        console.error('Erro ao ler cache:', e);
      }
    }
    
    return null;
  };

  // Salvar resultado no cache
  const saveToCache = (id, data) => {
    if (!id || !data) return;
    
    const cacheKey = `wo_${id}`;
    const cacheData = {
      data,
      timestamp: new Date().toISOString()
    };
    
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!workOrderId.trim()) {
      setError('Por favor, insira o número da WO');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    // Verificar cache
    const cachedData = checkCache(workOrderId);
    if (cachedData) {
      setResult(cachedData);
      setSuccess(true);
      setLoading(false);
      saveToRecent(cachedData.dados);
      return;
    }
    
    try {
      const response = await axios.post('/api/wondercom/allocate', {
        work_order_id: workOrderId
      });
      
      setResult(response.data);
      setSuccess(true);
      
      // Salvar no cache e no histórico recente
      saveToCache(workOrderId, response.data);
      if (response.data.dados) {
        saveToRecent(response.data.dados);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao alocar WO. Tente novamente.');
      console.error('Erro:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentWO = (id) => {
    setWorkOrderId(id);
    
    // Verificar cache
    const cachedData = checkCache(id);
    if (cachedData) {
      setResult(cachedData);
      setSuccess(true);
      return;
    }
    
    // Se não estiver em cache, submeter o formulário
    handleSubmit({ preventDefault: () => {} });
  };

  const openMap = (coordinates) => {
    if (!coordinates) return;
    
    // Extrai latitude e longitude das coordenadas
    // Formato esperado: "41.1579438, -8.6291053" ou similar
    const [lat, lng] = coordinates.split(',').map(coord => coord.trim());
    
    let mapUrl;
    
    switch (mapApp) {
      case 'google':
        mapUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
        break;
      case 'waze':
        mapUrl = `https://waze.com/ul?ll=${lat},${lng}&navigate=yes`;
        break;
      case 'apple':
        mapUrl = `http://maps.apple.com/?daddr=${lat},${lng}`;
        break;
      default:
        mapUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    }
    
    window.open(mapUrl, '_blank');
  };

  const clearCache = () => {
    if (workOrderId) {
      localStorage.removeItem(`wo_${workOrderId}`);
      setSuccess(false);
      setResult(null);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Alocação de Ordem de Trabalho</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="mb-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="workOrderId" className="block text-sm font-medium text-gray-700 mb-1">
                  Número da WO
                </label>
                <input
                  type="text"
                  id="workOrderId"
                  value={workOrderId}
                  onChange={(e) => setWorkOrderId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: 12345678"
                  disabled={loading}
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin mr-2" size={20} />
                    Alocando...
                  </>
                ) : (
                  'Alocar WO'
                )}
              </button>
            </form>
            
            {error && (
              <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md flex items-start">
                <AlertCircle className="mr-2 mt-0.5 flex-shrink-0" size={18} />
                <span>{error}</span>
              </div>
            )}
            
            {success && !error && (
              <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-md flex items-start">
                <CheckCircle className="mr-2 mt-0.5 flex-shrink-0" size={18} />
                <span>WO alocada com sucesso!</span>
              </div>
            )}
          </Card>
          
          {result && result.dados && (
            <Card>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Detalhes da WO {result.dados.id}</h2>
                <button 
                  onClick={clearCache}
                  className="text-blue-600 hover:text-blue-800 flex items-center text-sm"
                >
                  <RefreshCw size={16} className="mr-1" />
                  Atualizar
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Estado</h3>
                    <div className="mt-1">
                      <StatusBadge status={result.dados.estado} />
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">PDO</h3>
                    <p className="mt-1 text-lg">{result.dados.pdo || 'N/A'}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Fibra</h3>
                    <p className="mt-1 text-lg">{result.dados.fibra || 'N/A'}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Cor da Fibra</h3>
                    <p className="mt-1 text-lg">{result.dados.cor_fibra || 'N/A'}</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Endereço</h3>
                    <p className="mt-1 text-lg">{result.dados.endereco || 'N/A'}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Coordenadas</h3>
                    <p className="mt-1 text-lg">{result.dados.coordenadas || 'N/A'}</p>
                    
                    {result.dados.coordenadas && (
                      <div className="mt-4">
                        <h3 className="text-sm font-medium text-gray-500 mb-2">Abrir no Mapa</h3>
                        
                        <div className="flex space-x-2">
                          <button
                            onClick={() => setMapApp('google')}
                            className={`px-3 py-1 rounded-md text-sm ${
                              mapApp === 'google' 
                                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                                : 'bg-gray-100 text-gray-700 border border-gray-300'
                            }`}
                          >
                            Google Maps
                          </button>
                          
                          <button
                            onClick={() => setMapApp('waze')}
                            className={`px-3 py-1 rounded-md text-sm ${
                              mapApp === 'waze' 
                                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                                : 'bg-gray-100 text-gray-700 border border-gray-300'
                            }`}
                          >
                            Waze
                          </button>
                          
                          <button
                            onClick={() => setMapApp('apple')}
                            className={`px-3 py-1 rounded-md text-sm ${
                              mapApp === 'apple' 
                                ? 'bg-blue-100 text-blue-700 border border-blue-300' 
                                : 'bg-gray-100 text-gray-700 border border-gray-300'
                            }`}
                          >
                            Apple Maps
                          </button>
                        </div>
                        
                        <button
                          onClick={() => openMap(result.dados.coordenadas)}
                          className="mt-2 flex items-center text-blue-600 hover:text-blue-800"
                        >
                          <MapPin size={18} className="mr-1" />
                          Abrir Rota
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
        
        <div className="lg:col-span-1">
          <Card>
            <h2 className="text-lg font-semibold mb-4">WOs Recentes</h2>
            
            {recentWOs.length > 0 ? (
              <div className="space-y-3">
                {recentWOs.map((wo) => (
                  <div 
                    key={wo.id} 
                    className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => loadRecentWO(wo.id)}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium">WO #{wo.id}</span>
                      <StatusBadge status={wo.estado} />
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      <span>PDO: {wo.pdo || 'N/A'}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(wo.timestamp).toLocaleString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">Nenhuma WO recente encontrada.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default WorkOrderAllocation;
