import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Caminhos fixos
BASE_DIR = Path("/home/flavioleal/Sistema/tecnicos")
CENTRAL_JSON = BASE_DIR / "tecnicos.json"
KEY_FILE = Path("/home/flavioleal/Sistema/segredo.key")
SERVICE_ACCOUNT_FILE = "/home/flavioleal/Sistema/chave_servico_primaria.json"

# Autenticação Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# Pasta pai no Drive compartilhado
PASTA_PAI_DRIVE_ID = "1TNTB2QBYBM94LU_52Cjqx69FeWHomY8G"

# URL do endpoint Cloud Run para receber notificações
WEBHOOK_URL = "https://drive-webhook-1063112559876.europe-west1.run.app/webhook"

def get_fernet():
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return Fernet(key)

def criar_pasta_drive(nome, pai=None):
    file_metadata = {
        'name': nome,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if pai:
        file_metadata['parents'] = [pai]
    pasta = service.files().create(body=file_metadata, fields='id').execute()
    return pasta.get('id')

def registrar_webhook_pasta(pasta_id):
    canal = {
        "id": f"canal-{pasta_id}",  # pode ser qualquer string única
        "type": "web_hook",
        "address": WEBHOOK_URL
    }
    try:
        resposta = service.files().watch(fileId=pasta_id, body=canal).execute()
        print(f'Webhook registrado para a pasta {pasta_id}:')
        print(resposta)
    except Exception as e:
        print(f'Erro ao registrar webhook para {pasta_id}: {e}')

def criar_tecnico(nome_completo, email, usuario_portal, senha_portal):
    fernet = get_fernet()
    nome_formatado = nome_completo.replace(" ", "_")
    pasta_vm = BASE_DIR / nome_formatado

    # 1. Criar estrutura local
    os.makedirs(pasta_vm / "pdfs" / "novos", exist_ok=True)
    os.makedirs(pasta_vm / "pdfs" / "processados", exist_ok=True)
    os.makedirs(pasta_vm / "pdfs" / "erro", exist_ok=True)
    os.makedirs(pasta_vm / "logs", exist_ok=True)

    # 2. Criar estrutura no Google Drive
    id_pasta_tecnico = criar_pasta_drive(nome_formatado, pai=PASTA_PAI_DRIVE_ID)
    id_pasta_pdfs = criar_pasta_drive("pdfs", pai=id_pasta_tecnico)
    id_novos = criar_pasta_drive("novos", pai=id_pasta_pdfs)
    criar_pasta_drive("processados", pai=id_pasta_pdfs)
    criar_pasta_drive("erro", pai=id_pasta_pdfs)

    # *** NOVO: Registra webhook na pasta 'novos' ***
    registrar_webhook_pasta(id_novos)

    # 3. Criar credenciais criptografadas
    credenciais = {
        "usuario_portal": usuario_portal,
        "senha_portal": fernet.encrypt(senha_portal.encode()).decode()
    }
    with open(pasta_vm / "credenciais.json", "w") as f_out:
        json.dump(credenciais, f_out, indent=2)

    # 4. Atualizar tecnicos.json
    tecnico_info = {
        "nome": nome_completo,
        "email": email,
        "usuario_portal": usuario_portal,
        "pasta_vm": str(pasta_vm),
        "pasta_drive_id": id_pasta_tecnico,
        "pasta_novos_id": id_novos
    }

    if CENTRAL_JSON.exists():
        with open(CENTRAL_JSON, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
    else:
        data = []

    # Evita duplicação
    if not any(t["email"] == email for t in data):
        data.append(tecnico_info)
        with open(CENTRAL_JSON, "w", encoding="utf-8") as f_out:
            json.dump(data, f_out, indent=2, ensure_ascii=False)

    return True