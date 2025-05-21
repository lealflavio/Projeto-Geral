import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
// import { GoogleLogin } from '@react-oauth/google'; // Descomente quando integrar Google

const CadastroPage = () => {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [whatsapp, setWhatsapp] = useState("");
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [carregando, setCarregando] = useState(false);

  const navigate = useNavigate();

  const validarCampos = () => {
    if (nome.trim().length < 3) return "Nome deve ter pelo menos 3 caracteres.";
    if (!/\S+@\S+\.\S+/.test(email)) return "Email inválido.";
    if (senha.length < 6) return "Senha deve ter pelo menos 6 caracteres.";
    if (!/^\d{8,13}$/.test(whatsapp)) return "Número de WhatsApp inválido.";
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
        whatsapp,
      });
      if (response.status === 200 || response.status === 201) {
        setSucesso("Conta criada com sucesso! Redirecionando...");
        setTimeout(() => navigate("/"), 1800);
      }
    } catch (err) {
      let mensagem = "Erro ao criar conta. Verifique os dados e tente novamente.";
      if (err.response && err.response.data) {
        if (typeof err.response.data.detail === "string") {
          mensagem = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          mensagem = err.response.data.detail
            .map(item => {
              if (item.loc && item.msg) {
                return `${item.loc[item.loc.length - 1]}: ${item.msg}`;
              }
              return item.msg || JSON.stringify(item);
            })
            .join(" | ");
        } else if (err.response.data.message) {
          mensagem = err.response.data.message;
        } else {
          mensagem = JSON.stringify(err.response.data);
        }
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
          <div>
            <label className="block text-sm text-[#777]">WhatsApp</label>
            <input
              type="text"
              className="w-full mt-1 border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
              value={whatsapp}
              onChange={e => setWhatsapp(e.target.value.replace(/\D/g, ""))}
              placeholder="ex: 912345678"
              required
              inputMode="numeric"
              pattern="\d*"
              maxLength={13}
            />
          </div>

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
        <div className="my-4 flex flex-col items-center">
          <span className="text-gray-400 text-sm mb-2">Ou</span>
          {/* <GoogleLogin
            onSuccess={credentialResponse => {
              // Envie credentialResponse.credential ao backend
            }}
            onError={() => setErro("Falha ao autenticar com o Google.")}
            useOneTap
          /> */}
        </div>
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
