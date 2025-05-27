import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    
    // Modo de desenvolvimento - bypass de autenticação para testes
    if (import.meta.env.DEV) {
      console.log("Modo de desenvolvimento: bypass de autenticação ativado");
      localStorage.setItem("authToken", "dev-token-for-testing");
      navigate("/dashboard");
      return;
    }
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL;
      const response = await axios.post(`${apiUrl}/auth/login`, {
        email: email,
        senha: senha,
      });

      const token = response.data.access_token;
      localStorage.setItem("authToken", token);
      navigate("/dashboard");
    } catch (err) {
      setErro("Email ou senha incorretos.");
    }
    setCarregando(false);
  };

  // Função para acesso direto ao dashboard em ambiente de desenvolvimento
  const acessarDashboardDev = () => {
    if (import.meta.env.DEV) {
      localStorage.setItem("authToken", "dev-token-for-testing");
      navigate("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="bg-card p-6 rounded-2xl shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-semibold text-text text-center mb-6">Login</h2>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-muted">Email</label>
            <input
              type="email"
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="relative">
            <label className="block text-sm text-muted">Senha</label>
            <input
              type={mostrarSenha ? "text" : "password"}
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
            <div
              onClick={() => setMostrarSenha(!mostrarSenha)}
              className="absolute right-3 top-8 cursor-pointer text-muted"
            >
              {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
            </div>
          </div>
          {erro && <p className="text-danger text-sm">{erro}</p>}
          <button
            type="submit"
            className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90"
            disabled={carregando}
          >
            {carregando ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <p className="text-sm text-center text-muted mt-2">
          <span
            className="text-primary hover:underline cursor-pointer"
            onClick={() => navigate("/esqueci-senha")}
          >
            Esqueceu a senha?
          </span>
        </p>
        <p className="text-sm text-center text-muted mt-4">
          Não tem uma conta?{" "}
          <span
            className="text-primary hover:underline cursor-pointer"
            onClick={() => navigate("/cadastro")}
          >
            Cadastre-se
          </span>
        </p>
        
        {/* Botão de acesso direto ao dashboard (apenas em ambiente de desenvolvimento) */}
        {import.meta.env.DEV && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={acessarDashboardDev}
              className="w-full bg-amber-500 text-white py-2 rounded-lg font-semibold hover:bg-amber-600"
            >
              Acessar Dashboard (Modo Dev)
            </button>
            <p className="text-xs text-center text-gray-500 mt-1">
              Este botão só aparece em ambiente de desenvolvimento
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
