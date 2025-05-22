import React, { useState, useEffect } from "react";
import axios from "axios";
import { Settings, Check, X, Eye, EyeOff, RefreshCw } from "lucide-react";

const Toast = ({ show, onClose, message }) => {
  if (!show) return null;
  return (
    <div className="fixed top-6 left-1/2 z-50 -translate-x-1/2">
      <div className="bg-primary text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-fade-in">
        <span>{message}</span>
        <button onClick={onClose} className="ml-2 hover:text-background text-white">
          <X size={18} />
        </button>
      </div>
    </div>
  );
};

const Perfil = () => {
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
  const [editandoPortal, setEditandoPortal] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);

  // Toast
  const [toast, setToast] = useState({ show: false, message: "" });

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
        setUsuarioPortal(data.usuario_portal || "");
      } catch (error) {
        setToast({ show: true, message: "Erro ao carregar dados do usuário." });
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
      setToast({ show: true, message: "WhatsApp atualizado com sucesso!" });
    } catch (error) {
      setToast({ show: true, message: "Erro ao atualizar WhatsApp." });
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
      setToast({ show: true, message: "Senha atualizada com sucesso!" });
    } catch (error) {
      setToast({ show: true, message: "Erro ao atualizar senha." });
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
      setUsuario((u) => ({ ...u, integrado: true, usuario_portal: usuarioPortal }));
      setEditandoPortal(false);
      setSenhaPortal("");
      setToast({
        show: true,
        message: "Integração realizada com sucesso! Você ganhou 5 créditos para processar WOs 🎉",
      });
    } catch (error) {
      setToast({ show: true, message: "Falha na integração." });
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
      <Toast show={toast.show} message={toast.message} onClose={() => setToast({ show: false, message: "" })} />
      <div className="w-full max-w-md space-y-6">
        {/* Card único */}
        <div className="bg-card p-6 rounded-2xl shadow-md">
          <h2 className="text-2xl font-semibold text-text mb-4 text-center">Perfil</h2>
          {/* Dados do usuário */}
          <div className="space-y-4">
            {/* Nome */}
            <div>
              <label className="block text-sm text-muted">Nome</label>
              <p className="font-medium text-text">{usuario.nome_completo || usuario.nome || "-"}</p>
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
            {/* Integração K1 */}
            <div>
              <label className="block text-sm text-muted mb-1">Portal K1</label>
              {!usuario.integrado && !editandoPortal && (
                <div className="flex flex-col gap-2">
                  <p className="text-muted text-sm">
                    Ganhe <span className="text-primary font-bold">5 créditos</span> ao integrar sua conta com o portal K1.
                  </p>
                  <button
                    type="button"
                    className="bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90 transition mt-2"
                    onClick={() => setEditandoPortal(true)}
                  >
                    Integrar agora
                  </button>
                </div>
              )}
              {(editandoPortal || !usuario.integrado) && (
                editandoPortal && (
                  <form onSubmit={handleIntegrar} className="space-y-3 mt-2">
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
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="flex-1 bg-primary text-white py-2 rounded-lg font-semibold hover:bg-primary/90 transition"
                      >
                        Salvar
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditandoPortal(false)}
                        className="flex-1 bg-secondary text-muted py-2 rounded-lg font-semibold hover:bg-danger/10 transition"
                      >
                        Cancelar
                      </button>
                    </div>
                  </form>
                )
              )}
              {usuario.integrado && !editandoPortal && (
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-medium text-text">{usuario.usuario_portal}</span>
                  <button
                    type="button"
                    className="ml-2 flex items-center gap-1 px-3 py-1 bg-primary text-white rounded-full hover:bg-primary/90 transition text-sm"
                    onClick={() => setEditandoPortal(true)}
                  >
                    <RefreshCw size={16} /> Atualizar dados do portal
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      {/* Animação para toast */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-20px);}
          to { opacity: 1; transform: translateY(0);}
        }
        .animate-fade-in { animation: fade-in 0.3s ease; }
      `}</style>
    </div>
  );
};

export default Perfil;
