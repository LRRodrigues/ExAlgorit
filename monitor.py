"""
Sistema de monitoramento de alterações de um número específico em uma URL
"""

import requests
import re
import logging
import time
import sys
import psutil
from bs4 import BeautifulSoup
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from typing import Optional

# Setup do logger
logging.basicConfig(
    filename='monitoramento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Loga a atividade do usuário
def log_usuario(nome: str) -> None:
    if not re.fullmatch(r'[A-Za-z ]{3,}', nome):
        raise ValueError("Nome inválido. Use ao menos 3 caracteres e apenas letras.")
    logging.info(f"Usuário '{nome}' iniciou o monitoramento.")

# Captura recursos do sistema em tempo real
def log_recursos_sistema():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    logging.info(f"Uso de CPU: {cpu}%, Uso de Memória: {mem}%")

# Trata o HTML da página. (versão Selenium)
class MonitorHTML:
    def __init__(self, url: str, numero: str, timeout: int = 10):
        self.url = url
        self.numero = numero
        self.timeout = timeout
        self.ultima_ocorrencia = ""
        self.driver = self._setup_driver()

    def _setup_driver(self):
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            return driver
        except WebDriverException as e:
            logging.critical(f"Erro ao iniciar WebDriver: {e}")
            raise

    def validar_url(self) -> bool:
        pattern = re.compile(r'^https?://[\w.-]+(?:\.[\w\.-]+)+[/\w\.-]*$')
        return bool(pattern.match(self.url))

    def buscar_numero(self) -> Optional[str]:
        try:
            self.driver.get(self.url)
            time.sleep(2)  # Espera carregamento
            texto = self.driver.find_element(By.TAG_NAME, 'body').text

            match = re.search(re.escape(self.numero), texto)
            if match:
                logging.info(f"Número encontrado na posição: {match.start()} (Regex)")
                xpath = self._localizar_xpath(self.numero)
                if xpath:
                    logging.info(f"Número localizado via XPath: {xpath}")
                return texto
            else:
                logging.info("Número não encontrado na página.")
                return None
        except Exception as e:
            logging.error(f"Erro ao buscar número na página: {e}")
            return None

    def _localizar_xpath(self, texto_busca: str) -> Optional[str]:
        try:
            elementos = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{texto_busca}')]")
            if elementos:
                return self._get_xpath(elementos[0])
            return None
        except Exception as e:
            logging.error(f"Erro ao localizar XPath: {e}")
            return None

    def _get_xpath(self, elemento) -> str:
        path = ''
        while elemento.tag_name != 'html':
            siblings = self.driver.find_elements(By.XPATH, f"//{elemento.tag_name}")
            index = siblings.index(elemento) + 1
            path = f"/{elemento.tag_name}[{index}]" + path
            elemento = elemento.find_element(By.XPATH, "..")
        return f"/html{path}"

    def monitorar(self, intervalo: int = 60):
        logging.info(f"Iniciando monitoramento em: {self.url}")
        while True:
            log_recursos_sistema()
            conteudo = self.buscar_numero()
            if conteudo and conteudo != self.ultima_ocorrencia:
                logging.info("Alteração detectada no conteúdo da página.")
                self.ultima_ocorrencia = conteudo
            time.sleep(intervalo)

    def finalizar(self):
        self.driver.quit()

# Monitoramento de arquivos locais
class LogMudancasArquivos(FileSystemEventHandler):
    def on_modified(self, event):
        logging.info(f"Arquivo modificado: {event.src_path}")

    def on_created(self, event):
        logging.info(f"Arquivo criado: {event.src_path}")

def iniciar_monitoramento_arquivos(caminho: str):
    observador = Observer()
    evento = LogMudancasArquivos()
    observador.schedule(evento, caminho, recursive=True)
    observador.start()

"""
Execução principal.
Solicita nome do usuário, URL e número a ser monitorado.
Realiza validações, logs, e inicia os monitores de alteração e de recursos.
"""

def main():
    try:
        nome = input("Digite seu nome: ").strip()
        log_usuario(nome)

        url = input("Informe a URL a ser monitorada: ").strip()
        numero = input("Informe o número que deseja monitorar: ").strip()

        monitor = MonitorHTML(url, numero)

        if not monitor.validar_url():
            print("URL inválida.")
            return

        iniciar_monitoramento_arquivos('.')
        monitor.monitorar(intervalo=60)

    except Exception as e:
        logging.critical(f"Erro crítico: {e}")
        print(f"Erro: {e}")
        sys.exit(1)
    finally:
        try:
            monitor.finalizar()
        except:
            pass

if __name__ == "__main__":
    main()
