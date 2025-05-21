import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, User, Mail, Lock, Phone } from "lucide-react";

const CadastroPage = () => {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  const [integrar, setIntegrar] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);
  const [whatsapp, setWhatsapp] = useState("");

  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [carregando, setCarregando] = useState(false);

  const navigate = useNavigate();

  const validarCampos = () => {
    if (nome.trim().length < 3) return "Nome deve ter pelo menos 3 caracteres.";
    if (!/\S+@\S+\.\S+/.test(email)) return "Email inválido.";
    if (senha.length < 6) return "Senha deve ter pelo menos 6 caracteres.";
    if (integrar) {
      if (!usuarioPortal.trim()) return "Usuário do portal é obrigatório.";
      if (!senhaPortal.trim()) return "Senha do portal é obrigatória.";
      if (whatsapp && !/^\d{8,13}$/.test(whatsapp)) return "WhatsApp inválido.";
    }
    return null;
  };

  const handleCadastro = async (e) => {
    e.preventDefault();
    setErro("");
    setSucesso("");

    const erroValidacao = validarCampos();
    if (erroValidacao) {
      setErro(erroValidacao);
      return;
    }

    setCarregando(true);
    try {
      const response = await axios.post("http://localhost:8000/auth/register", {
        nome_completo: nome,
        email,
        senha,
        whatsapp: integrar ? whatsapp : "",
        usuario_portal: integrar ? usuarioPortal : "",
        senha_portal: integrar ? senhaPortal : "",
      });

      if (response.status === 200 || response.status === 201) {
        setSucesso("Conta criada com sucesso! Redirecionando...");
        setTimeout(() => navigate("/"), 1800);
      }
    } catch (err) {
      let mensagem = "Erro ao criar conta. Verifique os dados e tente novamente.";
      if (err.response && err.response.data && err.response.data.detail) {
        mensagem = err.response.data.detail;
      }
      setErro(mensagem);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F9F9F9] px-4">
      <div className="bg-white p-6 rounded-2xl shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-semibold text-[#333] text-center mb-6">Criar Conta</h2>
        <form onSubmit={handleCadastro} className="space-y-4">
          <div>
            <label className="block text-sm text-[#777]">Nome</label>
            <input
              type="text"
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm text-[#777]">Email</label>
            <input
              type="email"
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="relative">
            <label className="block text-sm text-[#777]">Senha</label>
            <input
              type={mostrarSenha ? "text" : "password"}
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
            <div
              onClick={() => setMostrarSenha(!mostrarSenha)}
              className="absolute right-3 top-8 cursor-pointer text-gray-500"
              style={{top: 38}}
            >
              {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
            </div>
          </div>

          {/* Toggle integração */}
          <div className="flex items-center justify-between py-2">
            <label className="text-sm text-[#777]">Integrar com o portal K1?</label>
            <button
              type="button"
              onClick={() => setIntegrar(!integrar)}
              className={`w-12 h-6 flex items-center rounded-full p-1 cursor-pointer transition-all duration-300 border-none focus:outline-none
                ${integrar ? "bg-[#7C3AED]" : "bg-gray-300"}
              `}
              style={{ justifyContent: integrar ? "flex-end" : "flex-start" }}
              aria-pressed={integrar}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </button>
          </div>

          {integrar && (
            <>
              <div>
                <label className="block text-sm text-[#777]">Usuário do Portal</label>
                <input
                  type="text"
                  className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
                  value={usuarioPortal}
                  onChange={(e) => setUsuarioPortal(e.target.value)}
                  required
                />
              </div>
              <div className="relative">
                <label className="block text-sm text-[#777]">Senha do Portal</label>
                <input
                  type={mostrarSenhaPortal ? "text" : "password"}
                  className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
                  value={senhaPortal}
                  onChange={(e) => setSenhaPortal(e.target.value)}
                  required
                />
                <div
                  onClick={() => setMostrarSenhaPortal(!mostrarSenhaPortal)}
                  className="absolute right-3 top-8 cursor-pointer text-gray-500"
                  style={{top: 38}}
                >
                  {mostrarSenhaPortal ? <EyeOff size={18} /> : <Eye size={18} />}
                </div>
              </div>
              <div>
                <label className="block text-sm text-[#777]">WhatsApp</label>
                <input
                  type="text"
                  className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
                  value={whatsapp}
                  onChange={(e) => setWhatsapp(e.target.value)}
                  placeholder="912345678"
                />
                <p className="text-xs text-[#999] -mt-2">Poderá fazer mais tarde, se preferir.</p>
              </div>
            </>
          )}

          {erro && <p className="text-red-500 text-sm">{erro}</p>}
          {sucesso && <p className="text-green-600 text-sm">{sucesso}</p>}

          <button
            type="submit"
            className="w-full bg-[#7C3AED] text-white py-2 rounded-lg font-semibold hover:bg-[#6B21A8]"
            disabled={carregando}
          >
            {carregando ? "Criando..." : "Criar Conta"}
          </button>
        </form>
        <p className="text-sm text-center text-[#777] mt-4">
          Já tem uma conta?{" "}
          <span
            className="text-[#7C3AED] hover:underline cursor-pointer"
            onClick={() => navigate("/")}
          >
            Faça login
          </span>
        </p>
      </div>
    </div>
  );
};

export default CadastroPage;
