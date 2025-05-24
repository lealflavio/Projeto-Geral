#!/usr/bin/env python3
"""
Extrator Otimizado de Dados de PDFs de Intervenção

Este script extrai dados relevantes de PDFs de intervenção e os salva em formato JSON.
Utiliza PyMuPDF para processamento direto de PDFs, implementa estratégias robustas
de extração e validação de dados, e inclui mecanismos de diagnóstico.
"""

import os
import sys
import re
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
import fitz  # PyMuPDF

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extrator_pdf.log'))
    ]
)
logger = logging.getLogger('extrator_pdf_otimizado')

# Adicionar diretório raiz ao path para importação
try:
    # Determinar o diretório base do projeto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
except Exception as e:
    logger.error(f"Erro ao configurar path: {str(e)}")

# Importar utilitários de caminho
try:
    from config.path_utils import get_path, join_path, ensure_dir_exists
    USING_PATH_UTILS = True
except ImportError:
    logger.warning("Utilitários de caminho não encontrados. Usando caminhos padrão.")
    USING_PATH_UTILS = False
    # Definir caminho padrão para compatibilidade
    DEFAULT_EXTRACAO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extracao_dados")
    DEFAULT_DIAGNOSTICO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostico")

# Constantes para extração
PADROES_CAMPOS = {
    "numero_intervencao": [
        r"Nº\s*[:\-]?\s*(\w+)",
        r"Número\s*[:\-]?\s*(\w+)",
        r"Intervenção\s*[:\-]?\s*(\w+)"
    ],
    "tipo_intervencao": [
        r"Tipo de Intervenção\s*[:\-]?\s*(.*?)(?=\s+[A-Za-z]|$)",
        r"Tipo\s*[:\-]?\s*(.*?)(?=\s+[A-Za-z]|$)"
    ],
    "data_inicio": [
        r"Data de Início\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})",
        r"Data Início\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})"
    ],
    "hora_inicio": [
        r"Hora de Início\s*[:\-]?\s*(\d{2}:\d{2})",
        r"Hora Início\s*[:\-]?\s*(\d{2}:\d{2})"
    ],
    "data_fim": [
        r"Data de Fim\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})",
        r"Data Fim\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})"
    ],
    "hora_fim": [
        r"Hora de Fim\s*[:\-]?\s*(\d{2}:\d{2})",
        r"Hora Fim\s*[:\-]?\s*(\d{2}:\d{2})"
    ]
}

PADROES_SECOES = {
    "observacoes_tecnico": [
        (r"Observações do Técnico", r"Equipamentos"),
        (r"Observações do Técnico", r"Questionário do cliente"),
        (r"Observações do Técnico", None)
    ],
    "equipamentos": [
        (r"Equipamentos", r"Materiais"),
        (r"Equipamentos", r"Questionário do cliente"),
        (r"Equipamentos", None)
    ],
    "materiais": [
        (r"Materiais", r"Questionário do cliente"),
        (r"Materiais", None)
    ]
}

