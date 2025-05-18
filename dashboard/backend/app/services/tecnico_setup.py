import os
import json
from pathlib import Path
from cryptography.fernet import Fernet

# Caminhos da VM
BASE_DIR = Path("/home/flavioleal_souza/Sistema/tecnicos")
CENTRAL_JSON = BASE_DIR / "tecnicos.json"
KEY_FILE = Path("/home/flavioleal_souza/Sistema/segredo.key")

# ID base do Google Drive (compartilhado)
GOOGLE_DRIVE_BASE = "https://drive.google.com/drive/folders/1TNTB2QBYBM94LU_52Cjqx69FeWHomY8G"

# Geração ou carregamento da chave de criptografia
def get_fernet():
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return Fernet(key)

# Função principal
def criar_estrutura_tecnico(nome_completo: str, email: str, usuario_portal: str, senha_portal: str):
    f = get_fernet()
    nome_formatado = nome_completo.replace(" ", "_")
    pasta_tecnico = BASE_DIR / nome_formatado

    # Cria pastas no sistema de arquivos (VM)
    os.makedirs(pasta_tecnico / "pdfs" / "novos", exist_ok=True)
    os.makedirs(pasta_tecnico / "pdfs" / "processados", exist_ok=True)
    os.makedirs(pasta_tecnico / "pdfs" / "erro", exist_ok=True)
    os.makedirs(pasta_tecnico / "logs", exist_ok=True)

    # Cria ou sobrescreve credenciais criptografadas
    credenciais = {
        "usuario_portal": usuario_portal,
        "senha_portal": f.encrypt(senha_portal.encode()).decode()
    }
    with open(pasta_tecnico / "credenciais.json", "w") as f_out:
        json.dump(credenciais, f_out, indent=2)

    # Atualiza tecnicos.json se o técnico ainda não existir
    tecnico_info = {
        "nome": nome_completo,
        "email": email,
        "usuario_portal": usuario_portal,
        "pasta_vm": str(pasta_tecnico),
        "pasta_drive": f"{GOOGLE_DRIVE_BASE}/{nome_formatado}/pdfs/novos"
    }

    if CENTRAL_JSON.exists():
        with open(CENTRAL_JSON, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
    else:
        data = []

    # Evita duplicações por email
    if not any(t["email"] == email for t in data):
        data.append(tecnico_info)
        with open(CENTRAL_JSON, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, indent=2, ensure_ascii=False)

    return True
