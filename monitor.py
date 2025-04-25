import asyncio
import logging
import re
import sys
from typing import Optional

import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Log geral
logging.basicConfig(
    filename="monitoramento.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Log específico de valores alterados
log_valores = logging.getLogger("ValoresAlterados")
handler_valores = logging.FileHandler("valores_alterados.log")
handler_valores.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
log_valores.addHandler(handler_valores)
log_valores.setLevel(logging.INFO)

def log_usuario(nome: str):
    if not re.fullmatch(r"[A-Za-z ]{3,}", nome):
        raise ValueError("Nome inválido. Use ao menos 3 letras.")
    logging.info(f"Usuário '{nome}' iniciou o monitoramento.")

def log_recursos():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    logging.info(f"CPU: {cpu}%, Memória: {mem}%")

class PaginaMonitorada:
    def __init__(self, url: str):
        self.url = url
        self.ultimo_valor = ""
        self.driver = self._setup_driver()

    def _setup_driver(self):
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.set_page_load_timeout(10)
            return driver
        except WebDriverException as e:
            logging.critical(f"Erro ao iniciar WebDriver: {e}")
            raise

    def validar_url(self):
        return re.match(r"^https?://[\w\.-]+", self.url)

    def buscar_numero(self) -> Optional[str]:
        try:
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 20)  # tempo aumentado

            # Espera até o elemento com o data-test estar presente
            elemento = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="instrument-price-last"]'))
            )

            texto = elemento.text.strip()
            if texto:
                logging.info(f"Valor localizado: {texto}")
                return texto
            else:
                logging.warning("Elemento encontrado, mas sem texto.")
            return None
        except Exception as e:
            logging.error(f"Erro na busca: {e}")
            return None


    def fechar(self):
        self.driver.quit()

class MonitorArquivos(FileSystemEventHandler):
    def on_modified(self, event):
        logging.info(f"Modificado: {event.src_path}")

    def on_created(self, event):
        logging.info(f"Criado: {event.src_path}")

    def iniciar(self, caminho="."):
        observer = Observer()
        observer.schedule(self, caminho, recursive=True)
        observer.start()
        return observer

async def monitoramento_web(monitor: PaginaMonitorada, intervalo: int = 60):
    logging.info(f"Iniciando monitoramento da URL: {monitor.url}")
    try:
        while True:
            log_recursos()
            valor = await asyncio.to_thread(monitor.buscar_numero)

            if valor and valor != monitor.ultimo_valor:
                logging.info(f"Valor alterado: {valor}")
                monitor.ultimo_valor = valor
                log_valores.info(f"Novo valor detectado: {valor}")

            await asyncio.sleep(intervalo)
    except asyncio.CancelledError:
        pass
    finally:
        monitor.fechar()

async def main():
    try:
        nome = input("Seu nome: ").strip()
        log_usuario(nome)

        url = "https://br.investing.com/crypto/bitcoin"
        monitor = PaginaMonitorada(url)

        if not monitor.validar_url():
            print("URL inválida.")
            return

        monitor_arquivos = MonitorArquivos()
        observer = monitor_arquivos.iniciar()

        tarefa_web = asyncio.create_task(monitoramento_web(monitor, intervalo=60))

        print("Monitoramento iniciado. Pressione Ctrl+C para parar.")
        await tarefa_web

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    except Exception as e:
        logging.critical(f"Erro crítico: {e}")
        print(f"Erro: {e}")
        sys.exit(1)
    finally:
        try:
            observer.stop()
            observer.join()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
