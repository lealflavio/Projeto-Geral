import React, { useState } from "react";
import { Lock, Phone, User } from "lucide-react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Perfil = () => {
  const usuario = {
    nome: "João Silva",
    email: "joao@exemplo.com",
    whatsapp: "912345678",
    integrado: false,
  };

  const navigate = useNavigate();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [whatsapp, setWhatsapp] = useState(usuario.whatsapp || "");

  const handleIntegrar = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem("authToken");
      await axios.put(
        "http://localhost:8000/usuarios/integrar",
        {
          usuario_portal: usuarioPortal,
          senha_portal: senhaPortal,
          whatsapp: whatsapp,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("Integração realizada com sucesso!");
      navigate("/dashboard");
    } catch (error) {
      console.error("Erro ao integrar:", error);
      alert("Falha na integração");
    }
  };

  const handleEditarPerfil = () => {
    alert("Função de edição de perfil ainda será implementada.");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#333]">Perfil</h1>

      {/* Card: Informações básicas */}
      <div className="bg-white p-6 rounded-2xl shadow space-y-4">
        <div>
          <label className="text-sm text-[#777]">Nome</label>
          <p className="font-medium text-[#333]">{usuario.nome}</p>
        </div>
        <div>
          <label className="text-sm text-[#777]">Email</label>
          <p className="font-medium text-[#333]">{usuario.email}</p>
        </div>
        <div>
          <label className="text-sm text-[#777]">WhatsApp</label>
          <p className="font-medium text-[#333]">{usuario.whatsapp}</p>
        </div>
        <button
          onClick={handleEditarPerfil}
          className="w-full bg-[#7C3AED] text-white py-2 rounded-xl font-semibold hover:bg-[#6B21A8] transition"
        >
          Editar Perfil
        </button>
      </div>

      {/* Card: Integração com o portal */}
      <div className="bg-white p-6 rounded-2xl shadow space-y-4">
        <div>
          <h2 className="text-base font-semibold text-[#333]">Integração com o K1</h2>
          <p className="text-sm text-[#777]">
            {usuario.integrado
              ? "Conta já integrada com o portal."
              : "Integre sua conta e comece a aproveitar agora mesmo!"}
          </p>
        </div>

        {!usuario.integrado && !mostrarFormulario && (
          <button
            onClick={() => setMostrarFormulario(true)}
            className="w-full bg-[#7C3AED] text-white py-2 rounded-xl font-semibold hover:bg-[#6B21A8] transition"
          >
            Integrar agora
          </button>
        )}

        {mostrarFormulario && (
          <form onSubmit={handleIntegrar} className="space-y-3 mt-2">
            <div>
              <label className="block text-sm text-[#555] mb-1">Usuário do Portal</label>
              <div className="flex items-center border rounded-xl p-2">
                <User size={18} className="text-[#999] mr-2" />
                <input
                  type="text"
                  placeholder="ex: joao.silva"
                  className="flex-1 outline-none text-sm"
                  value={usuarioPortal}
                  onChange={(e) => setUsuarioPortal(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-[#555] mb-1">Senha do Portal</label>
              <div className="flex items-center border rounded-xl p-2">
                <Lock size={18} className="text-[#999] mr-2" />
                <input
                  type="password"
                  placeholder="Sua senha do portal"
                  className="flex-1 outline-none text-sm"
                  value={senhaPortal}
                  onChange={(e) => setSenhaPortal(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-[#555] mb-1">WhatsApp</label>
              <div className="flex items-center border rounded-xl p-2">
                <Phone size={18} className="text-[#999] mr-2" />
                <input
                  type="text"
                  placeholder="912345678"
                  className="flex-1 outline-none text-sm"
                  onChange={(e) => setWhatsapp(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#7C3AED] text-white py-2 rounded-xl font-semibold hover:bg-[#6B21A8] transition"
            >
              Salvar integração
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Perfil;
