import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Settings, Check, X, Eye, EyeOff, RefreshCw, ExternalLink, FolderOpen } from "lucide-react";
import { useAuthContext } from "../context/AuthContext";

const Toast = ({ show, message, buttonText, onButton }) => {
  if (!show) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Fundo desfocado */}
      <div className="absolute inset-0 bg-black bg-opacity-40 backdrop-blur-sm transition-opacity"></div>
      {/* Toast */}
      <div className="relative bg-white border border-primary rounded-2xl shadow-xl p-8 z-10 flex flex-col items-center min-w-[320px] animate-fade-in">
        <span className="text-text text-center text-lg mb-4">{message}</span>
        <button
          onClick={onButton}
          className="bg-primary text-white px-6 py-2 rounded-lg font-semibold hover:bg-primary/90 transition text-base mx-auto"
        >
          {buttonText}
        </button>
      </div>
      {/* Animação */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-20px);}
          to { opacity: 1; transform: translateY(0);}
        }
        .animate-fade-in { animation: fade-in 0.35s cubic-bezier(.4,0,.2,1); }
      `}</style>
    </div>
  );
};

// Função de validação do usuário portal no formato nome.sobrenome (minúsculas, sem acento, só letras, sempre ponto)
function validarUsuarioPortal(valor) {
  return /^[a-z]+\.[a-z]+$/.test(valor);
}

const Perfil = () => {
  const navigate = useNavigate();
  // Estado do usuário
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);
  
  // Contexto de autenticação para atualizar credenciais globalmente
  const { login } = useAuthContext();

  // Edição dos dados
  const [editandoWhatsapp, setEditandoWhatsapp] = useState(false);
  const [novoWhatsapp, setNovoWhatsapp] = useState("");
  const [editandoSenha, setEditandoSenha] = useState(false);
  const [novaSenha, setNovaSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);

  // Integração Portal K1
  const [editandoPortal, setEditandoPortal] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);
  
  // Link da pasta no Drive
  const [pastaLink, setPastaLink] = useState("");

  // Toast
  const [toast, setToast] = useState({ show: false, message: "", buttonText: "" });

  // Carregar dados do usuário
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
        
        // Verificar se o usuário tem link da pasta
        if (data.pasta_novos_link) {
          setPastaLink(data.pasta_novos_link);
        } else if (data.usuario_portal) {
          // Se o usuário está integrado mas não tem o link, buscar o link
          fetchPastaLink(data.usuario_portal);
        }
      } catch (error) {
        setToast({
          show: true,
          message: "Erro ao carregar dados do usuário.",
          buttonText: "Tentar novamente",
          onButton: () => window.location.reload(),
        });
      }
      setCarregando(false);
    };
    fetchUsuario();
  }, []);
  
  // Buscar link da pasta do usuário
  const fetchPastaLink = async (userPortal) => {
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      const { data } = await axios.get(`${apiUrl}/folders/status`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { usuario_portal: userPortal }
      });
      
      if (data.status === "success" && data.exists && data.user_data?.novos_folder_link) {
        setPastaLink(data.user_data.novos_folder_link);
        
        // Atualizar o usuário local com o link da pasta
        setUsuario(prev => ({
          ...prev,
          pasta_novos_link: data.user_data.novos_folder_link
        }));
      }
    } catch (error) {
      console.error("Erro ao buscar link da pasta:", error);
    }
  };

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
      setToast({
        show: true,
        message: "WhatsApp atualizado com sucesso!",
        buttonText: "OK",
      });
    } catch (error) {
      setToast({
        show: true,
        message: "Erro ao atualizar WhatsApp.",
        buttonText: "Tentar novamente",
      });
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
      setToast({
        show: true,
        message: "Senha atualizada com sucesso!",
        buttonText: "OK",
      });
    } catch (error) {
      setToast({
        show: true,
        message: "Erro ao atualizar senha.",
        buttonText: "Tentar novamente",
      });
    }
  };

  // Função para tratar input do usuário portal (apenas minúsculas, ponto e letras)
  const handleUsuarioPortalChange = (e) => {
    const value = e.target.value.replace(/[^a-z.]/g, "");
    setUsuarioPortal(value);
  };

  // Integração com o portal K1
  const handleIntegrar = async (e) => {
    e.preventDefault();
    if (!validarUsuarioPortal(usuarioPortal)) {
      setToast({
        show: true,
        message: "O usuário do portal deve ser no formato nome.apelido. Se nao for o seu caso, contacte o suporte.",
        buttonText: "OK"
      });
      return;
    }
    try {
      const token = localStorage.getItem("authToken");
      const apiUrl = import.meta.env.VITE_API_URL;
      const response = await axios.put(
        `${apiUrl}/usuarios/integrar`,
        { usuario_portal: usuarioPortal, senha_portal: senhaPortal },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Verificar se a resposta contém o link da pasta
      if (response.data && response.data.pasta_novos_link) {
        setPastaLink(response.data.pasta_novos_link);
      } else {
        // Se não tiver o link, buscar após um tempo para dar tempo de criar as pastas
        setTimeout(() => fetchPastaLink(usuarioPortal), 5000);
      }
      
      // Atualizar o estado local do usuário
      const usuarioAtualizado = { 
        ...usuario, 
        integrado: true, 
        usuario_portal: usuarioPortal,
        senha_portal: senhaPortal, // Garantir que a senha também seja armazenada
        pasta_novos_link: response.data?.pasta_novos_link || ""
      };
      
      setUsuario(usuarioAtualizado);
      
      // IMPORTANTE: Atualizar o contexto global de autenticação e localStorage
      // Isso garante que as credenciais estejam disponíveis em toda a aplicação
      const userDataString = localStorage.getItem('user');
      if (userDataString) {
        const userData = JSON.parse(userDataString);
        const updatedUserData = {
          ...userData,
          usuario_portal: usuarioPortal,
          senha_portal: senhaPortal
        };
        
        // Atualizar localStorage
        localStorage.setItem('user', JSON.stringify(updatedUserData));
        
        // Atualizar contexto global usando a função login do AuthContext
        login(token, updatedUserData);
        
        // Disparar evento de storage para garantir sincronização entre abas
        window.dispatchEvent(new Event('storage'));
        
        console.log("Credenciais do portal atualizadas globalmente:", {
          usuario: usuarioPortal,
          senha: senhaPortal ? "Configurada" : "Não configurada"
        });
      }
      
      setEditandoPortal(false);
      setSenhaPortal("");
      setToast({
        show: true,
        message: "Integração realizada com sucesso! Você ganhou 5 créditos para processar WOs 🎉",
        buttonText: "Ir para o Dashboard",
      });
    } catch (error) {
      setToast({
        show: true,
        message: "Falha na integração.",
        buttonText: "Tentar novamente",
      });
    }
  };

  // Abrir pasta no Drive
  const abrirPastaDrive = () => {
    if (pastaLink) {
      window.open(pastaLink, '_blank');
    }
  };

  // Fechar toast e ação do botão
  const handleToastButton = () => {
    setToast({ show: false, message: "", buttonText: "" });
    if (toast.buttonText === "Ir para o Dashboard") {
      navigate("/dashboard");
    }
  };

  // Lógica para saber se o usuário está integrado
  const estaIntegrado =
    usuario && usuario.usuario_portal && usuario.usuario_portal.trim() !== "";

  if (carregando) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="text-primary">Carregando...</span>
      </div>
    );
  }

  // Layout antes da integração (dois cards)
  if (!estaIntegrado) {
    return (
      <div className="min-h-screen flex flex-col items-center bg-background px-4 py-8">
        <Toast
          show={toast.show}
          message={toast.message}
          buttonText={toast.buttonText}
          onButton={handleToastButton}
        />
        <div className="w-full max-w-md space-y-6">
          {/* Card Integração */}
          <div className="bg-card p-6 rounded-2xl shadow-md border-2 border-primary">
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
                  onChange={handleUsuarioPortalChange}
                  required
                  autoComplete="off"
                  autoCorrect="off"
                  spellCheck={false}
                  autoCapitalize="none"
                  inputMode="text"
                  placeholder="ex: joao.silva"
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
                  autoComplete="off"
                  autoCorrect="off"
                  spellCheck={false}
                  placeholder="sua senha"
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
          </div>
          {/* Card Perfil */}
          <div className="bg-card p-6 rounded-2xl shadow-md">
            <h2 className="text-xl font-semibold text-text mb-4 text-center">Perfil</h2>
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
            </div>
          </div>
        </div>
        {/* Toast animation (mantém para consistência visual) */}
        <style>{`
          @keyframes fade-in {
            from { opacity: 0; transform: translateY(-20px);}
            to { opacity: 1; transform: translateY(0);}
          }
          .animate-fade-in { animation: fade-in 0.3s cubic-bezier(.4,0,.2,1);}
        `}</style>
      </div>
    );
  }

  // Layout após integração (um card unificado)
  return (
    <div className="min-h-screen flex flex-col items-center bg-background px-4 py-8">
      <Toast
        show={toast.show}
        message={toast.message}
        buttonText={toast.buttonText}
        onButton={handleToastButton}
      />
      <div className="w-full max-w-md">
        <div className="bg-card p-6 rounded-2xl shadow-md border-primary border-2">
          <h2 className="text-2xl font-semibold text-text mb-4 text-center">Perfil e Integração K1</h2>
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
            {/* Portal K1 */}
            <div>
              <label className="block text-sm text-muted mb-1">Portal K1</label>
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
              {editandoPortal && (
                <form onSubmit={handleIntegrar} className="space-y-3 mt-2">
                  <div>
                    <label className="block text-sm text-muted">Usuário Portal</label>
                    <input
                      type="text"
                      className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-primary"
                      value={usuarioPortal}
                      onChange={handleUsuarioPortalChange}
                      required
                      autoComplete="off"
                      autoCorrect="off"
                      spellCheck={false}
                      autoCapitalize="none"
                      inputMode="text"
                      placeholder="ex: flavio.leal"
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
                      autoComplete="off"
                      autoCorrect="off"
                      spellCheck={false}
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
              )}
            </div>
            
            {/* Pasta no Drive - NOVO */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <label className="block text-sm text-muted mb-2">Sua Pasta no Drive</label>
              {pastaLink ? (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center">
                    <FolderOpen size={20} className="text-primary mr-2" />
                    <span className="text-sm text-text">Pasta para envio de arquivos</span>
                  </div>
                  <button
                    onClick={abrirPastaDrive}
                    className="flex items-center justify-center gap-2 bg-primary text-white py-2 px-4 rounded-lg hover:bg-primary/90 transition w-full"
                  >
                    <ExternalLink size={18} />
                    Abrir Pasta no Drive
                  </button>
                  <p className="text-xs text-muted mt-1 text-center">
                    Envie seus arquivos para esta pasta para processamento automático
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 p-3 bg-gray-50 rounded-lg">
                  <RefreshCw size={20} className="text-muted animate-spin" />
                  <p className="text-sm text-muted">Buscando informações da sua pasta...</p>
                </div>
              )}
            </div>
          </div>
        </div>
        <style>{`
          @keyframes fade-in {
            from { opacity: 0; transform: translateY(-20px);}
            to { opacity: 1; transform: translateY(0);}
          }
          .animate-fade-in { animation: fade-in 0.3s cubic-bezier(.4,0,.2,1);}
          
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .animate-spin { animation: spin 1.5s linear infinite; }
        `}</style>
      </div>
    </div>
  );
};

export default Perfil;