class ExtratorPDF:
    """Classe para extração de dados de PDFs de intervenção técnica."""
    
    def __init__(self, caminho_pdf: str):
        """
        Inicializa o extrator com o caminho do PDF.
        
        Args:
            caminho_pdf: Caminho absoluto para o arquivo PDF
        """
        self.caminho_pdf = caminho_pdf
        self.nome_pdf = os.path.basename(caminho_pdf).replace('.pdf', '')
        self.texto_completo = ""
        self.paginas_texto = []
        self.doc = None
        self.tempo_inicio = time.time()
        self.diagnostico_info = {
            "nome_arquivo": self.nome_pdf,
            "timestamp": datetime.now().isoformat(),
            "tempo_processamento": 0,
            "sucesso": False,
            "erros": [],
            "avisos": []
        }
        
        # Diretórios para saída
        if USING_PATH_UTILS:
            self.saida_dir = join_path('extracao_dados_dir', create=True)
            self.diagnostico_dir = join_path('diagnostico_dir', create=True)
        else:
            self.saida_dir = DEFAULT_EXTRACAO_DIR
            self.diagnostico_dir = DEFAULT_DIAGNOSTICO_DIR
            os.makedirs(self.saida_dir, exist_ok=True)
            os.makedirs(self.diagnostico_dir, exist_ok=True)
    
    def __enter__(self):
        """Método para uso com context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha recursos ao sair do context manager."""
        if self.doc:
            self.doc.close()
        
        # Registrar tempo de processamento
        self.diagnostico_info["tempo_processamento"] = time.time() - self.tempo_inicio
        
        # Salvar informações de diagnóstico
        self._salvar_diagnostico()
    
    def extrair_dados(self) -> Dict[str, Any]:
        """
        Extrai todos os dados relevantes do PDF.
        
        Returns:
            Dicionário com os dados extraídos
        """
        try:
            self._carregar_pdf()
            
            dados_relevantes = {
                "dados_intervencao": {},
                "observacoes_tecnico": None,
                "equipamentos_entregues": [],
                "materiais_usados": []
            }
            
            # Extrair dados de intervenção
            for campo, padroes in PADROES_CAMPOS.items():
                valor = self._extrair_campo_com_fallback(padroes)
                if valor:
                    dados_relevantes["dados_intervencao"][campo] = valor
            
            # Extrair observações do técnico
            dados_relevantes["observacoes_tecnico"] = self._extrair_secao_com_fallback("observacoes_tecnico")
            
            # Extrair equipamentos entregues
            secao_equipamentos = self._extrair_secao_com_fallback("equipamentos")
            if secao_equipamentos:
                dados_relevantes["equipamentos_entregues"] = self._extrair_equipamentos(secao_equipamentos)
            
            # Extrair materiais usados
            secao_materiais = self._extrair_secao_com_fallback("materiais")
            if secao_materiais:
                dados_relevantes["materiais_usados"] = self._extrair_materiais(secao_materiais)
            
            # Validar dados extraídos
            self._validar_dados(dados_relevantes)
            
            # Salvar dados em JSON
            self._salvar_dados(dados_relevantes)
            
            # Marcar como sucesso
            self.diagnostico_info["sucesso"] = True
            
            return dados_relevantes
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do PDF {self.nome_pdf}: {str(e)}")
            self.diagnostico_info["erros"].append(str(e))
            return None
    
    def _carregar_pdf(self) -> None:
        """Carrega o PDF e extrai o texto completo."""
        try:
            # Abrir o documento PDF
            self.doc = fitz.open(self.caminho_pdf)
            
            # Extrair texto de cada página
            self.paginas_texto = []
            for pagina in self.doc:
                self.paginas_texto.append(pagina.get_text())
            
            # Concatenar todo o texto
            self.texto_completo = "\n".join(self.paginas_texto)
            
            logger.info(f"PDF carregado com sucesso: {self.nome_pdf} ({len(self.doc)} páginas)")
        except Exception as e:
            logger.error(f"Erro ao carregar PDF {self.nome_pdf}: {str(e)}")
            self.diagnostico_info["erros"].append(f"Erro ao carregar PDF: {str(e)}")
            raise
    
    def _extrair_campo_com_fallback(self, padroes: List[str]) -> Optional[str]:
        """
        Tenta extrair um campo usando múltiplos padrões como fallback.
        
        Args:
            padroes: Lista de padrões regex para tentar
            
        Returns:
            Valor extraído ou None se não encontrado
        """
        for padrao in padroes:
            match = re.search(padrao, self.texto_completo)
            if match:
                return match.group(1).strip()
        return None
    
    def _extrair_secao_com_fallback(self, tipo_secao: str) -> Optional[str]:
        """
        Extrai uma seção de texto usando múltiplos padrões como fallback.
        
        Args:
            tipo_secao: Tipo de seção a extrair (chave em PADROES_SECOES)
            
        Returns:
            Texto da seção ou None se não encontrado
        """
        if tipo_secao not in PADROES_SECOES:
            logger.warning(f"Tipo de seção desconhecido: {tipo_secao}")
            self.diagnostico_info["avisos"].append(f"Tipo de seção desconhecido: {tipo_secao}")
            return None
        
        for inicio, fim in PADROES_SECOES[tipo_secao]:
            try:
                if fim:
                    match = re.search(f"{inicio}(.*?){fim}", self.texto_completo, re.DOTALL)
                else:
                    match = re.search(f"{inicio}(.*?)\\Z", self.texto_completo, re.DOTALL)
                
                if match:
                    return match.group(1).strip()
            except Exception as e:
                logger.warning(f"Erro ao extrair seção {tipo_secao} com padrão {inicio}-{fim}: {str(e)}")
                self.diagnostico_info["avisos"].append(f"Erro ao extrair seção {tipo_secao}: {str(e)}")
        
        return None
    
    def _extrair_equipamentos(self, texto_secao: str) -> List[str]:
        """
        Extrai informações de equipamentos da seção correspondente.
        
        Args:
            texto_secao: Texto da seção de equipamentos
            
        Returns:
            Lista de equipamentos extraídos
        """
        equipamentos = []
        
        # Primeiro tenta encontrar a subseção "Entregues"
        match_entregues = re.search(r"Entregues(.*?)(Recolhidos|\Z|Materiais|Questionário do cliente)", 
                                   texto_secao, re.DOTALL | re.IGNORECASE)
        
        texto_para_processar = match_entregues.group(1).strip() if match_entregues else texto_secao
        
        # Processa linha por linha
        linhas = texto_para_processar.splitlines()
        for linha in linhas:
            # Verifica se a linha contém "Serial Number"
            if "Serial Number" in linha:
                equipamento = " ".join(linha.split())
                equipamentos.append(equipamento)
        
        return equipamentos
    
    def _extrair_materiais(self, texto_secao: str) -> List[str]:
        """
        Extrai informações de materiais da seção correspondente.
        
        Args:
            texto_secao: Texto da seção de materiais
            
        Returns:
            Lista de materiais extraídos
        """
        materiais = []
        
        # Processa linha por linha
        linhas = texto_secao.splitlines()
        for linha in linhas:
            if linha.strip() and len(linha.split()) > 1:
                try:
                    # Tenta extrair descrição e quantidade
                    campos = linha.split()
                    descricao = " ".join(campos[:-1])
                    quantidade = float(campos[-1])
                    
                    # Converte para inteiro se for número inteiro
                    if quantidade.is_integer():
                        quantidade = int(quantidade)
                    
                    materiais.append(f"{descricao} {quantidade}")
                except (ValueError, IndexError):
                    # Ignora linhas que não seguem o padrão esperado
                    continue
        
        return materiais
    
    def _validar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Valida os dados extraídos e registra avisos para campos problemáticos.
        
        Args:
            dados: Dicionário com os dados extraídos
        """
        # Validar dados de intervenção
        if not dados["dados_intervencao"].get("numero_intervencao"):
            logger.warning("Número de intervenção não encontrado")
            self.diagnostico_info["avisos"].append("Número de intervenção não encontrado")
        
        # Validar datas e horas
        for campo in ["data_inicio", "data_fim"]:
            valor = dados["dados_intervencao"].get(campo)
            if valor and not re.match(r"\d{2}[/-]\d{2}[/-]\d{4}", valor):
                logger.warning(f"Formato de data inválido para {campo}: {valor}")
                self.diagnostico_info["avisos"].append(f"Formato de data inválido para {campo}: {valor}")
        
        for campo in ["hora_inicio", "hora_fim"]:
            valor = dados["dados_intervencao"].get(campo)
            if valor and not re.match(r"\d{2}:\d{2}", valor):
                logger.warning(f"Formato de hora inválido para {campo}: {valor}")
                self.diagnostico_info["avisos"].append(f"Formato de hora inválido para {campo}: {valor}")
        
        # Validar observações do técnico
        if not dados["observacoes_tecnico"]:
            logger.warning("Observações do técnico não encontradas")
            self.diagnostico_info["avisos"].append("Observações do técnico não encontradas")
    
    def _salvar_dados(self, dados: Dict[str, Any]) -> None:
        """
        Salva os dados extraídos em um arquivo JSON.
        
        Args:
            dados: Dicionário com os dados extraídos
        """
        caminho_saida = os.path.join(self.saida_dir, f"{self.nome_pdf}_dados.json")
        
        with open(caminho_saida, "w", encoding="utf-8") as f_out:
            json.dump(dados, f_out, indent=2, ensure_ascii=False)
        
        logger.info(f"Dados extraídos salvos em: {caminho_saida}")
    
    def _salvar_diagnostico(self) -> None:
        """Salva informações de diagnóstico em um arquivo JSON."""
        caminho_diagnostico = os.path.join(self.diagnostico_dir, f"{self.nome_pdf}_diagnostico.json")
        
        with open(caminho_diagnostico, "w", encoding="utf-8") as f_out:
            json.dump(self.diagnostico_info, f_out, indent=2, ensure_ascii=False)
        
        logger.info(f"Informações de diagnóstico salvas em: {caminho_diagnostico}")
    
    def salvar_screenshot_pagina(self, num_pagina: int) -> str:
        """
        Salva um screenshot de uma página específica do PDF.
        
        Args:
            num_pagina: Número da página (0-indexed)
            
        Returns:
            Caminho para o arquivo de imagem salvo
        """
        if not self.doc:
            self._carregar_pdf()
        
        if num_pagina < 0 or num_pagina >= len(self.doc):
            logger.error(f"Número de página inválido: {num_pagina}")
            return None
        
        try:
            # Obter a página
            pagina = self.doc[num_pagina]
            
            # Renderizar a página como imagem
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Salvar a imagem
            caminho_imagem = os.path.join(self.diagnostico_dir, f"{self.nome_pdf}_pagina_{num_pagina}.png")
            pix.save(caminho_imagem)
            
            logger.info(f"Screenshot da página {num_pagina} salvo em: {caminho_imagem}")
            return caminho_imagem
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot da página {num_pagina}: {str(e)}")
            self.diagnostico_info["erros"].append(f"Erro ao salvar screenshot: {str(e)}")
            return None


def extrair_dados_pdf_relevantes(caminho_pdf: str) -> Dict[str, Any]:
    """
    Função principal para extrair dados de um PDF.
    
    Args:
        caminho_pdf: Caminho para o arquivo PDF
        
    Returns:
        Dicionário com os dados extraídos ou None em caso de erro
    """
    try:
        with ExtratorPDF(caminho_pdf) as extrator:
            # Salvar screenshot da primeira página para diagnóstico
            extrator.salvar_screenshot_pagina(0)
            
            # Extrair dados
            return extrator.extrair_dados()
    except Exception as e:
        logger.error(f"Erro ao processar {caminho_pdf}: {str(e)}")
        return None


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Extrator otimizado de dados de PDFs de intervenção')
    parser.add_argument('pdf', help='Caminho para o arquivo PDF')
    parser.add_argument('--debug', action='store_true', help='Ativar modo de debug')
    args = parser.parse_args()
    
    # Configurar nível de logging baseado nos argumentos
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Extrair dados do PDF
    dados = extrair_dados_pdf_relevantes(args.pdf)
    
    if dados:
        print(f"Extração concluída com sucesso para {args.pdf}")
        if args.debug:
            print(json.dumps(dados, indent=2, ensure_ascii=False))
    else:
        print(f"Falha na extração de dados para {args.pdf}")
        sys.exit(1)
