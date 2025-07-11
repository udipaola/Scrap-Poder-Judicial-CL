# Archivo: verificacion_worker.py

import time
import tempfile
import os
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

MAX_REINTENTOS_VERIFICACION = 3

def verificacion_worker(task):
    """
    Un worker ligero que verifica si la página de consulta es accesible.
    Reintenta varias veces antes de darse por vencido.
    """
    headless_mode, = task

    for intento in range(MAX_REINTENTOS_VERIFICACION):
        print(f"[VERIFICADOR - Intento {intento + 1}/{MAX_REINTENTOS_VERIFICACION}] Iniciando...")
        driver = None
        try:
            # Crear un perfil único temporal para verificación
            profile_path = os.path.join(tempfile.gettempdir(), f"pjud_verification_profile_{uuid.uuid4()}")
            
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--window-position=-2000,0")
            if headless_mode:
                options.add_argument("--headless")

            driver = webdriver.Chrome(options=options)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            wait = WebDriverWait(driver, 20)

            driver.get("https://oficinajudicialvirtual.pjud.cl/")

            try:
                short_wait = WebDriverWait(driver, 5)
                cerrar_popup_button = short_wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Cerrar' and @data-dismiss='modal']"))
                )
                cerrar_popup_button.click()
            except TimeoutException:
                pass # No hay popup, no es un error

            boton_causas = wait.until(EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Consulta causas']")))
            driver.execute_script("arguments[0].click();", boton_causas)

            short_wait = WebDriverWait(driver, 10)
            short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#BusFecha"]')))
            
            print(f"[VERIFICADOR - Intento {intento + 1}] ¡ÉXITO! Acceso verificado.")
            if driver:
                driver.quit()
            return True # Si todo va bien, retornamos True y salimos de la función

        except Exception as e:
            print(f"[VERIFICADOR - Intento {intento + 1}] Fallo: {str(e)[:100]}...")
            if driver:
                driver.quit()
            if intento < MAX_REINTENTOS_VERIFICACION - 1:
                print("Reintentando en 5 segundos...")
                time.sleep(5)
            continue # Pasamos a la siguiente iteración del bucle

    # Si el bucle termina sin haber retornado True, es que todos los intentos fallaron
    print("[VERIFICADOR] Todos los intentos de verificación han fallado.")
    return False