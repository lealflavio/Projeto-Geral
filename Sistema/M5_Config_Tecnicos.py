import os
import json
from cryptography.fernet import Fernet

# --- Caminhos ---
CONFIG_DIR = "/home/flavioleal_souza/Sistema/config"
CHAVE_PATH = os.path.join(CONFIG_DIR, "chave.key")
JSON_TECNICOS_PATH = os.path.join(CONFIG_DIR, "tecnicos.json")

# --- Funções de criptografia ---
def gerar_chave():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    chave = Fernet.generate_key()
    with open(CHAVE_PATH, "wb") as f:
        f.write(chave)
    print("Chave de criptografia gerada com sucesso.")

def carregar_fernet():
    if not os.path.exists(CHAVE_PATH):
        print("Chave de criptografia não encontrada. Execute gerar_chave() primeiro.")
        return None
    with open(CHAVE_PATH, "rb") as f:
        chave = f.read()
    return Fernet(chave)

def criptografar_senha(senha, fernet):
    return fernet.encrypt(senha.encode()).decode()

# --- Cadastro de técnico ---
def cadastrar_tecnico(username, nome_completo, whatsapp, usuario_portal, senha_portal):
    fernet = carregar_fernet()
    if fernet is None:
        return

    senha_criptografada = criptografar_senha(senha_portal, fernet)

    novo_tecnico = {
        "nome_completo": nome_completo,
        "whatsapp": whatsapp,
        "usuario_portal": usuario_portal,
        "senha_portal_criptografada": senha_criptografada,
        "ativo": True
    }

    if os.path.exists(JSON_TECNICOS_PATH):
        with open(JSON_TECNICOS_PATH, "r", encoding="utf-8") as f:
            tecnicos = json.load(f)
    else:
        tecnicos = {}

    tecnicos[username] = novo_tecnico

    with open(JSON_TECNICOS_PATH, "w", encoding="utf-8") as f:
        json.dump(tecnicos, f, indent=2, ensure_ascii=False)

    print(f"Técnico '{nome_completo}' cadastrado com sucesso!")

# --- Execução direta para testes ---
if __name__ == "__main__":
    # Para uso manual: descomente para gerar a chave inicialmente
    # gerar_chave()

    cadastrar_tecnico(
        username="Teste",
        nome_completo="Flávio Leal",
        whatsapp="+351937059712",
        usuario_portal="flavio.leal",
        senha_portal="SENHA_SEGURA"
    )
