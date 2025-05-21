import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Lock, Mail, Phone, User, Eye, EyeOff } from "lucide-react";

const CadastroPage = () => {
  const navigate = useNavigate();
  const nomeRef = useRef(null);

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [whatsapp, setWhatsapp] = useState("");
  const [integrar, setIntegrar] = useState(false);
  const [usuarioPortal, setUsuarioPortal] = useState("");
  const [senhaPortal, setSenhaPortal] = useState("");
  const [mostrarSenhaPortal, setMostrarSenhaPortal] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [carregando, setCarregando] = useState(false);

  React.useEffect(() => {
    nomeRef.current && nomeRef.current.focus();
  }, []);

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

  // Campo com ícone, highlight e toggle para senha
  const InputWithIcon = ({
    label,
    icon,
    type,
    placeholder,
    value,
    onChange,
    inputRef,
    isPassword,
    mostrarSenha,
    setMostrarSenha,
    ...rest
  }) => (
    <div>
      <label className="block text-sm text-[#777]">{label}</label>
      <div className="relative flex items-center border border-gray-300 rounded-lg p-2 mt-1 focus-within:ring-2 focus-within:ring-[#7C3AED] transition-all bg-white">
        {icon}
        <input
          ref={inputRef}
          type={isPassword ? (mostrarSenha ? "text" : "password") : type}
          placeholder={placeholder}
          className="flex-1 outline-none text-sm bg-transparent pl-2"
          value={value}
          onChange={onChange}
          {...rest}
        />
        {isPassword && (
          <div
            onClick={() => setMostrarSenha(!mostrarSenha)}
            className="absolute right-3 cursor-pointer text-gray-500"
            tabIndex={0}
            role="button"
            aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
          >
            {mostrarSenha ? <EyeOff size={18} /> : <Eye size={18} />}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F9F9F9] px-4">
      <div className="bg-white p-6 rounded-2xl shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-semibold text-[#333] text-center mb-6">Criar Conta</h2>
        <form onSubmit={handleCadastro} className="space-y-4">

          <InputWithIcon
            label="Nome"
            icon={<User size={18} className="text-[#999]" />}
            type="text"
            placeholder="ex: João"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            inputRef={nomeRef}
            required
          />

          <InputWithIcon
            label="Email"
            icon={<Mail size={18} className="text-[#999]" />}
            type="email"
            placeholder="ex: joao@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <InputWithIcon
            label="Senha"
            icon={<Lock size={18} className="text-[#999]" />}
            type="password"
            placeholder="Mínimo 6 caracteres"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            isPassword
            mostrarSenha={mostrarSenha}
            setMostrarSenha={setMostrarSenha}
            required
          />

          {/* Toggle integração - switch colorido ao ativar */}
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

          {/* Campos extras condicionais */}
          {integrar && (
            <>
              <InputWithIcon
                label="Usuário do Portal"
                icon={<User size={18} className="text-[#999]" />}
                type="text"
                placeholder="ex: joao.silva"
                value={usuarioPortal}
                onChange={(e) => setUsuarioPortal(e.target.value)}
                required
              />

              <InputWithIcon
                label="Senha do Portal"
                icon={<Lock size={18} className="text-[#999]" />}
                type="password"
                placeholder="Sua senha do portal"
                value={senhaPortal}
                onChange={(e) => setSenhaPortal(e.target.value)}
                isPassword
                mostrarSenha={mostrarSenhaPortal}
                setMostrarSenha={setMostrarSenhaPortal}
                required
              />

              <InputWithIcon
                label="WhatsApp"
                icon={<Phone size={18} className="text-[#999]" />}
                type="text"
                placeholder="912345678"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
              />

              <p className="text-xs text-[#999] -mt-2">Poderá fazer mais tarde, se preferir.</p>
            </>
          )}

          {erro && <p className="text-red-500 text-sm">{erro}</p>}
          {sucesso && <p className="text-green-600 text-sm">{sucesso}</p>}

          <button
            type="submit"
            className="w-full bg-[#7C3AED] text-white py-2 rounded-lg font-semibold hover:bg-[#6B21A8] transition"
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
