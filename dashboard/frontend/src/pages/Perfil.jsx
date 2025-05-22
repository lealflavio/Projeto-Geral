import React, { useState } from "react";
import { Lock, Phone, User } from "lucide-react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Perfil = () => {
  // Simulação dos dados do usuário (troque pelo fetch real)
  const usuario = {
    nome: "João Silva",
    email: "joao@exemplo.com",
    whatsapp: "912345678",
    integrado: false,
    usuario_portal: "",
    senha_portal: "",
  };

  const navigate = useNavigate();
  const [editando, setEditando] = useState(false);
  const [novaSenha, setNovaSenha] = useState("");
  const [whatsapp, setWhatsapp] = useState(usuario.whatsapp);
  const [integrado, setIntegrado] = useState(usuario.integrado);
  const [mostrarFormIntegracao, setMostrarFormIntegracao] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState(usuario.usuario_portal || "");
  const [senhaPortal, setSenhaPortal] = useState(usuario.senha_portal || "");

  // Atualizar dados do perfil
  const handleSalvarPerfil = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.put(
        `${apiUrl}/usuarios/atualizar`,
        {
          whatsapp,
          senha: novaSenha,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      alert("Perfil atualizado com sucesso!");
      setEditando(false);
      // Atualize o estado global do usuário aqui, se necessário
    } catch (error) {
      alert("Erro ao atualizar perfil.");
    }
  };

  // Integração ou atualização dos dados do portal
  const handleIntegrar = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.put(
        `${apiUrl}/usuarios/integrar`,
        {
          usuario_portal: usuarioPortal,
          senha_portal: senhaPortal,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      alert(
        integrado
          ? "Dados do portal atualizados com sucesso!"
          : "Integração realizada com sucesso! Você ganhou 5 créditos para processar WOs 🎉"
      );
      setIntegrado(true);
      setMostrarFormIntegracao(false);
      // Atualize o estado global do usuário aqui, se necessário
    } catch (error) {
      alert("Falha na integração");
    }
  };

  return (
    <div className="space-y-6 bg-background min-h-screen py-8">
      <h1 className="text-xl font-semibold text-text">Perfil</h1>

      {/* Card: Informações básicas */}
      <div className="bg-card p-6 rounded-2xl shadow space-y-4">
        <div>
          <label className="text-sm text-muted">Nome</label>
          <p className="font-medium text-text">{usuario.nome}</p>
        </div>
        <div>
          <label className="text-sm text-muted">Email</label>
          <p className="font-medium text-text">{usuario.email}</p>
        </div>

        {!editando ? (
          <>
            <div>
              <label className="text-sm text-muted">WhatsApp</label>
              <p className="font-medium text-text">{whatsapp}</p>
            </div>
            <button
              onClick={() => setEditando(true)}
              className="w-full bg-primary text-card py-2 rounded-xl font-semibold hover:bg-opacity-90 transition"
            >
              Editar Perfil
            </button>
          </>
        ) : (
          <form onSubmit={handleSalvarPerfil} className="space-y-3">
            <div>
              <label className="block text-sm text-muted">WhatsApp</label>
              <input
                type="text"
                className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-muted">Nova Senha</label>
              <input
                type="password"
                className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                placeholder="Deixe em branco para não alterar"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 bg-primary text-card py-2 rounded-xl font-semibold hover:bg-opacity-90 transition"
              >
                Salvar
              </button>
              <button
                type="button"
                className="flex-1 bg-secondary text-text py-2 rounded-xl font-semibold hover:bg-muted transition"
                onClick={() => setEditando(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Card: Integração com o portal */}
      <div className="bg-card p-6 rounded-2xl shadow space-y-4">
        <div>
          <h2 className="text-base font-semibold text-text">Integração com o K1</h2>
          <p className="text-sm text-muted">
            {!integrado ? (
              <>
                <span className="font-semibold text-primary">
                  Ganhe 5 créditos
                </span>{" "}
                ao integrar sua conta com o portal K1. Use seus créditos para processar WOs e agilizar seu trabalho!<br />
                Conectando agora, você desbloqueia benefícios exclusivos e otimiza sua experiência.
              </>
            ) : (
              "Sua conta já está integrada ao portal K1. Aproveite seus créditos e utilize a integração sempre que precisar!"
            )}
          </p>
        </div>

        {/* Botão ou formulário de integração/atualização */}
        {!integrado && !mostrarFormIntegracao && (
          <button
            onClick={() => setMostrarFormIntegracao(true)}
            className="w-full bg-primary text-card py-2 rounded-xl font-semibold hover:bg-opacity-90 transition"
          >
            Integrar agora e ganhar 5 créditos
          </button>
        )}

        {((!integrado && mostrarFormIntegracao) || integrado) && (
          <form onSubmit={handleIntegrar} className="space-y-3">
            <div>
              <label className="block text-sm text-muted">Usuário Portal</label>
              <input
                type="text"
                className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                value={usuarioPortal}
                onChange={(e) => setUsuarioPortal(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-muted">Senha Portal</label>
              <input
                type="password"
                className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                value={senhaPortal}
                onChange={(e) => setSenhaPortal(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-primary text-card py-2 rounded-xl font-semibold hover:bg-opacity-90 transition"
            >
              {integrado ? "Atualizar dados do Portal" : "Integrar"}
            </button>
            {integrado && (
              <div className="text-xs text-muted mt-2">
                Você pode atualizar seus dados do portal a qualquer momento.
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
};

export default Perfil;
