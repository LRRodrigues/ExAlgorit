# Importa bibliotecas padrão do Python
import re                 # Para trabalhar com expressões regulares
import time               # Para criar pausas no código (sleep)
import logging            # Para registrar logs (mensagens informativas, de erro etc.)
from typing import Optional  # Para anotar tipos opcionais nas funções
from playwright.sync_api import sync_playwright  # Importa o Playwright para automação de navegador (modo síncrono)



# Define a configuração do sistema de log
logging.basicConfig(
    level=logging.INFO,  # Nível de log: mostra informações, alertas e erros
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato da mensagem
    handlers=[
        logging.FileHandler("log_sistema.txt"),  # Salva os logs no arquivo
        logging.StreamHandler()                  # Também mostra no terminal
    ]
)



def validar_nome_usuario(nome: str) -> bool:
    # Verifica se o nome tem pelo menos 3 caracteres e é composto apenas por letras (desconsiderando espaços)
    return len(nome) >= 3 and nome.replace(" ", "").isalpha()


def solicitar_usuario() -> str:
    while True:
        nome = input("Digite seu nome: ").strip()  # Solicita e remove espaços extras
        if validar_nome_usuario(nome):             # Valida o nome
            logging.info(f"Usuário identificado: {nome}")  # Loga a identificação
            return nome
        else:
            print("Nome inválido. Deve conter ao menos 3 letras e apenas caracteres alfabéticos.")


def solicitar_numero_alvo() -> str:
    padrao = r'^-?\d+(?:[\.,]\d+)?$'  # Regex para validar números inteiros ou decimais com ponto ou vírgula

    while True:
        entrada = input("Digite o número que deseja monitorar (ex: 5,718 ou -3,14): ").strip()
        entrada_normalizada = entrada.replace(".", "").replace(",", ".")  # Normaliza o número (ex: 1.234,56 → 1234.56)

        if re.match(padrao, entrada_normalizada):  # Verifica se o número é válido com regex
            logging.info(f"Número alvo definido para monitoramento: {entrada}")
            return entrada
        else:
            print("Número inválido. Exemplo de formatos válidos: -10, 20.5, 3,1415")


def monitorar_em_tempo_real(url: str, numero_alvo: str):
    # Inicia o Playwright (modo sincronizado)
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)  # Abre o navegador Chromium de forma invisível
        pagina = navegador.new_page()                 # Cria uma nova aba/página
        pagina.goto(url, timeout=60000)               # Acessa a URL com timeout de 60 segundos

        logging.info("Iniciando monitoramento em tempo real...")

        while True:
            try:
                # Localiza o valor do índice usando o seletor com atributo data-test="instrument-price-last"
                valor = pagina.locator('[data-test="instrument-price-last"]').inner_text(timeout=10000).strip()

                # Verifica se o valor atual contém o número alvo
                if numero_alvo in valor:
                    logging.info(f"Valor atual corresponde ao número monitorado ({numero_alvo}): {valor}")
                else:
                    logging.info(f"Valor atual: {valor} (número alvo: {numero_alvo})")

                time.sleep(1)  # Espera 1 segundo antes de repetir (frequência do site)
            except Exception as e:
                # Em caso de erro, registra a mensagem e espera 5 segundos antes de tentar novamente
                logging.error(f"Erro ao buscar valor ao vivo: {e}")
                time.sleep(5)

def main():
    print("=== SISTEMA DE MONITORAMENTO EM TEMPO REAL ===")
    usuario = solicitar_usuario()  # Solicita e valida nome

    while True:
        url = input("Digite a URL que deseja monitorar: ").strip()
        if url.startswith("http://") or url.startswith("https://"):  # Garante que a URL é válida
            break
        else:
            print("URL inválida. Deve começar com http:// ou https://")

    numero_alvo = solicitar_numero_alvo()  # Solicita o número a ser monitorado

    logging.info(f"Usuário '{usuario}' iniciou o monitoramento da URL: {url}")
    monitorar_em_tempo_real(url, numero_alvo)  # Inicia o monitoramento


if __name__ == "__main__":
    main()  # Roda o programa se o arquivo for executado diretamente
