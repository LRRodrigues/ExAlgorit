# Monitorador de Valores com Selenium

Este script em Python monitora alterações de um valor específico dentro de uma página web e registra as mudanças em arquivos de log.

## 🔧 Requisitos

- Python 3.7 ou superior
- Google Chrome instalado
- ChromeDriver compatível com a versão do seu navegador

## 📦 Instalação

1. Clone este repositório ou copie os arquivos.
2. Instale as dependências com:

```bash
pip install -r requirements.txt
```
❗Este arquivo lista todas as dependências do script:
  -Nota: Este projeto depende também do chromedriver.exe, que deve estar no mesmo diretório do script ou no PATH.

##  ▶️ Como usar
Execute o script:

bash
```
python ultimo.py
```

Siga as instruções no terminal:

  -Informe seu nome.
  
  -Informe a URL do site.
  
  -Informe o valor exato que deseja monitorar (exemplo: R$5.000,00 ou 5,00).

O script abrirá o site de forma invisível (modo headless), localizará o valor e iniciará o monitoramento.

## 📝 Logs

log_acontecimentos.log: Log geral de eventos e erros.
valores_atualizados.log: Log específico com as mudanças de valor detectadas.

## ❗ Observações
O valor deve aparecer exatamente como escrito na página.

O monitoramento é contínuo e verifica a cada 10 segundos.

# 📄 Licença
Este projeto é de uso livre para fins educacionais e profissionais.

