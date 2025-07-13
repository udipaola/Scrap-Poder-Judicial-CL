# Archivo: worker_suprema.py (CORREGIDO)

import time
import pandas as pd
import random
import json
import os
import tempfile
import logging
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from utils_suprema import forzar_cierre_navegadores, is_ip_blocked_con_reintentos
from selenium.webdriver.common.keys import Keys
from pagination_utils import (
    get_current_page_number,
    navigate_to_next_page,
    navigate_to_page,
    apply_checkpoint_pagination
)

# El checkpoint file se obtendrá de la tarea

# Variable global para controlar el modo debug
DEBUG_MODE = False


MAX_REINTENTOS_PAGINA = 3

# Lock para sincronizar el logging entre threads
log_lock = threading.Lock()

def log_progress(message, worker_id=None):
    """Log de progreso general del worker"""
    with log_lock:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[{worker_id}]" if worker_id else ""
        print(f"[{timestamp}] {prefix} PROGRESS: {message}")

def log_error(message, worker_id=None):
    """Log de errores del worker"""
    with log_lock:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[{worker_id}]" if worker_id else ""
        print(f"[{timestamp}] {prefix} ERROR: {message}")

def log_debug(message, worker_id=None):
    """Log de debug detallado (solo si DEBUG_MODE está activado)"""
    if DEBUG_MODE:
        with log_lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            prefix = f"[{worker_id}]" if worker_id else ""
            print(f"[{timestamp}] {prefix} DEBUG: {message}")

def log_worker_status(message, worker_id=None):
    """Log de estado del worker (inicio, fin, etc.)"""
    with log_lock:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[{worker_id}]" if worker_id else ""
        print(f"[{timestamp}] {prefix} STATUS: {message}")

