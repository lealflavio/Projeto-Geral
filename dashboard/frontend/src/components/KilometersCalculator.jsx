import React, { useState, useRef } from 'react';
import { MapPin, Calendar, Home, Navigation, Download, BarChart2, FileText, RefreshCw, Calculator } from 'lucide-react';

const KilometersCalculator = () => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [homeAddress, setHomeAddress] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [showMap, setShowMap] = useState(false);

    // Dados simulados para demonstração
    const mockCalculateKMs = () => {
        setLoading(true);
        
        // Simular tempo de processamento
        setTimeout(() => {
            const mockResult = {
                total_km: 127.5,
                detalhes: [
                    { origem: 'Residência', destino: 'WO #12345 - Rua das Flores, 123', distancia: 15.3 },
                    { origem: 'WO #12345', destino: 'WO #12346 - Av. da Liberdade, 45', distancia: 8.7 },
                    { origem: 'WO #12346', destino: 'WO #12347 - Rua Augusta, 290', distancia: 12.2 },
                    { origem: 'WO #12347', destino: 'WO #12348 - Praça do Comércio, 15', distancia: 5.8 },
                    { origem: 'WO #12348', destino: 'WO #12349 - Rua do Carmo, 71', distancia: 7.4 },
                    { origem: 'WO #12349', destino: 'Residência', distancia: 18.1 },
                ]
            };
            
            setResult(mockResult);
            setLoading(false);
            setShowMap(true);
        }, 1500);
    };

    const handleCalculate = () => {
        if (!startDate || !endDate) {
            alert('Por favor, selecione as datas inicial e final.');
            return;
        }
        
        mockCalculateKMs();
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'EUR'
        }).format(value);
    };

    const handleExportCSV = () => {
        if (!result) return;
        
        alert('Exportando dados para CSV...');
        // Implementação real conectaria com backend para gerar e baixar o arquivo
    };

    const handleExportPDF = () => {
        if (!result) return;
        
        alert('Exportando dados para PDF...');
        // Implementação real conectaria com backend para gerar e baixar o arquivo
    };

    return (
        <div className="space-y-6">
            {/* Formulário de cálculo */}
            <div className="bg-card rounded-lg p-6 border border-gray-200">
                <h2 className="text-lg font-medium text-text mb-4 flex items-center gap-2">
                    <Calculator size={20} className="text-primary" />
                    Calculadora de Quilometragem
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
                        Endereço Residencial (opcional)
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
                </div>
                
                <div className="flex justify-end">
                    <button
                        className="px-4 py-2 bg-primary text-card rounded-lg hover:bg-opacity-90 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={handleCalculate}
                        disabled={loading || !startDate || !endDate}
                    >
                        {loading ? (
                            <>
                                <RefreshCw size={18} className="animate-spin" />
                                <span>Calculando...</span>
                            </>
                        ) : (
                            <>
                                <Navigation size={18} />
                                <span>Calcular Rota</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
            
            {/* Resultados do cálculo */}
            {result && (
                <div className="bg-card rounded-lg p-6 border border-gray-200">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                        <h2 className="text-lg font-medium text-text flex items-center gap-2">
                            <BarChart2 size={20} className="text-primary" />
                            Resultado do Cálculo
                        </h2>
                        
                        <div className="flex items-center gap-2">
                            <button
                                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-muted hover:bg-gray-50 transition-colors flex items-center gap-2"
                                onClick={handleExportCSV}
                            >
                                <Download size={16} />
                                <span>CSV</span>
                            </button>
                            <button
                                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-muted hover:bg-gray-50 transition-colors flex items-center gap-2"
                                onClick={handleExportPDF}
                            >
                                <Download size={16} />
                                <span>PDF</span>
                            </button>
                        </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                            <p className="text-sm text-blue-600 mb-1">Total de KMs percorridos</p>
                            <p className="text-2xl font-bold text-blue-700">{result.total_km.toFixed(1)} km</p>
                        </div>
                        
                        <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100">
                            <p className="text-sm text-emerald-600 mb-1">Valor a receber (€0,36/km)</p>
                            <p className="text-2xl font-bold text-emerald-700">{formatCurrency(result.total_km * 0.36)}</p>
                        </div>
                    </div>
                    
                    <h3 className="text-md font-medium text-text mb-3">Detalhes do Percurso</h3>
                    
                    <div className="overflow-x-auto">
                        <table className="w-full min-w-full">
                            <thead>
                                <tr className="bg-gray-50 border-b border-gray-200">
                                    <th className="py-3 px-4 text-left text-xs font-medium text-muted uppercase tracking-wider">Origem</th>
                                    <th className="py-3 px-4 text-left text-xs font-medium text-muted uppercase tracking-wider">Destino</th>
                                    <th className="py-3 px-4 text-right text-xs font-medium text-muted uppercase tracking-wider">Distância</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {result.detalhes.map((item, index) => (
                                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                                        <td className="py-3 px-4 text-sm text-muted">{item.origem}</td>
                                        <td className="py-3 px-4 text-sm text-muted">{item.destino}</td>
                                        <td className="py-3 px-4 text-sm font-medium text-text text-right">{item.distancia.toFixed(1)} km</td>
                                    </tr>
                                ))}
                                <tr className="bg-gray-50">
                                    <td className="py-3 px-4 text-sm font-medium text-text" colSpan="2">Total</td>
                                    <td className="py-3 px-4 text-sm font-bold text-primary text-right">{result.total_km.toFixed(1)} km</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
            
            {/* Visualização do mapa */}
            {showMap && (
                <div className="bg-card rounded-lg p-6 border border-gray-200">
                    <h2 className="text-lg font-medium text-text mb-4 flex items-center gap-2">
                        <MapPin size={20} className="text-primary" />
                        Visualização da Rota
                    </h2>
                    
                    <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                        {/* Aqui seria integrado um mapa real como Google Maps ou Leaflet */}
                        <div className="w-full h-full flex items-center justify-center">
                            <div className="text-center p-6">
                                <MapPin size={48} className="text-primary mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-muted mb-2">Mapa de Rotas</h3>
                                <p className="text-sm text-muted">
                                    Em um ambiente de produção, aqui seria exibido o mapa com a rota calculada
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default KilometersCalculator;
