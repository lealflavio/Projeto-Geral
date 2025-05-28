from notificacoes import (
    enviar_mensagem_whatsapp,
    mensagem_boas_vindas,
    mensagem_inicio_processamento,
    mensagem_sucesso,
    mensagem_erro
)

# --- Interfaces públicas (simplificadas para o sistema principal) ---

def enviar_notificacao_boas_vindas(numero_whatsapp, nome_tecnico, link_drive):
    mensagem = mensagem_boas_vindas(nome_tecnico, link_drive)
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