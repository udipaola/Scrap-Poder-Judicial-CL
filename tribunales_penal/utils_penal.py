# Archivo: utils.py

import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def forzar_cierre_navegadores():
    """
    Intenta forzar el cierre de todos los procesos de Chrome y ChromeDriver usando la ruta absoluta de taskkill para mayor robustez.
    Esto es útil cuando los drivers o ventanas quedan colgados.
    """
    taskkill_path = r"C:\Windows\System32\taskkill.exe"
    print("[CIERRE FORZADO GLOBAL] Intentando terminar todos los procesos de ChromeDriver y Chrome...")
    os.system(f'{taskkill_path} /F /IM chromedriver.exe /T > nul 2>&1')
    os.system(f'{taskkill_path} /F /IM chrome.exe /T > nul 2>&1')
    time.sleep(2)  # Pausa para que el SO libere recursos
    print("[CIERRE FORZADO GLOBAL] Comandos de terminación ejecutados.")

def quedan_procesos_navegador():
    """
    Verifica si quedan procesos chrome.exe o chromedriver.exe activos.
    Retorna True si existen, False si no.
    """
    # Usamos la ruta absoluta para evitar problemas con la variable PATH
    tasklist_path = r"C:\Windows\System32\tasklist.exe"
    
    chrome = os.popen(f'{tasklist_path} /FI "IMAGENAME eq chrome.exe"').read()
    chromedriver = os.popen(f'{tasklist_path} /FI "IMAGENAME eq chromedriver.exe"').read()
    
    # Verificamos que el comando no haya devuelto un error antes de chequear el contenido
    if "ERROR:" in chrome or "información" in chrome.lower(): # El mensaje de error puede variar
        return False # Asumimos que no hay procesos si el comando falla
        
    return "chrome.exe" in chrome or "chromedriver.exe" in chromedriver

def is_ip_blocked_con_reintentos(driver, dia_id, retries=3, delay=5):
    """
    Verifica si la IP está bloqueada, reintentando varias veces.
    Intenta recargar la página para confirmar el estado.
    """
    print(f"[{dia_id}] Iniciando verificación de bloqueo de IP con {retries} reintentos.")
    for i in range(retries):
        # Recargamos la página en cada intento para asegurar un estado limpio.
        driver.get("https://oficinajudicialvirtual.pjud.cl/")
        time.sleep(delay)

        # Intentar cerrar el popup de mantenimiento
        try:
            short_wait = WebDriverWait(driver, 5)
            cerrar_popup_button = short_wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Cerrar' and @data-dismiss='modal']"))
            )
            cerrar_popup_button.click()
            print(f"[{dia_id}] Popup de mantenimiento encontrado y cerrado.")
            time.sleep(1)
        except Exception:
            print(f"[{dia_id}] No se encontró popup de mantenimiento, continuando...")
        
        # La prueba más simple: ¿está el título correcto? Si no, es un bloqueo casi seguro.
        if "Oficina Judicial Virtual" not in driver.title:
            print(f"[{dia_id}] Verificación {i+1}/{retries}: Fallo. Título de la página: '{driver.title}'.")
            time.sleep(delay)
            continue # Pasamos al siguiente reintento

        # Si el título es correcto, intentamos el siguiente paso: hacer clic en "Consulta causas"
        try:
            wait = WebDriverWait(driver, 10)
            boton_causas = wait.until(EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Consulta causas']")))
            driver.execute_script("arguments[0].click();", boton_causas)
            time.sleep(2) # Añadimos una pausa para que la página cargue
            
            # Última prueba: ¿llegamos a la página de búsqueda?
            short_wait = WebDriverWait(driver, 10)
            short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="#BusFecha"]')))
            
            # Si llegamos hasta aquí, no estamos bloqueados.
            print(f"[{dia_id}] Verificación {i+1}/{retries}: Acceso exitoso. No hay bloqueo.")
            return False
        except Exception as e:
            print(f"[{dia_id}] Verificación {i+1}/{retries}: El título era correcto, pero no se pudo acceder a la sección de consultas. Error: {e}")
            time.sleep(delay)
            # Continuamos al siguiente reintento

    print(f"[{dia_id}] BLOQUEO CONFIRMADO después de {retries} reintentos.")
    return True