def scrape_worker(task):
    """
    Tarea principal que extrae, transforma y carga los datos.
    """
    dia_a_procesar, lock, headless_mode, stop_event, debug_mode, total_workers = task
    dia_id = dia_a_procesar['id']
    
    # Configurar el modo debug globalmente
    global DEBUG_MODE
    DEBUG_MODE = debug_mode

    if stop_event.is_set():
        log_worker_status("Evento de parada activado. El worker no se iniciará.", dia_id)
        return f"STOPPED_BY_EVENT:{dia_id}"

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    if headless_mode:
        options.add_argument("--window-position=-2000,0")
        log_debug("Modo headless activado", dia_id)
    else:
        log_debug("Modo visible activado", dia_id)

    profile_path = None
    driver = None
    try:
        # Define un path de perfil único y predecible DENTRO del try
        profile_path = os.path.join(tempfile.gettempdir(), f"pjud_profile_{dia_id}")
        
        # Asigna el perfil único a la instancia de Chrome
        options.add_argument(f"--user-data-dir={profile_path}")
        
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        wait = WebDriverWait(driver, 25) # Aumentamos un poco el wait general

        if is_ip_blocked_con_reintentos(driver, dia_id):
            log_error("Bloqueo de IP detectado al inicio. Señalando parada.", dia_id)
            stop_event.set()
            return f"IP_BLOCKED:{dia_id}"

        log_progress("Acceso verificado. Procediendo con el scraping.", dia_id)

        # --- Extracción de información de la tarea ---
        ruta_salida = dia_a_procesar['ruta_salida']
        fecha_desde_str = dia_a_procesar['fecha_desde_str']
        fecha_hasta_str = dia_a_procesar['fecha_hasta_str']
        fecha_str = dia_a_procesar['fecha']  # Para compatibilidad con el código existente
        checkpoint_file = os.path.join(ruta_salida, 'checkpoint_suprema.json')
        try:
            log_debug("Haciendo clic en 'Búsqueda por Fecha'", dia_id)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            
            log_debug(f"Configurando fechas: desde {fecha_str} hasta {fecha_str}", dia_id)
            input_desde = wait.until(EC.presence_of_element_located((By.ID, "fecDesde")))
            input_hasta = wait.until(EC.presence_of_element_located((By.ID, "fecHasta")))
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_hasta)
            time.sleep(1)
            
            log_debug("Haciendo clic en el botón de consulta", dia_id)
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
        except Exception as e:
            log_error(f"Error grave durante la configuración de filtros: {e}", dia_id)
            screenshot_path = os.path.join(ruta_salida, f"error_screenshot_{dia_id}.png")
            driver.save_screenshot(screenshot_path)
            log_debug(f"Screenshot guardado en: {screenshot_path}", dia_id)
            stop_event.set()
            return f"ERROR:{dia_id}"
        
        pagina_inicial = dia_a_procesar.get('pagina_a_empezar', 1)
        
        # Aplicación de checkpoint con verificación robusta
        if pagina_inicial > 1:
            log_progress(f"Saltando a página inicial {pagina_inicial} desde checkpoint...", dia_id)
            if apply_checkpoint_pagination(driver, pagina_inicial, dia_id, total_workers, DEBUG_MODE, log_progress, log_error):
                pagina_actual = pagina_inicial
                log_progress(f"Checkpoint aplicado exitosamente. Iniciando desde página {pagina_actual}", dia_id)
            else:
                log_progress(f"Error aplicando checkpoint. Iniciando desde página 1", dia_id)
                pagina_actual = 1
        else:
            pagina_actual = 1
            log_progress(f"Iniciando desde página 1", dia_id)
        
        # Verificación adicional antes de procesar
        pagina_verificada = get_current_page_number(driver)
        if pagina_verificada != pagina_actual:
            log_progress(f"ADVERTENCIA: Discrepancia de página. Esperada: {pagina_actual}, Real: {pagina_verificada}", dia_id)
            pagina_actual = pagina_verificada

        # ==== INICIO DE LA LÓGICA ROBUSTA DE PAGINACIÓN ====
        reintentos_pagina = 0
        while not stop_event.is_set():

            log_worker_status(f"Procesando Página {pagina_actual}", dia_id)
            try:
                wait.until(EC.visibility_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                log_progress("La tabla de resultados no apareció. Verificando bloqueo.", dia_id)
                if is_ip_blocked_con_reintentos(driver, dia_id):
                    stop_event.set()
                    return f"IP_BLOCKED:{dia_id}"
                else:
                    log_progress("No parece ser un bloqueo. Se asume que no hay más resultados.", dia_id)
                    break
            
            filas_causas = driver.find_elements(By.XPATH, "//table[@id='dtaTableDetalleFecha']/tbody/tr")
            registros_pagina = []
            error_reintentar_pagina = False
            # Bucle 'for' para procesar filas con 'else' para la paginación
            for i in range(len(filas_causas)):
                if stop_event.is_set(): break
                try:
                    tabla_fresca = wait.until(EC.presence_of_element_located((By.ID, "dtaTableDetalleFecha")))
                    fila = tabla_fresca.find_elements(By.XPATH, ".//tbody/tr")[i]
                    
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    if not celdas or len(celdas) < 2: continue

                    # (Tu lógica de extracción de datos aquí... es correcta)
                    headers_principales_elems = tabla_fresca.find_elements(By.XPATH, ".//thead/tr/th")
                    headers_principales = {header.text.strip(): i for i, header in enumerate(headers_principales_elems)}
                    rol = celdas[headers_principales.get('Rol', 1)].text
                    observaciones = f"Rol: {rol} | Recurso: {celdas[headers_principales.get('Tipo Recurso', 2)].text} | Ingreso: {celdas[headers_principales.get('Fecha Ingreso', 4)].text} | Estado: {celdas[headers_principales.get('Estado Causa', 5)].text}"
                    
                    try:
                        celdas[0].find_element(By.TAG_NAME, 'a').click()
                    except (TimeoutException, Exception) as e_click:
                        from selenium.common.exceptions import ElementClickInterceptedException
                        if isinstance(e_click, ElementClickInterceptedException) or 'element click intercepted' in str(e_click):
                            log_error("ElementClickInterceptedException al hacer click en la lupa. Reintentando página completa...", dia_id)
                            error_reintentar_pagina = True
                            break
                        else:
                            raise
                    
                    # (Tu lógica de modal aquí... es correcta)
                    try:
                        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleSuprema")))
                    except TimeoutException:
                        log_error("Timeout esperando modal. Reintentando página completa...", dia_id)
                        error_reintentar_pagina = True
                        break
                    if "causa se encuentra reservada" not in modal.text:
                        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#litigantesSup"]'))).click()
                        try:
                            tabla_litigantes = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.ID, "litigantesSup")))
                            for fila_lit in tabla_litigantes.find_elements(By.XPATH, ".//tbody/tr"):
                                celdas_lit = fila_lit.find_elements(By.TAG_NAME, "td")
                                if len(celdas_lit) < 4: continue
                                registros_pagina.append({
                                    "NOMBRE": celdas_lit[3].text, "DOCUMENTO": celdas_lit[1].text,
                                    "CARGO": celdas_lit[0].text, "INSTITUCION": "Corte Suprema",
                                    "OBSERVACIONES": observaciones
                                })
                        except TimeoutException:
                            pass
                    
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#modalDetalleSuprema .close'))).click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleSuprema")))

                except StaleElementReferenceException:
                    log_error(f"Stale element en la página {pagina_actual}. Se reintentará la página completa.", dia_id)
                    error_reintentar_pagina = True
                    break
                except Exception as e_row:
                    from selenium.common.exceptions import ElementClickInterceptedException
                    error_message = str(e_row).split('\n')[0]
                    if isinstance(e_row, ElementClickInterceptedException) or 'element click intercepted' in error_message:
                        log_error("ElementClickInterceptedException detectado. Reintentando página completa...", dia_id)
                        error_reintentar_pagina = True
                        break
                    log_error(f"Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}", dia_id)
                    continue
            if error_reintentar_pagina:
                reintentos_pagina += 1
                if reintentos_pagina > MAX_REINTENTOS_PAGINA:
                    log_error(f"Se superó el máximo de reintentos ({MAX_REINTENTOS_PAGINA}) para la página {pagina_actual}. Cerrando worker y notificando al main para reintentar desde el checkpoint...", dia_id)
                    if driver:
                        driver.quit()
                    return f"RETRY:{dia_id}:page_{pagina_actual}"
                else:
                    log_progress(f"Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})...", dia_id)
                    time.sleep(3)
                continue
            
            # Este bloque 'else' solo se ejecuta si el 'for' termina SIN un 'break'
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                csv_path = os.path.join(ruta_salida, f"resultados_{dia_id}.csv")
                header = not os.path.exists(csv_path)
                df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
                log_progress(f"Guardados {len(registros_pagina)} registros en {csv_path}", dia_id)
            
            with lock:
                # (Tu lógica de checkpoint aquí... es correcta)
                try:
                    with open(checkpoint_file, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                checkpoint_data[dia_id] = {"status": "in_progress", "last_page": pagina_actual}
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
                log_debug(f"Checkpoint guardado en página {pagina_actual}", dia_id)

            # Navegar a la siguiente página usando función centralizada
            if navigate_to_next_page(driver, dia_id, total_workers, DEBUG_MODE, log_debug, log_error):
                pagina_actual = get_current_page_number(driver)
                log_progress(f"Paginación exitosa a la página {pagina_actual}", dia_id)
            else:
                log_progress("Fin de la paginación detectado.", dia_id)
                break
            continue
        # ==== FIN DE LA LÓGICA ROBUSTA ====

        if not stop_event.is_set():
            with lock:
                # (Tu lógica de marcar como completado aquí... es correcta)
                try:
                    with open(checkpoint_file, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                if dia_id in checkpoint_data:
                    checkpoint_data[dia_id]['status'] = 'completed'
                else:
                    checkpoint_data[dia_id] = {'status': 'completed'}
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
            log_worker_status("Tarea completada", dia_id)
            return f"COMPLETED:{dia_id}"
        else:
            log_worker_status("Tarea detenida por evento de parada", dia_id)
            return f"STOPPED:{dia_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        log_error(f"Error MUY grave en worker: {type(e).__name__} - {error_message}", dia_id)
        stop_event.set() # Señalamos a todos que paren
        return f"ERROR:{dia_id}" # Retornamos un error claro
    finally:
        if driver:
            driver.quit()
        log_worker_status("Worker finalizado", dia_id)