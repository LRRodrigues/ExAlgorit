# Importação das bibliotecas necessárias
import requests
import re  # Biblioteca de expressões regulares
import logging  # Biblioteca para gerar logs de atividades
import time  # Biblioteca para manipulação de tempo
import sys  # Biblioteca para manipulação de argumentos do sistema
import psutil  # Biblioteca para monitoramento de uso de CPU e memória
from selenium import webdriver  # Selenium para interação com a web
from selenium.webdriver.chrome.options import Options  # Configurações do navegador
from selenium.webdriver.common.by import By  # Para localizar elementos na página
from selenium.common.exceptions import WebDriverException  # Exceções do Selenium
from typing import Optional  # Para tipagem opcional de retorno

# Configuração do Logger para monitoramento e logs
logging.basicConfig(
    filename='monitoramento.log',  # Define o nome do arquivo de log
    level=logging.INFO,            # Define o nível do log (INFO para mostrar informações gerais)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Define o formato do log com data, nível e mensagem
)

# Função para logar a atividade do usuário
def log_usuario(nome: str) -> None:
    """
    Função que valida o nome do usuário e loga a atividade no arquivo de log.
    """
    # Validação do nome: pelo menos 3 caracteres alfabéticos
    if not re.fullmatch(r'[A-Za-z ]{3,}', nome):
        raise ValueError("Nome inválido. Use ao menos 3 caracteres e apenas letras.")
    logging.info(f"Usuário '{nome}' iniciou o monitoramento.")  # Registra o nome do usuário no log

# Função para capturar e logar o uso de recursos do sistema (CPU e Memória)
def log_recursos_sistema():
    """
    Função que coleta informações sobre o uso de CPU e memória e registra no log.
    """
    cpu = psutil.cpu_percent()  # Captura o uso percentual da CPU
    mem = psutil.virtual_memory().percent  # Captura o uso percentual da memória
    logging.info(f"Uso de CPU: {cpu}%, Uso de Memória: {mem}%")  # Registra no log

# Classe responsável pelo monitoramento da página HTML
class MonitorHTML:
    def __init__(self, url: str, numero: str, timeout: int = 10):
        """
        Inicializa a classe de monitoramento com a URL, número a ser monitorado e o tempo de timeout.
        """
        self.url = url  # URL que será monitorada
        self.numero = numero  # Número que estamos buscando
        self.timeout = timeout  # Tempo máximo de espera para carregar a página
        self.ultima_ocorrencia = ""  # Variável para armazenar o último conteúdo encontrado
        self.driver = self._setup_driver()  # Inicializa o WebDriver

    def _setup_driver(self):
        """
        Configura o WebDriver para Selenium, incluindo opções para rodar em modo headless.
        """
        try:
            options = Options()  # Cria uma instância de opções do navegador
            options.add_argument('--headless')  # Define o navegador para rodar sem interface gráfica
            options.add_argument('--disable-gpu')  # Desabilita a aceleração de GPU (necessário em alguns sistemas)
            options.add_argument('--no-sandbox')  # Impede o uso de sandbox, melhora performance em alguns casos
            driver = webdriver.Chrome(options=options)  # Inicializa o WebDriver com as opções definidas
            driver.set_page_load_timeout(self.timeout)  # Define o tempo de timeout para carregar a página
            return driver
        except WebDriverException as e:
            logging.critical(f"Erro ao iniciar WebDriver: {e}")  # Registra erro crítico no log se o WebDriver falhar
            raise  # Lança a exceção para interromper a execução

    def validar_url(self) -> bool:
        """
        Valida se a URL fornecida é válida usando uma expressão regular.
        """
        pattern = re.compile(r'^https?://[\w.-]+(?:\.[\w\.-]+)+[/\w\.-]*$')  # Expressão regular para validar URLs
        return bool(pattern.match(self.url))  # Retorna True se a URL for válida, caso contrário False

    def buscar_numero(self) -> Optional[str]:
        """
        Busca o número especificado na página carregada usando o Selenium.
        """
        try:
            self.driver.get(self.url)  # Carrega a página da URL fornecida
            time.sleep(2)  # Aguarda 2 segundos para garantir que a página foi completamente carregada
            texto = self.driver.find_element(By.TAG_NAME, 'body').text  # Obtém o texto completo da página

            # Usa expressão regular para procurar o número dentro do texto da página
            match = re.search(re.escape(self.numero), texto)
            if match:
                logging.info(f"Número {self.numero} encontrado na posição: {match.start()} (Regex)")  # Log do número encontrado
                return texto  # Retorna o conteúdo completo da página
            else:
                logging.info(f"Número {self.numero} não encontrado na página.")  # Log do número não encontrado
                return None
        except Exception as e:
            logging.error(f"Erro ao buscar número na página: {e}")  # Log de erro caso algo falhe ao buscar o número
            return None

    def monitorar(self, intervalo: int = 60):
        """
        Monitora a página indefinidamente, verificando o número a cada intervalo de tempo (em segundos).
        """
        logging.info(f"Iniciando monitoramento em: {self.url}")  # Log de início do monitoramento
        while True:
            log_recursos_sistema()  # Log do uso de recursos do sistema (CPU, memória)
            conteudo = self.buscar_numero()  # Chama a função para buscar o número na página

            if conteudo:
                logging.info(f"Número verificado: {self.numero}")  # Log do número verificado
                logging.info(f"Conteúdo da página verificado: {conteudo[:500]}...")  # Exibe os primeiros 500 caracteres do conteúdo da página

            # Se o conteúdo foi encontrado e for diferente do último verificado, considera que houve alteração
            if conteudo and conteudo != self.ultima_ocorrencia:
                logging.info("Alteração detectada no conteúdo da página.")  # Log de alteração detectada
                self.ultima_ocorrencia = conteudo  # Atualiza a variável que armazena o conteúdo da última verificação

            time.sleep(intervalo)  # Aguarda o intervalo antes de realizar nova verificação

    def finalizar(self):
        """
        Finaliza o driver do Selenium, fechando o navegador e liberando os recursos.
        """
        self.driver.quit()  # Fecha o WebDriver, liberando os recursos

# Função principal que executa o script
def main():
    try:
        nome = input("Digite seu nome: ").strip()  # Solicita o nome do usuário
        log_usuario(nome)  # Loga a atividade do usuário

        url = input("Informe a URL a ser monitorada: ").strip()  # Solicita a URL para monitoramento
        numero = input("Informe o número que deseja monitorar: ").strip()  # Solicita o número a ser monitorado

        # Cria uma instância do monitor para a URL e número fornecidos
        monitor = MonitorHTML(url, numero)

        # Verifica se a URL fornecida é válida
        if not monitor.validar_url():
            print("URL inválida.")
            return  # Se a URL não for válida, encerra a execução

        monitor.monitorar(intervalo=60)  # Inicia o monitoramento da página a cada 60 segundos

    except Exception as e:
        logging.critical(f"Erro crítico: {e}")  # Log de erro crítico caso ocorra algum problema
        print(f"Erro: {e}")  # Exibe a mensagem de erro para o usuário
        sys.exit(1)  # Finaliza a execução do script com código de erro 1
    finally:
        try:
            monitor.finalizar()  # Finaliza o monitoramento e fecha o WebDriver
        except:
            pass

# Inicia a execução do script chamando a função principal
if __name__ == "__main__":
    main()
