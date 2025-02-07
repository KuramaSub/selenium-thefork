from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re

app = Flask(__name__)

# Configuração do Selenium (ChromeDriver precisa estar instalado)
def iniciar_navegador():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Executar sem abrir a janela do navegador
    options.add_argument("--no-sandbox")  # Necessário para servidores Linux
    options.add_argument("--disable-dev-shm-usage")  # Evita erro de memória
    driver = webdriver.Chrome(options=options)
    return driver

@app.route("/webhook", methods=["POST"])
def latepoint_webhook():
    data = request.json
    
    if not data:
        return jsonify({"error": "Dados inválidos ou JSON não recebido"}), 400

    try:
        # Extrair dados do webhook
        manage_booking_url = data.get("manage_booking_for_agent")
        customer = data.get("customer", {})
        cliente = customer.get("full_name")
        email = customer.get("email")
        telefone = customer.get("phone")
        start_date = data.get("start_date")
        start_time = data.get("start_time")
        
        if not (manage_booking_url and cliente and email and telefone and start_date and start_time):
            return jsonify({"error": "Dados incompletos recebidos do webhook"}), 400
        
        driver = iniciar_navegador()
        driver.get(manage_booking_url)
        time.sleep(3)
        
        # Extrair número do slot disponível
        slot_text = driver.find_element(By.XPATH, "//div[contains(text(), 'Slots')]").text
        slot_number = re.search(r"(\d+) de", slot_text)
        if slot_number:
            slot_number = slot_number.group(1)
        else:
            driver.quit()
            return jsonify({"error": "Não foi possível extrair o número do slot"}), 400
        
        # Acessar o site do TheFork e preencher a reserva
        restaurante_url = "https://www.thefork.com/restaurant/example-restaurant"
        driver.get(restaurante_url)
        time.sleep(3)
        
        # Preencher a data da reserva
        data_input = driver.find_element(By.ID, "date-picker-input")
        data_input.clear()
        data_input.send_keys(start_date)
        
        # Preencher o número de pessoas com base no slot extraído
        pessoas_input = driver.find_element(By.ID, "party-size-selector")
        pessoas_input.send_keys(str(slot_number))
        pessoas_input.send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Selecionar o horário correto
        horario_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{start_time}')]")
        horario_button.click()
        time.sleep(2)
        
        # Preencher detalhes do cliente
        nome_input = driver.find_element(By.NAME, "customer-name")
        nome_input.send_keys(cliente)
        
        email_input = driver.find_element(By.NAME, "customer-email")
        email_input.send_keys(email)
        
        telefone_input = driver.find_element(By.NAME, "customer-phone")
        telefone_input.send_keys(telefone)
        
        # Confirmar a reserva
        reservar_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
        reservar_button.click()
        time.sleep(3)
        
        driver.quit()
        return jsonify({"message": "Reserva feita com sucesso!", "slot": slot_number})
    
    except Exception as e:
        driver.quit()
        return jsonify({"error": f"Erro inesperado: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
