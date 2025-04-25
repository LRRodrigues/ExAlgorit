import re
import time
import logging
from typing import Optional
from playwright.sync_api import sync_playwright

# === CONFIGURAÇÃO DE LOG ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log_sistema.txt"),
        logging.StreamHandler()
    ]
)

# Valida se o nome inserido é aceitável (mínimo 3 letras e apenas caracteres alfabéticos)
def validar_nome_usuario(nome: str) -> bool:
    return len(nome) >= 3 and nome.replace(" ", "").isalpha()

# Solicita e valida o nome do usuário
def solicitar_usuario() -> str:
    while True:
        nome = input("Digite seu nome: ").strip()
        if validar_nome_usuario(nome):
            logging.info(f"Usuário identificado: {nome}")
            return nome
        else:
            print("Nome inválido. Deve conter ao menos 3 letras e apenas caracteres alfabéticos.")

# Solicita e valida o número a ser monitorado (como string, mantendo formatação)
def solicitar_numero_alvo() -> str:
    padrao = r'^-?\d+(?:[\.,]\d+)?$'
    while True:
        entrada = input("Digite o número que deseja monitorar (ex: 5,718 ou -3,14): ").strip()
        entrada_normalizada = entrada.replace(".", "").replace(",", ".")
        if re.match(padrao, entrada_normalizada):
            logging.info(f"Número alvo definido para monitoramento: {entrada}")
            return entrada_normalizada  # Retorna já em formato com ponto
        else:
            print("Número inválido. Exemplo de formatos válidos: -10, 20.5, 3,1415")

# Função principal que monitora o valor em tempo real usando o Playwright
def monitorar_em_tempo_real(url: str, numero_alvo: str):
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page()
        pagina.goto(url, timeout=60000)

        logging.info("Iniciando monitoramento em tempo real...")

        while True:
            try:
                # Captura o valor bruto do HTML
                valor_bruto = pagina.locator('[data-test="instrument-price-last"]').inner_text(timeout=10000).strip()

                # Remove caracteres indesejados e normaliza para ponto decimal
                valor_limpo = re.sub(r'[^\d,.-]', '', valor_bruto)
                valor_formatado = valor_limpo.replace('.', '').replace(',', '.')

                # Mostra apenas o número limpo no log
                if numero_alvo in valor_formatado:
                    logging.info(f"{valor_formatado} ← Número alvo encontrado!")
                else:
                    logging.info(f"{valor_formatado}")

                time.sleep(1)  # Atualiza a cada 1 segundo (como o site)
            except Exception as e:
                logging.error(f"Erro ao buscar valor ao vivo: {e}")
                time.sleep(5)

# Função principal do programa
def main():
    print("=== SISTEMA DE MONITORAMENTO EM TEMPO REAL ===")
    usuario = solicitar_usuario()

    while True:
        url = input("Digite a URL que deseja monitorar: ").strip()
        if url.startswith("http://") or url.startswith("https://"):
            break
        else:
            print("URL inválida. Deve começar com http:// ou https://")

    numero_alvo = solicitar_numero_alvo()
    logging.info(f"Usuário '{usuario}' iniciou o monitoramento da URL: {url}")
    monitorar_em_tempo_real(url, numero_alvo)

# Executa o programa se for chamado diretamente
if __name__ == "__main__":
    main()
