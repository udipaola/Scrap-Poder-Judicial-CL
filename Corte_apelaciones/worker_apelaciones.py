# Archivo: worker.py (Versión para Escenario 2: Apelaciones)

import sys
import os
# Agregar el directorio padre al path para encontrar el módulo utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from utils_apelaciones import forzar_cierre_navegadores, is_ip_blocked_con_reintentos
from selenium.webdriver.common.keys import Keys
from utils.pagination_utils import (
    get_current_page_number,
    navigate_to_next_page,
    navigate_to_page,
    apply_checkpoint_pagination
)



# Variable global para controlar el modo debug
DEBUG_MODE = False

# Constante para máximo de reintentos de página
MAX_REINTENTOS_PAGINA = 3

# El checkpoint file se obtendrá de la tarea

def log_progress(message, task_id=None):
    """Log de progreso general del worker"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    thread_id = threading.current_thread().ident
    prefix = f"[{timestamp}][Thread-{thread_id}]"
    if task_id:
        prefix += f"[{task_id}]"
    print(f"{prefix}[PROGRESS] {message}")

def log_error(message, task_id=None):
    """Log de errores del worker"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    thread_id = threading.current_thread().ident
    prefix = f"[{timestamp}][Thread-{thread_id}]"
    if task_id:
        prefix += f"[{task_id}]"
    print(f"{prefix}[ERROR] {message}")

def log_debug(message, task_id=None):
    """Log de debug detallado (solo si DEBUG_MODE está activado)"""
    if not DEBUG_MODE:
        return
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    thread_id = threading.current_thread().ident
    prefix = f"[{timestamp}][Thread-{thread_id}]"
    if task_id:
        prefix += f"[{task_id}]"
    print(f"{prefix}[DEBUG] {message}")

