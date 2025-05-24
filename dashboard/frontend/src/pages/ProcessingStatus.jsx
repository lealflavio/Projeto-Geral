import React, { useState, useEffect } from 'react';
import { StatusNotification, ProgressIndicator, StatusIndicator, Toast, LoadingSpinner } from '../components/FeedbackVisual';
import { Bell, RefreshCw, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

const ProcessingStatus = () => {
  const [notifications, setNotifications] = useState([]);
  const [showToast, setShowToast] = useState(false);
  const [toastConfig, setToastConfig] = useState({});
  const [processingStatus, setProcessingStatus] = useState('waiting');
  const [processingProgress, setProcessingProgress] = useState(0);
  
  // Simulação de progresso de processamento
  useEffect(() => {
    if (processingStatus === 'processing') {
      const interval = setInterval(() => {
        setProcessingProgress(prev => {
          const newProgress = prev + Math.floor(Math.random() * 5) + 1;
          if (newProgress >= 100) {
            clearInterval(interval);
            setProcessingStatus('success');
            showNotification('success', 'Processamento concluído com sucesso!');
            showToastMessage('Processamento finalizado', 'success');
            return 100;
          }
          return newProgress;
        });
      }, 800);
      
      return () => clearInterval(interval);
    }
  }, [processingStatus]);
  
  // Função para adicionar notificação
  const showNotification = (type, message) => {
    const newNotification = {
      id: Date.now(),
      type,
      message,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setNotifications(prev => [newNotification, ...prev]);
  };
  
  // Função para remover notificação
  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };
  
  // Função para mostrar toast
  const showToastMessage = (message, type = 'info') => {
    setToastConfig({ message, type });
    setShowToast(true);
  };
  
  // Função para iniciar processamento simulado
  const startProcessing = () => {
    setProcessingStatus('processing');
    setProcessingProgress(0);
    showNotification('processing', 'Iniciando processamento de PDF...');
    showToastMessage('Processamento iniciado', 'processing');
  };
  
  // Função para simular erro
  const simulateError = () => {
    setProcessingStatus('error');
    showNotification('error', 'Erro no processamento: formato de PDF não suportado.');
    showToastMessage('Erro no processamento', 'error');
  };
  
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Status de Processamento</h1>
      
      {/* Painel de status */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#333]">Status Atual</h2>
          <StatusIndicator 
            status={processingStatus} 
            animate={processingStatus === 'processing'} 
          />
        </div>
        
        {/* Indicador de progresso */}
        <ProgressIndicator 
          progress={processingProgress} 
          status={processingStatus} 
          label="Progresso do processamento" 
        />
        
        {/* Botões de ação */}
        <div className="flex flex-wrap gap-3 mt-6">
          <button 
            className="bg-[#7C3AED] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#6B21A8] transition flex items-center gap-2"
            onClick={startProcessing}
            disabled={processingStatus === 'processing'}
          >
            <RefreshCw size={18} className={processingStatus === 'processing' ? 'animate-spin' : ''} />
            <span>Iniciar Processamento</span>
          </button>
          
          <button 
            className="bg-red-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-600 transition flex items-center gap-2"
            onClick={simulateError}
          >
            <AlertCircle size={18} />
            <span>Simular Erro</span>
          </button>
          
          <button 
            className="border border-gray-200 px-4 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition flex items-center gap-2"
            onClick={() => showNotification('info', 'Esta é uma notificação informativa de exemplo.')}
          >
            <Bell size={18} />
            <span>Notificação Info</span>
          </button>
          
          <button 
            className="border border-gray-200 px-4 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition flex items-center gap-2"
            onClick={() => showNotification('warning', 'Atenção: este é um aviso importante.')}
          >
            <AlertTriangle size={18} />
            <span>Notificação Aviso</span>
          </button>
        </div>
      </div>
      
      {/* Exemplos de indicadores de carregamento */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#333] mb-4">Indicadores de Carregamento</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
            <LoadingSpinner size="small" label="Carregamento pequeno" />
          </div>
          
          <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
            <LoadingSpinner label="Carregamento médio" />
          </div>
          
          <div className="flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
            <LoadingSpinner size="large" label="Carregamento grande" />
          </div>
        </div>
      </div>
      
      {/* Painel de notificações */}
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#333]">Notificações</h2>
          {notifications.length > 0 && (
            <button 
              className="text-sm text-[#7C3AED] hover:underline"
              onClick={() => setNotifications([])}
            >
              Limpar todas
            </button>
          )}
        </div>
        
        {notifications.length === 0 ? (
          <div className="text-center py-8 text-[#777]">
            <Bell size={32} className="mx-auto mb-2 opacity-30" />
            <p>Nenhuma notificação no momento</p>
          </div>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            {notifications.map(notification => (
              <StatusNotification 
                key={notification.id}
                type={notification.type}
                message={notification.message}
                timestamp={notification.timestamp}
                onDismiss={() => dismissNotification(notification.id)}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Toast de notificação */}
      {showToast && (
        <div className="fixed bottom-4 right-4 z-50">
          <Toast 
            message={toastConfig.message}
            type={toastConfig.type}
            onClose={() => setShowToast(false)}
          />
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;
