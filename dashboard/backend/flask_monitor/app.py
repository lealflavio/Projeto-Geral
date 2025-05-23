from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Só loga os cabeçalhos da notificação recebida do Google Drive
    print("Notificação recebida do Google Drive!")
    print("Headers:")
    for k, v in request.headers.items():
        print(f"{k}: {v}")
    # Você pode salvar essas infos em banco, enviar mensagem, etc. MAS NÃO BAIXA ARQUIVO NENHUM!
    return "OK", 200

if __name__ == '__main__':
    app.run(port=5001, host="0.0.0.0")
