import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Settings, Check, X, Eye, EyeOff } from "lucide-react";

const Perfil = () => {
  const navigate = useNavigate();

  // Estado para dados do usuário
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);

  // Estados de edição
  const [editandoWhatsapp, setEditandoWhatsapp] = useState(false);
  const [novoWhatsapp, setNovoWhatsapp] = useState("");
  const [editandoSenha, setEditandoSenha] = useState(false);
  const [novaSenha, setNovaSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  // Integração K1
  const [integrado, setIntegrado] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);

  // Carregar dados do usuário ao montar
  useEffect(() => {
    const fetchUsuario = async () => {
      setCarregando(true);
      try {
        const token = localStorage.getItem("authToken");
        const apiUrl = import.meta.env.VITE_API_URL;
        const { data } = await axios.get(`${apiUrl}/usuarios/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsuario(data);
        setNovoWhatsapp(data.whatsapp || "");
        setIntegrado(!!data.integrado);
        setUsuarioPortal(data.usuario_portal || "");
      } catch (error) {
        alert("Erro ao carregar dados do usuário.");
      }
      setCarregando(false);
    };
    fetchUsuario();
  }, []);

  // Salvar WhatsApp
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

  // Salvar Senha
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
      setUsuario((u) => ({ ...u, integrado: true, usuario_portal: usuarioPortal }));
      alert("Integração realizada com sucesso! Você ganhou 5 créditos para processar WOs 🎉");
      setSenhaPortal("");
    } catch (error) {
      alert("Falha na integração");
    }
  };

  if (carregando) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="text-primary">Carregando...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center bg-background px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        {/* Card Integração */}
        <div className="bg-card p-6 rounded-2xl shadow-md">
          <h2 className="text-2xl font-semibold text-text mb-2 text-center">Integração com o K1</h2>
          <p className="text-center text-muted mb-4">
            Ganhe <span className="text-primary font-bold">5 créditos</span> ao integrar sua conta com o portal K1.
          </p>
          <form onSubmit={handleIntegrar} className="space-y-3">
            <div>
              <label className="block text-sm text-muted">Usuário Portal</label>
              <input
                type="text"
                className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                value={usuarioPortal}
                onChange={(e) => setUsuarioPortal(e.target.value)}
                required
                autoCapitalize="none"
                autoCorrect="off"
                autoComplete="username"
                spellCheck={false}
                inputMode="text"
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
              className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90 mt-2"
            >
              {integrado ? "Atualizar dados do Portal" : "Integrar agora"}
            </button>
            {integrado && (
              <div className="text-xs text-muted mt-2 text-center">
                Você já possui integração ativa e pode atualizar seus dados do portal a qualquer momento.
              </div>
            )}
          </form>
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
            <div>
              <label className="block text-sm text-muted">WhatsApp</label>
              <div className="flex items-center gap-2">
                {!editandoWhatsapp ? (
                  <>
                    <span className="font-medium text-text">{usuario.whatsapp}</span>
                    <button
                      type="button"
                      title="Editar"
                      onClick={() => setEditandoWhatsapp(true)}
                      className="ml-2 p-1 rounded hover:bg-primary/10 transition"
                    >
                      <Settings size={18} className="text-primary" />
                    </button>
                  </>
                ) : (
                  <>
                    <input
                      type="text"
                      className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                      value={novoWhatsapp}
                      onChange={(e) => setNovoWhatsapp(e.target.value)}
                    />
                    <button
                      type="button"
                      title="Salvar"
                      onClick={handleSalvarWhatsapp}
                      className="ml-2 p-1 rounded hover:bg-primary bg-primary text-white transition"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      type="button"
                      title="Cancelar"
                      onClick={() => {
                        setNovoWhatsapp(usuario.whatsapp);
                        setEditandoWhatsapp(false);
                      }}
                      className="ml-1 p-1 rounded hover:bg-danger/20 text-danger transition"
                    >
                      <X size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>
            {/* Senha */}
            <div>
              <label className="block text-sm text-muted">Senha</label>
              <div className="flex items-center gap-2">
                {!editandoSenha ? (
                  <>
                    <span className="font-medium text-muted">********</span>
                    <button
                      type="button"
                      title="Alterar senha"
                      onClick={() => setEditandoSenha(true)}
                      className="ml-2 p-1 rounded hover:bg-primary/10 transition"
                    >
                      <Settings size={18} className="text-primary" />
                    </button>
                  </>
                ) : (
                  <>
                    <input
                      type={mostrarSenha ? "text" : "password"}
                      className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                      value={novaSenha}
                      onChange={(e) => setNovaSenha(e.target.value)}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      title={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
                      onClick={() => setMostrarSenha((v) => !v)}
                      className="ml-1 p-1 rounded hover:bg-primary/10 text-muted transition"
                    >
                      {mostrarSenha ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                    <button
                      type="button"
                      title="Salvar"
                      onClick={handleSalvarSenha}
                      className="ml-2 p-1 rounded hover:bg-primary bg-primary text-white transition"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      type="button"
                      title="Cancelar"
                      onClick={() => {
                        setNovaSenha("");
                        setEditandoSenha(false);
                      }}
                      className="ml-1 p-1 rounded hover:bg-danger/20 text-danger transition"
                    >
                      <X size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Perfil;
