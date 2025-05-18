import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Lock, Mail, Phone, User } from "lucide-react";

const CadastroPage = () => {
  const navigate = useNavigate();

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [integrar, setIntegrar] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  const handleCadastro = async (e) => {
    e.preventDefault();
    setErro("");
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
        navigate("/");
      }
    } catch (err) {
      console.error(err);
      setErro("Erro ao criar conta. Verifique os dados e tente novamente.");
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
            <div className="flex items-center border rounded-xl p-2">
              <User size={18} className="text-[#999] mr-2" />
              <input
                type="text"
                placeholder="ex: João"
                className="flex-1 outline-none text-sm"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-[#777]">Email</label>
            <div className="flex items-center border rounded-xl p-2">
              <Mail size={18} className="text-[#999] mr-2" />
              <input
                type="email"
                placeholder="ex: joao@email.com"
                className="flex-1 outline-none text-sm"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-[#777]">Senha</label>
            <div className="flex items-center border rounded-xl p-2">
              <Lock size={18} className="text-[#999] mr-2" />
              <input
                type="password"
                placeholder="Mínimo 6 caracteres"
                className="flex-1 outline-none text-sm"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Toggle integração */}
          <div className="flex items-center justify-between py-2">
            <label className="text-sm text-[#777]">Integrar com o portal K1?</label>
            <div
              onClick={() => setIntegrar(!integrar)}
              className={`w-12 h-6 flex items-center rounded-full p-1 cursor-pointer transition-all duration-300 ${
                integrar ? "bg-[#7C3AED] justify-end" : "bg-gray-300 justify-start"
              }`}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </div>
          </div>

          {/* Campos extras condicionais */}
          {integrar && (
            <>
              <div>
                <label className="block text-sm text-[#777]">Usuário do Portal</label>
                <div className="flex items-center border rounded-xl p-2">
                  <User size={18} className="text-[#999] mr-2" />
                  <input
                    type="text"
                    placeholder="ex: joao.silva"
                    className="flex-1 outline-none text-sm"
                    value={usuarioPortal}
                    onChange={(e) => setUsuarioPortal(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-[#777]">Senha do Portal</label>
                <div className="flex items-center border rounded-xl p-2">
                  <Lock size={18} className="text-[#999] mr-2" />
                  <input
                    type="password"
                    placeholder="Sua senha do portal"
                    className="flex-1 outline-none text-sm"
                    value={senhaPortal}
                    onChange={(e) => setSenhaPortal(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-[#777]">WhatsApp</label>
                <div className="flex items-center border rounded-xl p-2">
                  <Phone size={18} className="text-[#999] mr-2" />
                  <input
                    type="text"
                    placeholder="912345678"
                    className="flex-1 outline-none text-sm"
                    value={whatsapp}
                    onChange={(e) => setWhatsapp(e.target.value)}
                  />
                </div>
              </div>

              <p className="text-xs text-[#999] -mt-2">Poderá fazer mais tarde, se preferir.</p>
            </>
          )}

          {erro && <p className="text-red-500 text-sm">{erro}</p>}

          <button
            type="submit"
            className="w-full bg-[#7C3AED] text-white py-2 rounded-xl font-semibold hover:bg-[#6B21A8] transition"
            disabled={carregando}
          >
            {carregando ? "Criando..." : "Criar Conta"}
          </button>
        </form>

        <p className="text-sm text-center text-[#777] mt-4">
          Já tem uma conta?{' '}
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
