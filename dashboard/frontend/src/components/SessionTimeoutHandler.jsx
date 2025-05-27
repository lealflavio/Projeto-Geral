import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const INACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutos em milissegundos
const WARNING_TIMEOUT = 4.5 * 60 * 1000; // Aviso 30 segundos antes da expiração

const SessionTimeoutHandler = ({ children }) => {
  const navigate = useNavigate();
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showWarning, setShowWarning] = useState(false);
  
  // Função para resetar o timer de inatividade
  const resetTimer = useCallback(() => {
    setLastActivity(Date.now());
    setShowWarning(false);
  }, []);

  // Função para fazer logout e redirecionar para a página de login
  const handleLogout = useCallback(() => {
    localStorage.removeItem('authToken');
    navigate('/', { replace: true });
  }, [navigate]);

  // Efeito para monitorar a inatividade
  useEffect(() => {
    // Verificar inatividade a cada segundo
    const interval = setInterval(() => {
      const now = Date.now();
      const timeSinceLastActivity = now - lastActivity;
      
      // Se passou do tempo de inatividade, faz logout
      if (timeSinceLastActivity >= INACTIVITY_TIMEOUT) {
        handleLogout();
      } 
      // Se está próximo do tempo de expiração, mostra aviso
      else if (timeSinceLastActivity >= WARNING_TIMEOUT && !showWarning) {
        setShowWarning(true);
      }
    }, 1000);

    // Limpa o intervalo quando o componente é desmontado
    return () => clearInterval(interval);
  }, [lastActivity, handleLogout, showWarning]);

  // Efeito para adicionar listeners de eventos de atividade do usuário
  useEffect(() => {
    // Lista de eventos para monitorar
    const events = [
      'mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart',
      'click', 'keydown', 'keyup'
    ];

    // Adiciona os listeners para cada evento
    const resetTimerFn = () => resetTimer();
    events.forEach(event => {
      window.addEventListener(event, resetTimerFn);
    });

    // Limpa os listeners quando o componente é desmontado
    return () => {
      events.forEach(event => {
        window.removeEventListener(event, resetTimerFn);
      });
    };
  }, [resetTimer]);

  return (
    <>
      {children}
      
      {/* Modal de aviso de expiração */}
      {showWarning && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4">Aviso de Inatividade</h3>
            <p className="mb-6">
              Sua sessão está prestes a expirar devido à inatividade. 
              Clique em qualquer lugar ou pressione qualquer tecla para continuar.
            </p>
            <div className="flex justify-end">
              <button
                onClick={resetTimer}
                className="bg-primary text-white px-4 py-2 rounded-lg"
              >
                Continuar Sessão
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SessionTimeoutHandler;
