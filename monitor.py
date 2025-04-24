import asyncio # Execução assíncrona (paralela)
import logging # Registro de logs
import re      # Expressões regulares (validação e busca)
import sys     # Manipulação de exceções e finalização
from typing import Optional  # Tipagem

import psutil  # Monitoramento de CPU e memória
from selenium import webdriver  # Controle de navegador
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager # Baixa o driver automaticamente

from watchdog.observers import Observer # Observa arquivos
from watchdog.events import FileSystemEventHandler # Trata eventos de arquivos


# Log geral em "monitoramento.log"
logging.basicConfig(
    filename="monitoramento.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Log específico de valores alterados
log_valores = logging.getLogger("ValoresAlterados") # Log separado para valores detectados
handler_valores = logging.FileHandler("valores_alterados.log")
handler_valores.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
log_valores.addHandler(handler_valores)
log_valores.setLevel(logging.INFO)

# Valida e registra o nome do usuário
def log_usuario(nome: str):   
    if not re.fullmatch(r"[A-Za-z ]{3,}", nome):
        raise ValueError("Nome inválido. Use ao menos 3 letras.")
    logging.info(f"Usuário '{nome}' iniciou o monitoramento.")

# Loga uso de CPU e memória
def log_recursos():   
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    logging.info(f"CPU: {cpu}%, Memória: {mem}%")


class PaginaMonitorada:
    def __init__(self, url: str, numero: str):
        self.url = url
        self.numero = numero
        self.ultima_ocorrencia = ""
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
            wait = WebDriverWait(self.driver, 5)
            body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            texto = body.text

            match = re.search(re.escape(self.numero), texto)
            if match:
                logging.info(f"Número '{self.numero}' localizado.")
                return texto
            return None
        except Exception as e:
            logging.error(f"Erro na busca: {e}")
            return None

    def fechar(self):
        self.driver.quit()


class MonitorArquivos(FileSystemEventHandler):
    def on_modified(self, event):         # Loga arquivos modificados
        logging.info(f"Modificado: {event.src_path}")

    def on_created(self, event):          # Loga arquivos criados
        logging.info(f"Criado: {event.src_path}")

    def iniciar(self, caminho="."):      # Inicia observação de arquivos
        observer = Observer()
        observer.schedule(self, caminho, recursive=True)
        observer.start()
        return observer


async def monitoramento_web(monitor: PaginaMonitorada, intervalo: int = 60):  # Checa repetidamente a página
    logging.info(f"Iniciando monitoramento da URL: {monitor.url}")
    try:
        while True:
            log_recursos()
            conteudo = await asyncio.to_thread(monitor.buscar_numero)

            if conteudo and conteudo != monitor.ultima_ocorrencia:
                logging.info("Alteração detectada na página.")
                monitor.ultima_ocorrencia = conteudo

                # Extrai o trecho com o número e salva no log específico
                match = re.search(re.escape(monitor.numero) + r".{0,20}", conteudo)
                if match:
                    valor_encontrado = match.group(0).strip()
                    log_valores.info(f"Novo valor detectado: {valor_encontrado}")

            await asyncio.sleep(intervalo)
    except asyncio.CancelledError:
        pass
    finally:
        monitor.fechar()


async def main():
    try:
        nome = input("Seu nome: ").strip()
        log_usuario(nome)

        url = input("URL a monitorar: ").strip()
        numero = input("Número a buscar: ").strip()

        monitor = PaginaMonitorada(url, numero)
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
