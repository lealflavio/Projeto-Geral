import subprocess
import logging
import re
import os
import json

# Função de extração do valor após um rótulo específico
def extrair_valor_apos_rotulo(texto, rotulo):
    match = re.search(rf"{rotulo}\s*[:\-]?\s*(.*?)(?=\s+[A-Za-z]|$)", texto)
    return match.group(1).strip() if match else None

# Função para extrair uma seção inteira do texto (multi-linha)
def extrair_secao_multilinha(texto, inicio, fim=None):
    try:
        if fim:
            match = re.search(rf"{inicio}(.*?){fim}", texto, re.DOTALL)
        else:
            match = re.search(rf"{inicio}(.*?)\Z", texto, re.DOTALL)

        return match.group(1).strip() if match else None
    except Exception as e:
        logging.error(f"Erro ao extrair seção {inicio}: {e}")
        return None

# Função para extrair os equipamentos entregues
def extrair_equipamentos(texto):
    equipamentos = []
    linhas = texto.splitlines()
    for linha in linhas:
        # Ajuste para pegar a descrição do equipamento e serial number
        if "Serial Number" in linha:
            equipamentos.append(" ".join(linha.split()))
    return equipamentos

# Função para extrair os materiais
def extrair_materiais(texto):
    materiais = []
    linhas = texto.splitlines()
    for linha in linhas:
        if linha.strip() and len(linha.split()) > 1:
            # Limpeza para garantir que não haja espaços extras
            campos = linha.split()
            # Garantir que o valor da quantidade seja um número inteiro, sem casas decimais
            try:
                descricao = " ".join(campos[:-1])
                quantidade = float(campos[-1])
                # Se quantidade for um número inteiro, removemos a parte decimal
                if quantidade.is_integer():
                    quantidade = int(quantidade)
                materiais.append(f"{descricao} {quantidade}")
            except ValueError:
                continue  # Se não conseguir converter para número, ignora a linha
    return materiais


# Função principal para extrair dados de um PDF
def extrair_dados_pdf_relevantes(caminho_pdf):
    dados_relevantes = {
        "dados_intervencao": {},
        "observacoes_tecnico": None,
        "equipamentos_entregues": [],
        "materiais_usados": []
    }

    try:
        process = subprocess.run(["pdftotext", "-layout", caminho_pdf, "-"], capture_output=True, text=True, check=True, encoding='utf-8')
        texto_completo = process.stdout
    except FileNotFoundError:
        logging.error("Comando pdftotext não encontrado. Verifique se poppler-utils está instalado e no PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar pdftotext para {caminho_pdf}: {e}. Output: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao processar {caminho_pdf} com pdftotext: {e}")
        return None

    # Extrair Dados da Intervenção
    dados_relevantes["dados_intervencao"]["numero_intervencao"] = extrair_valor_apos_rotulo(texto_completo, "Nº")
    dados_relevantes["dados_intervencao"]["tipo_intervencao"] = extrair_valor_apos_rotulo(texto_completo, "Tipo de Intervenção")
    dados_relevantes["dados_intervencao"]["data_inicio"] = extrair_valor_apos_rotulo(texto_completo, "Data de Início")
    dados_relevantes["dados_intervencao"]["hora_inicio"] = extrair_valor_apos_rotulo(texto_completo, "Hora de Início")
    dados_relevantes["dados_intervencao"]["data_fim"] = extrair_valor_apos_rotulo(texto_completo, "Data de Fim")
    dados_relevantes["dados_intervencao"]["hora_fim"] = extrair_valor_apos_rotulo(texto_completo, "Hora de Fim")

    # Extrair Observações do Técnico
    dados_relevantes["observacoes_tecnico"] = extrair_secao_multilinha(texto_completo, "Observações do Técnico", "Equipamentos")
    if not dados_relevantes["observacoes_tecnico"]:
         dados_relevantes["observacoes_tecnico"] = extrair_secao_multilinha(texto_completo, "Observações do Técnico", "Questionário do cliente")
    if not dados_relevantes["observacoes_tecnico"]:
         dados_relevantes["observacoes_tecnico"] = extrair_secao_multilinha(texto_completo, "Observações do Técnico")

    # Extrair Equipamentos Entregues
    secao_equipamentos_texto = extrair_secao_multilinha(texto_completo, "Equipamentos", "Materiais")
    if not secao_equipamentos_texto:
        secao_equipamentos_texto = extrair_secao_multilinha(texto_completo, "Equipamentos", "Questionário do cliente")
    if not secao_equipamentos_texto:
        secao_equipamentos_texto = extrair_secao_multilinha(texto_completo, "Equipamentos")
        
    if secao_equipamentos_texto:
        match_entregues = re.search(r"Entregues(.*?)(Recolhidos|\Z|Materiais|Questionário do cliente)", secao_equipamentos_texto, re.DOTALL | re.IGNORECASE)
        if match_entregues:
            texto_equip_entregues = match_entregues.group(1).strip()
            dados_relevantes["equipamentos_entregues"] = extrair_equipamentos(texto_equip_entregues)
        else:
            dados_relevantes["equipamentos_entregues"] = extrair_equipamentos(secao_equipamentos_texto)

    # Extrair Materiais Usados
    secao_materiais_texto = extrair_secao_multilinha(texto_completo, "Materiais", "Questionário do cliente")
    if not secao_materiais_texto:
        secao_materiais_texto = extrair_secao_multilinha(texto_completo, "Materiais")
        
    if secao_materiais_texto:
        dados_relevantes["materiais_usados"] = extrair_materiais(secao_materiais_texto)

    # Limpar chaves vazias em dados_intervencao
    dados_relevantes["dados_intervencao"] = {k: v for k, v in dados_relevantes["dados_intervencao"].items() if v is not None}

    # Criar diretório para salvar os arquivos se não existir
    saida_dir = "/home/flavioleal_souza/Sistema/extracao_dados"
    os.makedirs(saida_dir, exist_ok=True)

    # Salvar os dados extraídos em um arquivo JSON
    nome_pdf = os.path.basename(caminho_pdf).replace('.pdf', '')
    caminho_saida = os.path.join(saida_dir, f"{nome_pdf}_dados.json")
    
    with open(caminho_saida, "w", encoding="utf-8") as f_out:
        json.dump(dados_relevantes, f_out, indent=2, ensure_ascii=False)
    
    logging.info(f"Dados extraídos salvos em: {caminho_saida}")
    return dados_relevantes
