import React from 'react';
import { Bell, CheckCircle, AlertTriangle, AlertCircle, Clock, RefreshCw } from 'lucide-react';

// Componente para notificações de status
const StatusNotification = ({ type, message, timestamp, onDismiss }) => {
  // Definir ícone e cores com base no tipo
  const getTypeConfig = () => {
    switch (type) {
      case 'success':
        return {
          icon: <CheckCircle size={20} />,
          bgColor: 'bg-emerald-50',
          textColor: 'text-emerald-800',
          borderColor: 'border-emerald-200',
          iconColor: 'text-emerald-500'
        };
      case 'error':
        return {
          icon: <AlertCircle size={20} />,
          bgColor: 'bg-red-50',
          textColor: 'text-red-800',
          borderColor: 'border-red-200',
          iconColor: 'text-red-500'
        };
      case 'warning':
        return {
          icon: <AlertTriangle size={20} />,
          bgColor: 'bg-amber-50',
          textColor: 'text-amber-800',
          borderColor: 'border-amber-200',
          iconColor: 'text-amber-500'
        };
      case 'info':
        return {
          icon: <Bell size={20} />,
          bgColor: 'bg-blue-50',
          textColor: 'text-blue-800',
          borderColor: 'border-blue-200',
          iconColor: 'text-blue-500'
        };
      case 'processing':
        return {
          icon: <RefreshCw size={20} className="animate-spin" />,
          bgColor: 'bg-purple-50',
          textColor: 'text-purple-800',
          borderColor: 'border-purple-200',
          iconColor: 'text-purple-500'
        };
      default:
        return {
          icon: <Bell size={20} />,
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-800',
          borderColor: 'border-gray-200',
          iconColor: 'text-gray-500'
        };
    }
  };

  const config = getTypeConfig();

  return (
    <div className={`${config.bgColor} ${config.textColor} border ${config.borderColor} rounded-lg p-4 mb-3 flex items-start animate-fadeIn`}>
      <div className={`${config.iconColor} mr-3 mt-0.5 flex-shrink-0`}>
        {config.icon}
      </div>
      <div className="flex-1">
        <p className="font-medium">{message}</p>
        {timestamp && (
          <p className="text-xs mt-1 opacity-75 flex items-center">
            <Clock size={12} className="mr-1" />
            {timestamp}
          </p>
        )}
      </div>
      {onDismiss && (
        <button 
          onClick={onDismiss} 
          className={`ml-3 p-1 rounded-full hover:bg-white/20 ${config.textColor}`}
          aria-label="Fechar notificação"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      )}
    </div>
  );
};

// Componente para indicador de progresso
const ProgressIndicator = ({ progress, status, label }) => {
  // Determinar cor com base no status
  const getStatusColor = () => {
    switch (status) {
      case 'success': return 'bg-emerald-500';
      case 'error': return 'bg-red-500';
      case 'warning': return 'bg-amber-500';
      case 'processing': return 'bg-purple-500';
      default: return 'bg-primary';
    }
  };

  const statusColor = getStatusColor();

  return (
    <div className="mb-4">
      {label && <p className="text-sm text-muted mb-1">{label}</p>}
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className={`h-full ${statusColor} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <p className="text-xs text-muted mt-1 text-right">{progress}% concluído</p>
    </div>
  );
};

// Componente para indicador de status em tempo real
const StatusIndicator = ({ status, label, animate = false }) => {
  // Configurar com base no status
  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return { color: 'bg-emerald-500', text: 'Online', textColor: 'text-emerald-800' };
      case 'offline':
        return { color: 'bg-red-500', text: 'Offline', textColor: 'text-red-800' };
      case 'processing':
        return { color: 'bg-purple-500', text: 'Processando', textColor: 'text-purple-800' };
      case 'waiting':
        return { color: 'bg-amber-500', text: 'Aguardando', textColor: 'text-amber-800' };
      default:
        return { color: 'bg-gray-500', text: 'Desconhecido', textColor: 'text-gray-800' };
    }
  };

  const config = getStatusConfig();
  
  return (
    <div className="flex items-center">
      {label && <span className="text-sm text-muted mr-2">{label}:</span>}
      <div className="flex items-center">
        <span className={`inline-block w-2.5 h-2.5 rounded-full ${config.color} ${animate ? 'animate-pulse' : ''} mr-1.5`}></span>
        <span className={`text-xs font-medium ${config.textColor}`}>{config.text}</span>
      </div>
    </div>
  );
};

// Componente para toast de notificação
const Toast = ({ message, type = 'info', duration = 5000, onClose }) => {
  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        if (onClose) onClose();
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);
  
  // Configurar com base no tipo
  const getTypeConfig = () => {
    switch (type) {
      case 'success':
        return { icon: <CheckCircle size={18} />, bgColor: 'bg-emerald-500' };
      case 'error':
        return { icon: <AlertCircle size={18} />, bgColor: 'bg-red-500' };
      case 'warning':
        return { icon: <AlertTriangle size={18} />, bgColor: 'bg-amber-500' };
      case 'processing':
        return { icon: <RefreshCw size={18} className="animate-spin" />, bgColor: 'bg-purple-500' };
      default:
        return { icon: <Bell size={18} />, bgColor: 'bg-primary' };
    }
  };
  
  const config = getTypeConfig();
  
  return (
    <div className={`${config.bgColor} text-card px-4 py-3 rounded-lg shadow-lg flex items-center animate-slideIn max-w-md`}>
      <div className="mr-3">
        {config.icon}
      </div>
      <div className="flex-1">
        {message}
      </div>
      {onClose && (
        <button 
          onClick={onClose} 
          className="ml-3 p-1 rounded-full hover:bg-white/20 text-card"
          aria-label="Fechar notificação"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      )}
    </div>
  );
};

// Componente para animação de carregamento
const LoadingSpinner = ({ size = 'medium', color = 'primary', label }) => {
  // Configurar tamanho
  const getSize = () => {
    switch (size) {
      case 'small': return 'w-4 h-4 border-2';
      case 'large': return 'w-10 h-10 border-4';
      default: return 'w-6 h-6 border-3';
    }
  };
  
  // Configurar cor
  const getColor = () => {
    switch (color) {
      case 'white': return 'border-white/30 border-t-white';
      case 'success': return 'border-emerald-200 border-t-emerald-500';
      case 'error': return 'border-red-200 border-t-red-500';
      default: return 'border-purple-200 border-t-purple-500';
    }
  };
  
  const sizeClass = getSize();
  const colorClass = getColor();
  
  return (
    <div className="flex items-center justify-center">
      <div className={`${sizeClass} ${colorClass} rounded-full animate-spin`}></div>
      {label && <span className="ml-3 text-sm text-muted">{label}</span>}
    </div>
  );
};

export { 
  StatusNotification, 
  ProgressIndicator, 
  StatusIndicator, 
  Toast, 
  LoadingSpinner 
};
