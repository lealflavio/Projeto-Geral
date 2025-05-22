import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Settings, Eye, EyeOff } from "lucide-react";

const Perfil = () => {
  const navigate = useNavigate();

  // Simule fetch do usuário, substitua pelo seu fetch real
  const [usuario, setUsuario] = useState({
    nome: "João Silva",
    email: "joao@exemplo.com",
    whatsapp: "912345678",
    integrado: false,
    usuario_portal: "",
    // senha_portal: "",
  });

  const [editandoWhatsapp, setEditandoWhatsapp] = useState(false);
  const [novoWhatsapp, setNovoWhatsapp] = useState(usuario.whatsapp);

  const [editandoSenha, setEditandoSenha] = useState(false);
  const [novaSenha, setNovaSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  const [integrado, setIntegrado] = useState(usuario.integrado);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);

  // Atualize os campos caso usuário venha do fetch
  useEffect(() => {
    setNovoWhatsapp(usuario.whatsapp || "");
    setIntegrado(usuario.integrado || false);
    setUsuarioPortal(usuario.usuario_portal || "");
    // setSenhaPortal(usuario.senha_portal || "");
  }, [usuario]);

  // Salvar apenas o campo alterado
  const handleSalvarWhatsapp = async () => {
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.put(
        `${apiUrl}/usuarios/atualizar`,
        { whatsapp: novoWhatsapp },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setUsuario((u) => ({ ...u, whatsapp: novoWhatsapp }));
      setEditandoWhatsapp(false);
      alert("WhatsApp atualizado com sucesso!");
    } catch (error) {
      alert("Erro ao atualizar WhatsApp.");
    }
  };

  const handleSalvarSenha = async () => {
    try {
      if (!novaSenha) return;
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.put(
        `${apiUrl}/usuarios/atualizar`,
        { senha: novaSenha },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNovaSenha("");
      setEditandoSenha(false);
      alert("Senha atualizada com sucesso!");
    } catch (error) {
      alert("Erro ao atualizar senha.");
    }
  };

  // Integração com o portal K1
  const handleIntegrar = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      await axios.put(
        `${apiUrl}/usuarios/integrar`,
        { usuario_portal: usuarioPortal, senha_portal: senhaPortal },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIntegrado(true);
      setUsuario((u) => ({ ...u, integrado: true }));
      alert("Integração realizada com sucesso! Você ganhou 5 créditos para processar WOs 🎉");
      setSenhaPortal("");
    } catch (error) {
      alert("Falha na integração");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center bg-background px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        {/* Card Integração */}
        <div className="bg-card p-6 rounded-2xl shadow-md">
          <h2 className="text-2xl font-semibold text-text mb-2 text-center">Integração com o K1</h2>
          <p className="text-center text-muted mb-4">
            Ganhe <span className="text-primary font-bold">5 créditos</span> ao integrar sua conta com o portal K1.
          </p>
          {!integrado && (
            <form onSubmit={handleIntegrar} className="space-y-3">
              <div>
                <label className="block text-sm text-muted">Usuário Portal</label>
                <input
                  type="text"
                  className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                  value={usuarioPortal}
                  onChange={(e) => setUsuarioPortal(e.target.value)}
                  required
                  autoComplete="username"
                />
              </div>
              <div className="relative">
                <label className="block text-sm text-muted">Senha Portal</label>
                <input
                  type={mostrarSenhaPortal ? "text" : "password"}
                  className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                  value={senhaPortal}
                  onChange={(e) => setSenhaPortal(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <div
                  onClick={() => setMostrarSenhaPortal((v) => !v)}
                  className="absolute right-3 top-8 cursor-pointer text-muted"
                  title={mostrarSenhaPortal ? "Ocultar senha" : "Mostrar senha"}
                >
                  {mostrarSenhaPortal ? <EyeOff size={18} /> : <Eye size={18} />}
                </div>
              </div>
              <button
                type="submit"
                className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90"
              >
                Integrar agora
              </button>
            </form>
          )}
          {integrado && (
            <div className="text-center">
              <div className="text-primary font-bold text-lg mb-2">
                Conta já integrada!
              </div>
              <div className="text-muted text-sm mb-2">
                Você já possui integração ativa e pode atualizar seus dados do portal a qualquer momento.
              </div>
              <form onSubmit={handleIntegrar} className="space-y-3 mt-2">
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
                <div className="relative">
                  <label className="block text-sm text-muted">Senha Portal</label>
                  <input
                    type={mostrarSenhaPortal ? "text" : "password"}
                    className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                    value={senhaPortal}
                    onChange={(e) => setSenhaPortal(e.target.value)}
                    required
                  />
                  <div
                    onClick={() => setMostrarSenhaPortal((v) => !v)}
                    className="absolute right-3 top-8 cursor-pointer text-muted"
                  >
                    {mostrarSenhaPortal ? <EyeOff size={18} /> : <Eye size={18} />}
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90"
                >
                  Atualizar dados do Portal
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Card Perfil */}
        <div className="bg-card p-6 rounded-2xl shadow-md">
          <h2 className="text-xl font-semibold text-text mb-4 text-center">Perfil</h2>
          <div className="space-y-4">
            {/* Nome */}
            <div>
              <label className="block text-sm text-muted">Nome</label>
              <p className="font-medium text-text">{usuario.nome}</p>
            </div>
            {/* Email */}
            <div>
              <label className="block text-sm text-muted">Email</label>
              <p className="font-medium text-text">{usuario.email}</p>
            </div>
            {/* WhatsApp */}
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-sm text-muted">WhatsApp</label>
                {!editandoWhatsapp ? (
                  <p className="font-medium text-text">{usuario.whatsapp}</p>
                ) : (
                  <input
                    type="text"
                    className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                    value={novoWhatsapp}
                    onChange={(e) => setNovoWhatsapp(e.target.value)}
                  />
                )}
              </div>
              <button
                type="button"
                title={editandoWhatsapp ? "Salvar" : "Alterar"}
                onClick={() => {
                  if (editandoWhatsapp) {
                    handleSalvarWhatsapp();
                  } else {
                    setEditandoWhatsapp(true);
                  }
                }}
                className={`p-2 rounded-full transition ${
                  editandoWhatsapp
                    ? "bg-primary text-white hover:bg-primary/90"
                    : "bg-secondary text-muted hover:bg-primary/10"
                }`}
              >
                <Settings size={18} />
              </button>
              {editandoWhatsapp && (
                <button
                  type="button"
                  title="Cancelar"
                  onClick={() => {
                    setNovoWhatsapp(usuario.whatsapp);
                    setEditandoWhatsapp(false);
                  }}
                  className="ml-1 p-2 rounded-full bg-secondary text-muted hover:bg-danger/10 transition"
                >
                  X
                </button>
              )}
            </div>
            {/* Senha */}
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-sm text-muted">Senha</label>
                {!editandoSenha ? (
                  <p className="font-medium text-muted">********</p>
                ) : (
                  <input
                    type={mostrarSenha ? "text" : "password"}
                    className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                    value={novaSenha}
                    onChange={(e) => setNovaSenha(e.target.value)}
                    autoComplete="new-password"
                  />
                )}
              </div>
              <button
                type="button"
                title={editandoSenha ? "Salvar" : "Alterar"}
                onClick={() => {
                  if (editandoSenha) {
                    handleSalvarSenha();
                  } else {
                    setEditandoSenha(true);
                  }
                }}
                className={`p-2 rounded-full transition ${
                  editandoSenha
                    ? "bg-primary text-white hover:bg-primary/90"
                    : "bg-secondary text-muted hover:bg-primary/10"
                }`}
              >
                <Settings size={18} />
              </button>
              {editandoSenha && (
                <>
                  <button
                    type="button"
                    title="Cancelar"
                    onClick={() => {
                      setNovaSenha("");
                      setEditandoSenha(false);
                    }}
                    className="ml-1 p-2 rounded-full bg-secondary text-muted hover:bg-danger/10 transition"
                  >
                    X
                  </button>
                  <button
                    type="button"
                    onClick={() => setMostrarSenha((v) => !v)}
                    className="ml-1 p-2 rounded-full bg-secondary text-muted hover:bg-primary/10 transition"
                    title={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Perfil;
