import os
from flask import Flask, request
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Carregar a chave de serviço da variável de ambiente
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Escopos necessários para acessar o Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Função para autenticar com o Google Drive
def autenticar_drive():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# Função para baixar o PDF
def baixar_pdf(drive_service, file_id, file_name):
    request = drive_service.files().get_media(fileId=file_id)
    with open(file_name, 'wb') as f:
        request.execute(fd=f)

# Rota para receber as notificações
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if 'fileId' in data:
        file_id = data['fileId']
        file_name = data['fileName']
        
        drive_service = autenticar_drive()
        baixar_pdf(drive_service, file_id, file_name)
        return "OK", 200
    return "Erro", 400

if __name__ == '__main__':
    # Rodar na porta 5001
    app.run(port=5001)
