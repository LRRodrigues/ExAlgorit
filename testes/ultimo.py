

# Importação das bibliotecas necessárias
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import logging
import time
import sys
from datetime import datetime
import os

# Configuração do sistema de logs para registrar eventos e mudanças de valores
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log_acontecimentos.log"),
        logging.StreamHandler(sys.stdout)
    ])

# Logger específico para mudanças de valores
valor_logger = logging.getLogger("valores_logger")
valor_handler = logging.FileHandler("valores_atualizados.log")
valor_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
valor_logger.addHandler(valor_handler)
valor_logger.propagate = False

# Validação do nome do usuário
def validar_nome(nome):
    if len(nome.strip()) <= 3:
        raise ValueError("Nome inválido. Deve conter mais de 3 caracteres.")
    return nome.strip()

# Limpeza do valor informado, removendo caracteres indesejados
def limpar_valor(valor):
    return re.sub(r'[<>"\']', '', valor.strip())

# Função para gerar o XPath completo de um elemento encontrado
# Utiliza JavaScript para percorrer a árvore DOM
def gerar_xpath_completo(driver, elemento):
    try:
        xpath = driver.execute_script("""
            function absoluteXPath(element) {
                var comp, comps = [];
                var parent = null;
                var xpath = '';
                var getPos = function(element) {
                    var position = 1, curNode;
                    if (element.nodeType == Node.ATTRIBUTE_NODE) {
                        return null;
                    }
                    for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){
                        if (curNode.nodeName == element.nodeName)
                            ++position;
                    }
                    return position;
                }

                if (element instanceof Document) {
                    return '/';
                }

                for (; element && !(element instanceof Document); element = element.nodeType ==Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                    comp = {};
                    switch (element.nodeType) {
                        case Node.TEXT_NODE:
                            comp.name = 'text()';
                            break;
                        case Node.ATTRIBUTE_NODE:
                            comp.name = '@' + element.nodeName;
                            break;
                        case Node.PROCESSING_INSTRUCTION_NODE:
                            comp.name = 'processing-instruction()';
                            break;
                        case Node.COMMENT_NODE:
                            comp.name = 'comment()';
                            break;
                        case Node.ELEMENT_NODE:
                            comp.name = element.nodeName;
                            break;
                    }
                    comp.position = getPos(element);
                    comps.push(comp);
                }

                for (var i = comps.length - 1; i >= 0; i--) {
                    comp = comps[i];
                    xpath += '/' + comp.name.toLowerCase();
                    if (comp.position !== null) {
                        xpath += '[' + comp.position + ']';
                    }
                }

                return xpath;
            }
            return absoluteXPath(arguments[0]);
        """, elemento)
        return xpath
    except Exception as e:
        logging.error(f"Erro ao gerar XPath: {e}")
        return None

# Busca o elemento que contém exatamente o valor informado
def encontrar_elemento_por_valor(driver, valor_exato):
    try:
        elementos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//*[text()='{valor_exato}']"))
        )
        for elemento in elementos:
            texto = elemento.text.strip()
            if texto == valor_exato:
                return elemento
    except Exception as e:
        logging.error(f"Erro ao encontrar elemento: {e}")
    return None

# Monitora continuamente o valor localizado por um XPath e registra mudanças
def monitorar_xpath(driver, xpath, valor_anterior, usuario, url):
    while True:
        try:
            elemento = driver.find_element(By.XPATH, xpath)
            texto_atual = elemento.text.strip()
            if texto_atual != valor_anterior:
                logging.info(f"Valor alterado! De {valor_anterior} para {texto_atual}")
                valor_logger.info(f"Usuário: {usuario} | Site: {url} | {valor_anterior} -> {texto_atual}")
                valor_anterior = texto_atual
            else:
                logging.info("Nenhuma alteração detectada.")
            valor_logger.info(f"Usuário: {usuario} | Site: {url} | Valor atual: {texto_atual}")
        except Exception as e:
            logging.error(f"Erro ao monitorar valor por XPath: {e}")
        time.sleep(10)

# Bloco principal do programa com tratamento de exceções
try:
    # Coleta de entrada do usuário
    nome_usuario = input("Digite seu nome: ")
    nome_usuario = validar_nome(nome_usuario)

    url = input("Digite o link do site: ").strip()
    valor_desejado = input("Digite o valor a ser monitorado (ex: R$5.000,00 ou 5,00): ").strip()

    if not valor_desejado:
        raise ValueError("Valor não pode ser vazio.")
    valor_limpo = limpar_valor(valor_desejado)

    # Registro inicial das informações
    logging.info(f"Usuário: {nome_usuario}")
    logging.info(f"URL: {url}")
    logging.info(f"Valor exato a buscar: {valor_limpo}")

    # Configurações do navegador (headless)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113 Safari/537.36")

    # Caminho do ChromeDriver e inicialização
    service = ChromeService(executable_path=os.path.join(os.getcwd(), 'chromedriver.exe'))
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    # Aguarda o carregamento da página
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    logging.info("Página carregada com sucesso.")

    # Encontra o elemento correspondente ao valor e gera o XPath
    elemento = encontrar_elemento_por_valor(driver, valor_limpo)
    if not elemento:
        raise Exception("Valor não encontrado na página.")

    xpath = gerar_xpath_completo(driver, elemento)
    if not xpath:
        raise Exception("XPath não pôde ser gerado.")
    logging.info(f"XPath gerado: {xpath}")

    # Inicia o monitoramento do valor
    logging.info("Iniciando monitoramento do valor...")
    monitorar_xpath(driver, xpath, valor_limpo, nome_usuario, url)

except Exception as e:
    logging.critical(f"Erro crítico: {e}")
    print(f"Erro: {e}")
    sys.exit(1)
