from twilio.rest import Client
import logging

# --- Configurações do Twilio ---

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# --- Envio genérico de mensagens via WhatsApp ---
def enviar_mensagem_whatsapp(numero_destino, mensagem, tipo_log=None, numero_wo=None):
    try:
        client.messages.create(
            body=mensagem,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{numero_destino}"
        )
        if tipo_log and numero_wo:
            logging.info(f"[WO {numero_wo}] Notificação de {tipo_log} enviada para {numero_destino}")
        elif tipo_log:
            logging.info(f"Notificação de {tipo_log} enviada para {numero_destino}")
        else:
            logging.info(f"Mensagem enviada com sucesso para {numero_destino}")
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para {numero_destino}: {e}")

# --- Mensagens formatadas ---
def mensagem_boas_vindas(nome_completo):
    return f"""
👋 Olá, {nome_completo}!

Você foi registrado no sistema automático da Wondercom.  
A partir de agora, receberá atualizações sobre suas WOs por aqui.

Em caso de dúvidas, fale com o suporte.
"""

def mensagem_inicio_processamento(nome_completo, numero_wo, dados):
    tipo = dados.get("tipo_intervencao", "-")
    data = dados.get("data_inicio", "-")
    hora = dados.get("hora_inicio", "-")

    equipamentos = dados.get("equipamentos_entregues", [])
    materiais = dados.get("materiais_usados", [])

    equipamentos_formatado = "\n".join([f"• {linha.strip()}" for linha in equipamentos]) or "Nenhum"
    materiais_formatado = "\n".join([f"• {linha.strip()}" for linha in materiais]) or "Nenhum"

    return f"""
⚙️ Início do processamento da WO {numero_wo}

Técnico: {nome_completo}  
Tipo: {tipo}  
Data: {data} às {hora}

📦 Equipamentos entregues:  
{equipamentos_formatado}

🧰 Materiais usados:  
{materiais_formatado}
"""

def mensagem_sucesso(numero_wo):
    return f"""
✅ Sucesso na WO {numero_wo}!

Todos os dados foram extraídos corretamente e estão prontos para envio.
"""

def mensagem_erro(numero_wo):
    return f"""
⚠️ Erro ao processar a WO {numero_wo}.

Não foi possível extrair os dados corretamente.  
Revise o PDF e tente novamente.

Se precisar de ajuda, fale com o suporte.
"""

# --- Interfaces públicas ---
def enviar_notificacao_boas_vindas(numero_whatsapp, nome_tecnico):
    mensagem = mensagem_boas_vindas(nome_tecnico)
    enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="boas-vindas")

def enviar_notificacao_wo_iniciada(numero_whatsapp, nome_tecnico, numero_wo, dados_intervencao):
    mensagem = mensagem_inicio_processamento(nome_tecnico, numero_wo, dados_intervencao)
    enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="início", numero_wo=numero_wo)

def enviar_notificacao_wo_sucesso(numero_whatsapp, numero_wo):
    mensagem = mensagem_sucesso(numero_wo)
    enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="sucesso", numero_wo=numero_wo)

def enviar_notificacao_wo_erro(numero_whatsapp, numero_wo):
    mensagem = mensagem_erro(numero_wo)
    enviar_mensagem_whatsapp(numero_whatsapp, mensagem, tipo_log="erro", numero_wo=numero_wo)