def log_worker_status(message, task_id=None):
    """Log de estado del worker (inicio, fin, cambios importantes)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    thread_id = threading.current_thread().ident
    prefix = f"[{timestamp}][Thread-{thread_id}]"
    if task_id:
        prefix += f"[{task_id}]"
    print(f"{prefix}[WORKER] {message}")

def scrape_worker(task_info):
    global DEBUG_MODE
    task, lock, headless_mode, stop_event, debug_mode = task_info
    DEBUG_MODE = debug_mode
    task_id = task['id']

    # --- Verificación inicial del evento de parada ---
    if stop_event.is_set():
        log_worker_status("Evento de parada activado. El worker no se iniciará.", task_id)
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
        log_worker_status("Ejecutando en modo HEADLESS.", task_id)
        # Posiciona la ventana fuera del área visible del monitor
        options.add_argument("--window-position=-2000,0")
        options.add_argument("--window-size=1920,1080")
    else:
        log_worker_status("Ejecutando en modo VISIBLE.", task_id)
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
            log_worker_status("Bloqueo de IP detectado al inicio. Señalando parada.", task_id)
            stop_event.set()
            forzar_cierre_navegadores()
            if driver: driver.quit()
            return f"IP_BLOCKED:{task_id}"
            
        log_worker_status("Acceso verificado. Procediendo con el scraping.", task_id)

        # --- Extracción de información de la tarea ---
        ruta_salida = task['ruta_salida']
        fecha_desde_str = task['fecha_desde_str']
        fecha_hasta_str = task['fecha_hasta_str']
        fecha_str = task['fecha']  # Para compatibilidad con el código existente
        corte_id = task['corte_id']
        corte_nombre = task['corte_nombre']
        checkpoint_file = os.path.join(ruta_salida, 'checkpoint_apelaciones.json')
        
        try:
            log_debug("Asegurando clic en 'Búsqueda por Fecha'...", task_id)
            # Espera antes de hacer clic en "Consulta causas"
            time.sleep(18)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            # Espera después de hacer clic en "Consulta causas" y antes de filtrar por fecha
            time.sleep(18)
            log_debug("Seleccionando Competencia 'Corte Apelaciones'...", task_id)
            select_competencia = Select(wait.until(EC.presence_of_element_located((By.ID, "fecCompetencia"))))
            select_competencia.select_by_value("2")

            # --- INICIO: Espera inteligente para la carga AJAX de las cortes ---
            time.sleep(10)
            log_debug(f"Esperando a que la corte '{corte_nombre}' cargue en el menú...", task_id)
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"#corteFec option[value='{corte_id}']"))
            )
            # --- FIN: Espera inteligente ---

            log_debug(f"Seleccionando Corte: {corte_nombre}...", task_id)
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
            log_error(f"Error grave durante la configuración de filtros: {e}", task_id)
            screenshot_path = os.path.join(ruta_salida, f"error_screenshot_{task_id}.png")
            driver.save_screenshot(screenshot_path)
            log_progress(f"Screenshot de error guardado en: {screenshot_path}", task_id)
            stop_event.set()
            return f"ERROR:{task_id}"

        
        pagina_inicial = task.get('pagina_a_empezar', 1)
        
        # Aplicación de checkpoint con verificación robusta usando utils centralizados
        if pagina_inicial > 1:
            log_progress(f"Saltando a página inicial {pagina_inicial} desde checkpoint...", task_id)
            if apply_checkpoint_pagination(driver, pagina_inicial, task_id, 1, DEBUG_MODE, log_progress, log_error):
                pagina_actual = pagina_inicial
                log_progress(f"Checkpoint aplicado exitosamente. Iniciando desde página {pagina_actual}", task_id)
            else:
                log_progress(f"Error aplicando checkpoint. Iniciando desde página 1", task_id)
                pagina_actual = 1
        else:
            pagina_actual = 1
            log_progress(f"Iniciando desde página 1", task_id)
        
        # Verificación adicional antes de procesar
        pagina_verificada = get_current_page_number(driver)
        if pagina_verificada != pagina_actual:
            log_progress(f"ADVERTENCIA: Discrepancia de página. Esperada: {pagina_actual}, Real: {pagina_verificada}", task_id)
            pagina_actual = pagina_verificada
            
        reintentos_pagina = 0
        error_reintentar_pagina = False

        while not stop_event.is_set():

            log_worker_status(f"Procesando Página {pagina_actual}", task_id)
            try:
                wait.until(EC.visibility_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                log_error("La tabla de resultados no apareció. Verificando bloqueo.", task_id)
                if is_ip_blocked_con_reintentos(driver, task_id):
                    stop_event.set()
                    return f"IP_BLOCKED:{task_id}"
                else:
                    log_progress("No parece ser un bloqueo. Se asume que no hay más resultados.", task_id)
                    break
            
            tabla_principal = driver.find_element(By.ID, "dtaTableDetalleFecha")
            headers_principales_elems = tabla_principal.find_elements(By.XPATH, ".//thead/tr/th")
            headers_principales = {header.text.strip(): i for i, header in enumerate(headers_principales_elems)}
            
            filas_causas = driver.find_elements(By.XPATH, "//table[@id='dtaTableDetalleFecha']/tbody/tr")
            registros_pagina = []
            
            try:
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
                        try:
                            lupa.click()
                        except ElementClickInterceptedException:
                            log_error(f"ElementClickInterceptedException al hacer clic en lupa - fila {i}", task_id)
                            error_reintentar_pagina = True
                            break
                        except Exception as e_click:
                            log_error(f"Error al hacer clic en lupa - fila {i}: {e_click}", task_id)
                            continue

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
                        log_error(f"Stale element en la página {pagina_actual}. Se reintentará la página.", task_id)
                        break 
                    except Exception as e_row:
                        # Imprimimos solo el tipo de error y la primera línea del mensaje.
                        error_message = str(e_row).split('\n')[0]
                        log_error(f"Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}", task_id)
                        continue

            except ElementClickInterceptedException:
                log_error(f"ElementClickInterceptedException durante procesamiento de filas en página {pagina_actual}", task_id)
                error_reintentar_pagina = True
                break
            
            # Guardar datos y checkpoint
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                csv_path = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                header = not os.path.exists(csv_path)
                df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
                log_progress(f"Guardados {len(registros_pagina)} registros en página {pagina_actual}", task_id)
            else:
                log_debug(f"No se encontraron registros en página {pagina_actual}", task_id)
            
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
                
                log_debug(f"Checkpoint guardado en página {pagina_actual}", task_id)

            # --- INICIO: PAGINACIÓN ROBUSTA usando utils centralizados ---
            if not navigate_to_next_page(driver, task_id, 1, DEBUG_MODE, log_debug, log_error):
                log_worker_status("Fin de paginación detectado", task_id)
                break
            
            # Actualizar página actual
            pagina_actual = get_current_page_number(driver)
            log_worker_status(f"Avanzando a página {pagina_actual}", task_id)
            reintentos_pagina = 0  # Reset reintentos al cambiar página exitosamente
            # --- FIN: PAGINACIÓN ROBUSTA ---
            
            # Manejo de reintentos por ElementClickInterceptedException
            if error_reintentar_pagina:
                reintentos_pagina += 1
                if reintentos_pagina > MAX_REINTENTOS_PAGINA:
                    log_error(f"Máximo de reintentos ({MAX_REINTENTOS_PAGINA}) alcanzado en página {pagina_actual}. Enviando señal RETRY.", task_id)
                    driver.quit()
                    return f"RETRY:{task_id}"
                else:
                    log_progress(f"Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})...", task_id)
                    time.sleep(3)
                    error_reintentar_pagina = False
                    continue
            else:
                # Reset reintentos si no hay error
                reintentos_pagina = 0


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

            log_progress("Tarea completada y marcada en checkpoint.", task_id)
            log_worker_status("TAREA COMPLETADA", task_id)
            return f"COMPLETED:{task_id}"
        else:
            log_worker_status("Tarea detenida por evento de parada.", task_id)
            return f"STOPPED:{task_id}"

    except Exception as e:
        # Imprimimos solo el tipo de error y la primera línea del mensaje.
        error_message = str(e).split('\n')[0]
        log_worker_status(f"ERROR CRÍTICO: {type(e).__name__} - {error_message}", task_id)
        log_error(f"Error grave en worker: {error_message}", task_id)
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()
        log_worker_status("Worker finalizado", task_id)
