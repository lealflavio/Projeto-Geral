import { createContext, useContext, useState } from 'react';

// Criar o contexto de autenticação
const AuthContext = createContext();

// Hook personalizado para usar o contexto
export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext deve ser usado dentro de um AuthProvider');
  }
  return context;
};

// Provedor do contexto
export const AuthProvider = ({ children }) => {
  // Estado para armazenar o token de autenticação
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || null);
  
  // Estado para armazenar informações do usuário
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : { 
      id: '1', 
      name: 'Técnico',
      email: 'tecnico@exemplo.com',
      role: 'technician'
    };
  });

  // Função para login
  const login = (token, userData) => {
    localStorage.setItem('authToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setAuthToken(token);
    setUser(userData);
  };

  // Função para logout
  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setAuthToken(null);
    setUser(null);
  };

  // Valor do contexto
  const value = {
    authToken,
    user,
    login,
    logout,
    isAuthenticated: !!authToken
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
