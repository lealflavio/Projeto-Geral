import { useState, useEffect } from 'react';

// Função para simular o comportamento do componente SessionTimeoutHandler
const TestSessionTimeout = () => {
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutos em segundos
  const [showWarning, setShowWarning] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Efeito para simular a contagem regressiva
  useEffect(() => {
    const interval = setInterval(() => {
      // Calcula o tempo desde a última atividade em segundos
      const elapsedSeconds = Math.floor((Date.now() - lastActivity) / 1000);
      const remaining = 300 - elapsedSeconds; // 5 minutos - tempo decorrido
      
      setTimeRemaining(remaining > 0 ? remaining : 0);
      
      // Mostra aviso quando faltam 30 segundos
      if (remaining <= 30 && remaining > 0 && !showWarning) {
        setShowWarning(true);
      }
      
      // Simula expiração da sessão
      if (remaining <= 0 && !sessionExpired) {
        setSessionExpired(true);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [lastActivity, showWarning, sessionExpired]);

  // Função para simular atividade do usuário
  const simulateUserActivity = () => {
    setLastActivity(Date.now());
    setShowWarning(false);
    setSessionExpired(false);
    setTimeRemaining(300);
  };

  // Função para simular inatividade acelerada (para testes)
  const simulateInactivity = () => {
    // Simula 4 minutos e 40 segundos de inatividade
    setLastActivity(Date.now() - 280000);
  };

  return (
    <div className="p-6 max-w-lg mx-auto bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Teste de Expiração de Sessão</h2>
      
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <p className="font-semibold">Status da Sessão:</p>
        {sessionExpired ? (
          <p className="text-red-600 font-bold">SESSÃO EXPIRADA - Redirecionando para login...</p>
        ) : (
          <p>Ativa - Tempo restante: {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}</p>
        )}
      </div>
      
      <div className="flex space-x-4 mb-6">
        <button 
          onClick={simulateUserActivity}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Simular Atividade do Usuário
        </button>
        
        <button 
          onClick={simulateInactivity}
          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
        >
          Simular Inatividade (4:40)
        </button>
      </div>
      
      <div className="bg-gray-100 p-4 rounded">
        <h3 className="font-semibold mb-2">Instruções de Teste:</h3>
        <ol className="list-decimal pl-5 space-y-2">
          <li>O timer começa em 5:00 minutos e diminui a cada segundo</li>
          <li>Quando faltar 30 segundos, um aviso será exibido</li>
          <li>Quando o timer chegar a 0:00, a sessão expira</li>
          <li>Clique em "Simular Atividade" para reiniciar o timer</li>
          <li>Clique em "Simular Inatividade" para avançar o timer para 4:40 (faltando 20 segundos para o aviso)</li>
        </ol>
      </div>
      
      {/* Modal de aviso */}
      {showWarning && !sessionExpired && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4">Aviso de Inatividade</h3>
            <p className="mb-6">
              Sua sessão está prestes a expirar devido à inatividade. 
              Clique em qualquer lugar ou pressione qualquer tecla para continuar.
            </p>
            <div className="flex justify-end">
              <button
                onClick={simulateUserActivity}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg"
              >
                Continuar Sessão
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestSessionTimeout;
