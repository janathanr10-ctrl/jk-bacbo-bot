from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import telegram
import schedule
import threading
import time
from collections import Counter
import os

TOKEN = os.getenv('TOKEN')
VIP_GROUP_ID = int(os.getenv('VIP_GROUP_ID'))
URL = 'https://www.betano.bet.br/casino/live/games/bac-bo/5605/tables/'

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

ultimos_sinais = []
status_bot = 'Parado'

def iniciar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def pegar_resultados():
    driver = iniciar_driver()
    driver.get(URL)
    time.sleep(10)

    resultados = []
    elementos = driver.find_elements("css selector", '.game-history-result .result-item')
    for elem in elementos[:10]:
        classes = elem.get_attribute('class')
        if 'red' in classes:
            resultados.append('vermelho')
        elif 'blue' in classes:
            resultados.append('azul')
        elif 'yellow' in classes:
            resultados.append('amarelo')
        else:
            resultados.append('desconhecido')
    driver.quit()
    return resultados

def analisar_resultados(resultados):
    resultados_validos = [r for r in resultados if r in ['vermelho', 'azul', 'amarelo']]
    if not resultados_validos:
        return None
    contagem = Counter(resultados_validos)
    return contagem.most_common(1)[0][0]

def enviar_sinal():
    global status_bot, ultimos_sinais
    status_bot = 'Rodando'
    try:
        resultados = pegar_resultados()
        cor = analisar_resultados(resultados)
        if cor is None:
            print("Não foi possível determinar o sinal")
            status_bot = 'Erro: sem sinal'
            return

        mensagem = f"""📢 *Sinal JK Bac Bo* 📊

🎲 Cor recomendada: `{cor.capitalize()}`  
⏰ Validade: 3 minutos  
👉 Aposte aqui: {URL}

Jogue com responsabilidade! ✅"""

        bot.send_message(chat_id=VIP_GROUP_ID, text=mensagem, parse_mode=telegram.ParseMode.MARKDOWN)
        print(f"Sinal enviado: {cor}")

        ultimos_sinais.insert(0, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {cor.capitalize()}")
        if len(ultimos_sinais) > 10:
            ultimos_sinais.pop()
        status_bot = 'Rodando'
    except Exception as e:
        print(f"Erro ao enviar sinal: {e}")
        status_bot = f"Erro: {e}"

def agendador():
    schedule.every(5).minutes.do(enviar_sinal)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template_string('''
        <h1>JK BacBo Signals - Painel</h1>
        <p>Status do Bot: <b>{{status}}</b></p>
        <h2>Últimos Sinais Enviados</h2>
        <ul>
        {% for sinal in sinais %}
            <li>{{ sinal }}</li>
        {% else %}
            <li>Nenhum sinal enviado ainda.</li>
        {% endfor %}
        </ul>
    ''', status=status_bot, sinais=ultimos_sinais)

if __name__ == '__main__':
    thread = threading.Thread(target=agendador)
    thread.daemon = True
    thread.start()

    app.run(host='0.0.0.0', port=8080)
