"""
Sistema de Monitoramento Web com Log, Busca de Número e Documentação.

Este script monitora um site em busca de um número específico, identifica
alterações no conteúdo, registra logs do sistema e do usuário, e valida
todas as entradas. Pode ser usado para fins acadêmicos, auditorias ou
monitoramento contínuo de dados em páginas HTML.

Autor: Lucas (adaptado por ChatGPT)
Data: 25/04/2025
"""

import requests         # Requisições HTTP para capturar HTML do site
import re               # Regex para busca flexível de números (ponto ou vírgula)
import time             # Pausa entre os ciclos de monitoramento
import logging          # Registro de logs do sistema
from datetime import datetime  # Timestamp de eventos e logs

# === Configuração do log de sistema (grava ações técnicas e eventos) ===
logging.basicConfig(
    filename='log_sistema.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# === Arquivo de log de usuário ===
user_log = open("log_usuario.txt", "a", encoding="utf-8")

def log_usuario(msg: str):
    """
    Registra uma mensagem no log do usuário com timestamp.
    
    :param msg: Mensagem a ser registrada.
    """
    user_log.write(f"{datetime.now()} - {msg}\n")
    user_log.flush()  # Garante que a escrita ocorra imediatamente

def validar_url(url: str) -> bool:
    """
    Valida se a URL começa com http:// ou https://.

    :param url: URL fornecida pelo usuário.
    :return: True se válida, False caso contrário.
    """
    return url.startswith("http://") or url.startswith("https://")

def obter_html(url: str, timeout: int = 10) -> str:
    """
    Faz uma requisição GET ao site e retorna o conteúdo HTML.

    :param url: URL do site.
    :param timeout: Tempo máximo de espera da requisição.
    :return: HTML da página como string.
    :raises Exception: Se a requisição falhar.
    """
    try:
        resposta = requests.get(url, timeout=timeout)
        resposta.raise_for_status()
        return resposta.text
    except Exception as e:
        logging.error(f"Erro ao acessar {url}: {e}")
        raise

def buscar_numero(html: str, numero: str) -> list:
    """
    Procura o número na página com regex, considerando ponto ou vírgula.

    :param html: Conteúdo HTML.
    :param numero: Número a ser buscado.
    :return: Lista de posições onde o número foi encontrado.
    """
    try:
        # Converte "," ou "." para regex genérico [.,]
        numero_regex = re.escape(numero).replace(",", "[.,]").replace(".", "[.,]")
        matches = list(re.finditer(numero_regex, html))

        for match in matches:
            pos = match.start()
            logging.info(f"Número encontrado na posição: {pos}")
            print(f"✔ Número encontrado na posição: {pos}")
        return matches
    except Exception as e:
        logging.error(f"Erro na busca do número: {e}")
        raise

def monitorar_pagina(url: str, numero: str, ciclos: int = 5, intervalo: int = 10):
    """
    Monitora a página procurando mudanças e ocorrências do número.

    :param url: Endereço do site.
    :param numero: Número a ser monitorado.
    :param ciclos: Quantidade de ciclos de monitoramento.
    :param intervalo: Tempo entre as verificações.
    """
    log_usuario(f"Início do monitoramento: URL={url}, Número={numero}")
    ultimo_html = ""

    for i in range(ciclos):
        try:
            print(f"🔍 [{i+1}/{ciclos}] Verificando a página...")

            html = obter_html(url)

            if html != ultimo_html:
                logging.info("🔁 Alteração detectada na página.")

                if numero in html:
                    print("✅ Número identificado na nova versão.")
                    buscar_numero(html, numero)
                else:
                    print("❌ Número não encontrado.")
                    logging.info("Número ausente na nova versão da página.")

                ultimo_html = html  # Atualiza o HTML salvo
            else:
                print("🟡 Nenhuma mudança detectada.")
                logging.info("Sem alterações na página.")

            time.sleep(intervalo)

        except Exception as e:
            print(f"⚠ Erro no ciclo {i+1}: {e}")
            logging.error(f"Erro no ciclo {i+1}: {e}")

    log_usuario("Monitoramento encerrado.")
    user_log.close()

# ============================
# ENTRADA DO USUÁRIO
# ============================

if __name__ == "__main__":
    print("=== Monitoramento de Número em Site ===")
    nome_usuario = input("Digite seu nome (mínimo 3 letras): ").strip()

    while len(nome_usuario) < 3 or not nome_usuario.replace(" ", "").isalpha():
        print("❗ Nome inválido. Use apenas letras, com pelo menos 3 caracteres.")
        nome_usuario = input("Digite seu nome novamente: ").strip()

    log_usuario(f"Usuário: {nome_usuario}")

    url = input("Digite a URL do site a ser monitorado: ").strip()
    while not validar_url(url):
        print("❗ URL inválida. Deve começar com http:// ou https://")
        url = input("Digite novamente a URL: ").strip()

    numero = input("Digite o número que deseja procurar: ").strip()
    while not numero.replace(",", "").replace(".", "").isdigit():
        print("❗ Entrada inválida. Digite um número com ou sem vírgula/ponto.")
        numero = input("Digite o número: ").strip()

    # Chama a função principal
    monitorar_pagina(url, numero, ciclos=5, intervalo=10)

    print("✅ Monitoramento finalizado com sucesso.")
