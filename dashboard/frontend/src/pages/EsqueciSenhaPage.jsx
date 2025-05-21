import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const EsqueciSenhaPage = () => {
  const [email, setEmail] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const navigate = useNavigate();

  const handleEnviar = async (e) => {
    e.preventDefault();
    setMensagem("");
    setErro("");
    setCarregando(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.post(`${apiUrl}/auth/forgot-password`, { email });
      setMensagem("Se o e-mail estiver cadastrado, enviaremos as instruções para recuperação.");
    } catch (err) {
      setErro("Erro ao solicitar recuperação. Tente novamente.");
    }
    setCarregando(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="bg-card p-6 rounded-2xl shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-semibold text-text text-center mb-6">Recuperar Senha</h2>
        <form onSubmit={handleEnviar} className="space-y-4">
          <div>
            <label className="block text-sm text-muted">E-mail</label>
            <input
              type="email"
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          {mensagem && <p className="text-green-600 text-sm">{mensagem}</p>}
          {erro && <p className="text-danger text-sm">{erro}</p>}
          <button
            type="submit"
            className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90"
            disabled={carregando}
          >
            {carregando ? "Enviando..." : "Enviar instruções"}
          </button>
        </form>
        <p className="text-sm text-center text-muted mt-4">
          <span
            className="text-primary hover:underline cursor-pointer"
            onClick={() => navigate("/")}
          >
            Voltar para o login
          </span>
        </p>
      </div>
    </div>
  );
};

export default EsqueciSenhaPage;
