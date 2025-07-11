# Archivo: worker.py (Versión para Escenario 2: Apelaciones)

import time
import pandas as pd
import random
import json
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from utils_apelaciones import forzar_cierre_navegadores, is_ip_blocked_con_reintentos

# El checkpoint file se obtendrá de la tarea

def scrape_worker(task_info):
    task, lock, headless_mode, stop_event = task_info
    task_id = task['id']

    # --- Verificación inicial del evento de parada ---
    if stop_event.is_set():
        print(f"[{task_id}] Evento de parada activado. El worker no se iniciará.")
        return f"STOPPED_BY_EVENT:{task_id}"

    # Preferencias para optimizar el navegador (bloquear imágenes)
    chrome_prefs = {
        "profile.managed_default_content_settings.images": 2
    }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", chrome_prefs)
    
    # --- INICIO: Silenciar logs de la consola ---
    options.add_argument('--log-level=3')
    # --- FIN: Silenciar logs de la consola ---

    # Argumentos para evitar la detección de automatización
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    if headless_mode:
        print(f"[{task_id}] Ejecutando en modo HEADLESS.")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    else:
        print(f"[{task_id}] Ejecutando en modo VISIBLE (fuera de pantalla).")
        # Posiciona la ventana fuera del área visible del monitor
        options.add_argument("--window-position=-2000,0")
        # Inicia la ventana maximizada para un comportamiento estable
        options.add_argument("--start-maximized")
        # Deshabilita la barra "Chrome está siendo controlado..."
        options.add_argument("--disable-infobars")

    profile_path = None
    driver = None
    try:
        # Define un path de perfil único y predecible DENTRO del try
        profile_path = os.path.join(tempfile.gettempdir(), f"pjud_profile_{task_id}")
        
        # Asigna el perfil único a la instancia de Chrome
        options.add_argument(f"--user-data-dir={profile_path}")
        
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        wait = WebDriverWait(driver, 25)

        # --- Verificación de IP ---
        if is_ip_blocked_con_reintentos(driver, task_id):
            print(f"[{task_id}] Bloqueo de IP detectado al inicio. Señalando parada.")
            stop_event.set()
            forzar_cierre_navegadores()
            if driver: driver.quit()
            return f"IP_BLOCKED:{task_id}"
            
        print(f"[{task_id}] Acceso verificado. Procediendo con el scraping.")

        # --- Extracción de información de la tarea ---
        ruta_salida = task['ruta_salida']
        fecha_desde_str = task['fecha_desde_str']
        fecha_hasta_str = task['fecha_hasta_str']
        fecha_str = task['fecha']  # Para compatibilidad con el código existente
        corte_id = task['corte_id']
        corte_nombre = task['corte_nombre']
        checkpoint_file = os.path.join(ruta_salida, 'checkpoint_apelaciones.json')
        
        try:
            print(f"[{task_id}] Asegurando clic en 'Búsqueda por Fecha'...")
            # Espera antes de hacer clic en "Consulta causas"
            time.sleep(18)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            # Espera después de hacer clic en "Consulta causas" y antes de filtrar por fecha
            time.sleep(18)
            print(f"[{task_id}] Seleccionando Competencia 'Corte Apelaciones'...")
            select_competencia = Select(wait.until(EC.presence_of_element_located((By.ID, "fecCompetencia"))))
            select_competencia.select_by_value("2")

            # --- INICIO: Espera inteligente para la carga AJAX de las cortes ---
            time.sleep(10)
            print(f"[{task_id}] Esperando a que la corte '{corte_nombre}' cargue en el menú...")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"#corteFec option[value='{corte_id}']"))
            )
            # --- FIN: Espera inteligente ---

            print(f"[{task_id}] Seleccionando Corte: {corte_nombre}...")
            select_corte_element = driver.find_element(By.ID, "corteFec")
            select_corte = Select(select_corte_element)
            select_corte.select_by_value(corte_id)
            time.sleep(2)
        
            input_desde = wait.until(EC.presence_of_element_located((By.ID, "fecDesde")))
            input_hasta = wait.until(EC.presence_of_element_located((By.ID, "fecHasta")))
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_hasta)
            time.sleep(2)
            
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
        except Exception as e:
            print(f"Error grave en worker {task_id} durante la configuración de filtros: {e}")
            screenshot_path = os.path.join(ruta_salida, f"error_screenshot_{task_id}.png")
            driver.save_screenshot(screenshot_path)
            stop_event.set()
            return f"ERROR:{task_id}"

        
        pagina_a_empezar = task.get('pagina_a_empezar', 1)
        pagina_actual = 1

        while not stop_event.is_set():
            if pagina_actual < pagina_a_empezar:
                pass

            print(f"--- [{task_id}] Procesando Página {pagina_actual} ---")
            try:
                wait.until(EC.visibility_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                print(f"[{task_id}] La tabla de resultados no apareció. Verificando bloqueo.")
                if is_ip_blocked_con_reintentos(driver, task_id):
                    stop_event.set()
                    return f"IP_BLOCKED:{task_id}"
                else:
                    print(f"[{task_id}] No parece ser un bloqueo. Se asume que no hay más resultados.")
                    break
            
            tabla_principal = driver.find_element(By.ID, "dtaTableDetalleFecha")
            headers_principales_elems = tabla_principal.find_elements(By.XPATH, ".//thead/tr/th")
            headers_principales = {header.text.strip(): i for i, header in enumerate(headers_principales_elems)}
            
            filas_causas = driver.find_elements(By.XPATH, "//table[@id='dtaTableDetalleFecha']/tbody/tr")
            registros_pagina = []
            
            for i in range(len(filas_causas)):
                if stop_event.is_set(): break
                try:
                    tabla_fresca = wait.until(EC.presence_of_element_located((By.ID, "dtaTableDetalleFecha")))
                    fila = tabla_fresca.find_elements(By.XPATH, ".//tbody/tr")[i]
                    
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    if not celdas or len(celdas) < 2: continue

                    # --- Inicio: Construcción dinámica de observaciones ---
                    observaciones_parts = []
                    for header, index in headers_principales.items():
                        if index < len(celdas):
                            valor = celdas[index].text.strip()
                            if valor: # Solo añadir si la celda tiene contenido
                                observaciones_parts.append(f"{header}: {valor}")
                    
                    observaciones = " | ".join(observaciones_parts)
                    # --- Fin: Construcción dinámica de observaciones ---

                    lupa = fila.find_element(By.CSS_SELECTOR, "a[href='#modalDetalleApelaciones']")
                    lupa.click()

                    modal_selector = "#modalDetalleApelaciones"
                    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, modal_selector)))

                    if "causa se encuentra reservada" not in modal.text:
                        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#litigantesApe"]'))).click()
                        try:
                            tabla_litigantes = WebDriverWait(driver, 3).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, '#litigantesApe table'))
                            )
                            for fila_lit in tabla_litigantes.find_elements(By.XPATH, ".//tbody/tr"):
                                celdas_lit = fila_lit.find_elements(By.TAG_NAME, "td")
                                if len(celdas_lit) < 4: continue
                                registros_pagina.append({
                                    "NOMBRE": celdas_lit[3].text, "DOCUMENTO": celdas_lit[1].text,
                                    "CARGO": celdas_lit[0].text, "INSTITUCION": corte_nombre,
                                    "OBSERVACIONES": observaciones
                                })
                        except TimeoutException:
                            pass

                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'{modal_selector} .close'))).click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_selector)))

                except StaleElementReferenceException:
                    print(f"[{task_id}] Stale element en la página {pagina_actual}. Se reintentará la página.")
                    break 
                except Exception as e_row:
                    # Imprimimos solo el tipo de error y la primera línea del mensaje.
                    error_message = str(e_row).split('\n')[0]
                    print(f"[{task_id}] Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}")
                    continue
            else: 
                if registros_pagina:
                    df = pd.DataFrame(registros_pagina)
                    csv_path = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                    header = not os.path.exists(csv_path)
                    df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
                
                with lock:
                    try:
                        # Abrir en modo lectura y escritura, crear si no existe
                        with open(checkpoint_file, 'r+') as f:
                            checkpoint_data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        checkpoint_data = {}

                    # Actualizar la información de la tarea actual
                    checkpoint_data[task_id] = {
                        "status": "in_progress",
                        "last_page": pagina_actual
                    }

                    # Escribir de vuelta al archivo
                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoint_data, f, indent=4)
                    
                    print(f"[{task_id}] Checkpoint guardado en página {pagina_actual}.")

                try:
                    # 1. Obtener número de página activa ANTES del clic
                    pagina_activa_antes = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()
                    print(f"[{task_id}] Página activa actual: {pagina_activa_antes}.")

                    # 2. Intentar hacer clic en 'Siguiente'
                    boton_siguiente = wait.until(EC.element_to_be_clickable((By.ID, "sigId")))
                    driver.execute_script("arguments[0].click();", boton_siguiente)
                    
                    # 3. Esperar a que la página reaccione
                    time.sleep(4) # Pausa crucial para que el DOM se actualice

                    # 4. Obtener número de página activa DESPUÉS del clic
                    pagina_activa_despues = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()

                    # 5. Comparar para detectar bucle infinito
                    if pagina_activa_antes == pagina_activa_despues:
                        print(f"[{task_id}] El número de página no cambió ({pagina_activa_despues}). Fin de la paginación detectado.")
                        break # Salir del bucle while
                    else:
                        print(f"[{task_id}] Paginación exitosa a la página {pagina_activa_despues}.")
                        pagina_actual = int(pagina_activa_despues)
                        
                except (NoSuchElementException, TimeoutException):
                    # Esto ocurre si el botón 'Siguiente' o el paginador desaparecen por completo
                    print(f"[{task_id}] No se encontró el botón 'Siguiente' o el paginador. Fin de la tarea.")
                    break # Salir del bucle while
                continue
            
            print(f"[{task_id}] Reintentando página {pagina_actual}...")
            time.sleep(2)
            continue


        # --- Finalización ---
        if not stop_event.is_set():
            with lock:
                try:
                    with open(checkpoint_file, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                
                # Actualizar el estado de la tarea a 'completed'
                if task_id in checkpoint_data:
                    checkpoint_data[task_id]['status'] = 'completed'
                else:
                    checkpoint_data[task_id] = {'status': 'completed'}
                
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)

            print(f"[{task_id}] Tarea completada y marcada en checkpoint.")
            return f"COMPLETED:{task_id}"
        else:
            print(f"[{task_id}] Tarea detenida por evento de parada.")
            return f"STOPPED:{task_id}"

    except Exception as e:
        # Imprimimos solo el tipo de error y la primera línea del mensaje.
        error_message = str(e).split('\n')[0]
        print(f"Error grave en worker {task_id}: {type(e).__name__} - {error_message}")
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()
