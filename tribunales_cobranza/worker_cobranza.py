# Archivo: worker.py

import sys
import os
# --- Asegura que el path raíz esté en sys.path para los imports absolutos ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import threading
import logging
from utils_cobranza import forzar_cierre_navegadores, is_ip_blocked_con_reintentos
from selenium.webdriver.common.keys import Keys
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.pagination_utils import (
    get_current_page_number,
    navigate_to_next_page,
    navigate_to_page,
    apply_checkpoint_pagination
)

# Funciones de paginación movidas a utils/pagination_utils.py

# Configurar logging para reducir ruido
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Sistema de logging ultra-limpio
DEBUG_MODE = False  # Cambiar a True solo para debugging

def log_progress(task_id, message):
    """Log para mensajes de progreso esenciales"""
    print(f"[Worker {task_id}] {message}")

def log_error(task_id, message):
    """Log para errores críticos"""
    print(f"[Worker {task_id}] ERROR: {message}")

def log_debug(task_id, message):
    """Log para debug (solo visible si DEBUG_MODE está activado)"""
    if DEBUG_MODE:
        print(f"[Worker {task_id}] DEBUG: {message}")

def log_worker_status(task_id, total_workers, status, details=""):
    """Log conciso del estado del worker"""
    print(f"Worker {task_id}/{total_workers}: {status} {details}")

import tempfile

# Constantes para manejo de errores
MAX_REINTENTOS_PAGINA = 3

def scrape_worker(task_info):
    task, lock, headless_mode, stop_event, debug_mode = task_info
    task_id = task['id']
    total_workers = task.get('total_workers', 1)
    
    # Configurar DEBUG_MODE basado en el parámetro recibido
    global DEBUG_MODE
    DEBUG_MODE = debug_mode

    # --- Verificación inicial del evento de parada ---
    if stop_event.is_set():
        log_worker_status(task_id, total_workers, "DETENIDO", "evento de parada")
        return f"STOPPED_BY_EVENT:{task_id}"
    
    log_worker_status(task_id, total_workers, "INICIANDO", "verificando IP")

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    if headless_mode:
        options.add_argument("--window-position=-2000,0")

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
        log_debug(task_id, "Verificando bloqueo de IP")
        
        if is_ip_blocked_con_reintentos(driver, task_id):
            log_worker_status(task_id, total_workers, "ERROR", "IP bloqueada")
            stop_event.set()
            return f"IP_BLOCKED:{task_id}"
            
        log_worker_status(task_id, total_workers, "CONFIGURANDO", "filtros de búsqueda")

        # TAREA 2.1: Reemplazar el desempaquetado de la tarea por esta versión genérica.
        
        # Extraer información de la nueva estructura de tareas
        ruta_salida = task['ruta_salida']
        fecha_desde_str = task['fecha_desde_str']
        fecha_hasta_str = task['fecha_hasta_str']
        competencia_nombre = task['competencia_nombre']
        competencia_value = task['competencia_value']
        selector_id = task['selector_id']
        
        # Crear directorio de salida si no existe
        os.makedirs(ruta_salida, exist_ok=True)
        
        # Definir archivo de checkpoint centralizado
        CHECKPOINT_FILE = os.path.join(ruta_salida, 'checkpoint_tribunales_cobranza.json')

        # Determinar las claves correctas para el ID y el nombre del ítem
        item_id_key = next((key for key in task if key.endswith('_id') and key != 'id' and key != 'selector_id'), None)
        item_nombre_key = next((key for key in task if key.endswith('_nombre') and key != 'competencia_nombre'), None)
        
        if not item_id_key or not item_nombre_key:
            raise ValueError(f"No se pudieron determinar las claves de item para la tarea: {task_id}")

        item_id = task[item_id_key]
        item_nombre = task[item_nombre_key]

        # TAREA 2.2: Reemplazar toda la sección de "Aplicación de filtros"
        # hasta el clic en "btnConConsultaFec" con este bloque unificado.

        # --- INICIO: LÓGICA DE SELECCIÓN DE FILTROS UNIFICADA ---
        try:
            # Paso 1: Navegar a la sección de búsqueda por fecha
            log_debug(task_id, "Configurando filtros")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            
            # Paso 2: Seleccionar la Competencia principal (ej. Civil)
            log_debug(task_id, f"Seleccionando Competencia '{competencia_nombre}'")
            time.sleep(1) # Pequeña pausa para asegurar que la UI se estabilice
            select_competencia_element = wait.until(EC.visibility_of_element_located((By.ID, "fecCompetencia")))
            select_competencia = Select(select_competencia_element)
            select_competencia.select_by_value(competencia_value)

            log_debug(task_id, "Esperando carga de tribunales")
            time.sleep(2)

            # Paso 3: Espera robusta con LAMBDA a que el menú secundario se pueble vía AJAX
            log_debug(task_id, f"Esperando menú {selector_id}")
            wait.until(
                lambda d: len(Select(d.find_element(By.ID, selector_id)).options) > 1
            )

            # Paso 4: Seleccionar el ítem específico (Corte o Tribunal)
            log_debug(task_id, f"Seleccionando '{item_nombre}'")
            select_item = Select(driver.find_element(By.ID, selector_id))
            select_item.select_by_value(item_id)
        
            # Paso 5: Ingresar fechas y buscar
            input_desde = driver.find_element(By.ID, "fecDesde")
            input_hasta = driver.find_element(By.ID, "fecHasta")
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_desde_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_hasta_str}';", input_hasta)
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
            
            log_debug(task_id, "Esperando carga de resultados")
            time.sleep(3);
            
        except Exception as e:
            log_error(task_id, f"Error en la configuración de filtros: {e}")
            # Capturar screenshot de error
            try:
                screenshot_path = os.path.join(ruta_salida, f"error_filtros_{task_id}.png")
                driver.save_screenshot(screenshot_path)
                log_progress(task_id, f"Screenshot de error guardado en: {screenshot_path}")
            except Exception as screenshot_error:
                log_error(task_id, f"Error al guardar screenshot: {screenshot_error}")
            return f"ERROR_FILTROS:{task_id}"

        # --- FIN: LÓGICA DE SELECCIÓN DE FILTROS UNIFICADA ---

        # Aplicación de checkpoint con verificación robusta usando utilidades centralizadas
        pagina_inicial = task.get('pagina_a_empezar', 1)
        if pagina_inicial > 1:
            if apply_checkpoint_pagination(driver, pagina_inicial, task_id, total_workers, DEBUG_MODE, log_progress, log_error):
                pagina_actual = pagina_inicial
            else:
                pagina_actual = 1
        else:
            pagina_actual = 1
        
        # Confirmar página actual
        pagina_verificada = get_current_page_number(driver)
        if pagina_verificada != pagina_actual:
            log_progress(task_id, f"ADVERTENCIA: Discrepancia de página. Esperada: {pagina_actual}, Real: {pagina_verificada}")
            pagina_actual = pagina_verificada
        log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")

        # Variables para manejo de reintentos
        reintentos_pagina = 0
        error_reintentar_pagina = False

        while not stop_event.is_set():
            registros_pagina = []
            
            # Verificar si hay mensaje de "No se encontraron resultados"
            try:
                no_results = driver.find_element(By.XPATH, "//td[contains(text(), 'No se encontraron resultados')]")
                log_progress(task_id, "Sin resultados - Finalizando")
                break
            except NoSuchElementException:
                pass  # Hay resultados, continuar
            
            log_debug(task_id, f"Procesando página {pagina_actual}")

            # Esperar a que la tabla se cargue
            try:
                wait.until(EC.presence_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                log_error(task_id, f"Timeout en página {pagina_actual}")
                break

            # Extraer datos de la página actual
            try:
                filas_causas = driver.find_elements(By.XPATH, "//tbody[@id='verDetalleFecha']/tr[td[2]]")
                headers_principales_elems = driver.find_elements(By.XPATH, "//table[@id='dtaTableDetalleFecha']/thead/tr/th")
                headers_principales = {header.text.strip(): i for i, header in enumerate(headers_principales_elems)}
                for i, fila in enumerate(filas_causas):
                    if stop_event.is_set():
                        break
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    if not celdas or len(celdas) < 6:
                        continue
                    # Mapeo de columnas para Cobranza
                    rit = celdas[headers_principales.get('Rit', 1)].text
                    tribunal = celdas[headers_principales.get('Tribunal', 2)].text
                    caratulado = celdas[headers_principales.get('Caratulado', 3)].text
                    fecha_ingreso = celdas[headers_principales.get('Fecha Ingreso', 4)].text
                    estado_causa = celdas[headers_principales.get('Estado Procesal', 6)].text
                    observaciones = f"RIT: {rit} | Tribunal: {tribunal} | Caratulado: {caratulado} | Fecha Ingreso: {fecha_ingreso} | Estado Procesal: {estado_causa}"
                    # Click en la lupa (detalle)
                    try:
                        boton_detalle = celdas[0].find_element(By.CSS_SELECTOR, ".toggle-modal")
                        driver.execute_script("arguments[0].click();", boton_detalle)
                    except ElementClickInterceptedException as e_click:
                        log_error(task_id, f"ElementClickInterceptedException en lupa: {e_click}")
                        error_reintentar_pagina = True
                        break
                    except Exception as e_click:
                        log_error(task_id, f"Error al hacer click en la lupa: {e_click}")
                        continue
                    # Esperar modal y extraer datos adicionales de cabecera
                    try:
                        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleCobranza")))
                        # Extraer tabla de cabecera clave-valor
                        datos_adicionales = {}
                        try:
                            tabla_cabecera = driver.find_element(By.CSS_SELECTOR, "#modalDetalleCobranza table.table-titulos")
                            filas_cab = tabla_cabecera.find_elements(By.TAG_NAME, "tr")
                            for fila_cab in filas_cab:
                                celdas_cab = fila_cab.find_elements(By.TAG_NAME, "td")
                                for celda in celdas_cab:
                                    txt = celda.text.strip()
                                    if ':' in txt:
                                        clave, valor = txt.split(':', 1)
                                        datos_adicionales[clave.strip()] = valor.strip()
                        except Exception:
                            pass
                        # Click en tab de litigantes si existe (puede estar ya activo)
                        try:
                            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#litigantesCob"]'))).click()
                        except Exception:
                            pass
                        # Extraer tabla de litigantes
                        tabla_litigantes = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#litigantesCob table")))
                        filas_lit = tabla_litigantes.find_elements(By.XPATH, ".//tbody/tr")
                        for fila_lit in filas_lit:
                            celdas_lit = fila_lit.find_elements(By.TAG_NAME, "td")
                            if len(celdas_lit) < 4:
                                continue
                            registros_pagina.append({
                                "NOMBRE": celdas_lit[3].text,
                                "DOCUMENTO": celdas_lit[1].text,
                                "CARGO": celdas_lit[0].text,
                                "INSTITUCION": tribunal,
                                "OBSERVACIONES": observaciones + " | " + " | ".join([f"{k}: {v}" for k,v in datos_adicionales.items()])
                            })
                    except Exception as e_modal:
                        log_error(task_id, f"Error extrayendo litigantes: {e_modal}")
                    finally:
                        # Cerrar modal
                        try:
                            driver.find_element(By.CSS_SELECTOR, "#modalDetalleCobranza .close").click()
                            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleCobranza")))
                        except Exception:
                            pass
            except ElementClickInterceptedException as e:
                log_error(task_id, f"ElementClickInterceptedException en procesamiento de filas: {e}")
                error_reintentar_pagina = True
                break
            except StaleElementReferenceException:
                log_error(task_id, "Error de referencia estancada. Reintentando la página")
                continue

            # Verificar si hay que reintentar por ElementClickInterceptedException
            if error_reintentar_pagina:
                reintentos_pagina += 1
                if reintentos_pagina > MAX_REINTENTOS_PAGINA:
                    log_error(task_id, f"Máximo de reintentos ({MAX_REINTENTOS_PAGINA}) alcanzado para página {pagina_actual}")
                    driver.quit()
                    return f"RETRY:{task_id}"
                else:
                    log_progress(task_id, f"Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})")
                    time.sleep(3)
                    error_reintentar_pagina = False
                    continue

            # Guardar datos y checkpoint
            if registros_pagina:
                log_progress(task_id, f"Guardando {len(registros_pagina)} registros")
                df = pd.DataFrame(registros_pagina)
                csv_path = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                header = not os.path.exists(csv_path)
                df = df[["NOMBRE", "DOCUMENTO", "CARGO", "INSTITUCION", "OBSERVACIONES"]]  # Orden y columnas fijas
                df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
            else:
                log_debug(task_id, "Página sin registros")
            
            with lock:
                try:
                    with open(CHECKPOINT_FILE, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}

                checkpoint_data[task_id] = {
                    "status": "in_progress",
                    "last_page": pagina_actual
                }

                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
                
                log_debug(task_id, f"Checkpoint guardado en página {pagina_actual}")

            # Navegación a la siguiente página usando utilidades centralizadas
            if not navigate_to_next_page(driver, task_id, total_workers, DEBUG_MODE, log_debug, log_error):
                log_progress(task_id, "Fin de la paginación detectado")
                break
            
            # Obtener nueva página actual
            pagina_actual = get_current_page_number(driver)
            log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")
                
            # Resetear variables de control para la siguiente iteración
            reintentos_pagina = 0
            error_reintentar_pagina = False

        # --- Finalización ---
        if not stop_event.is_set():
            with lock:
                try:
                    with open(CHECKPOINT_FILE, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                
                if task_id in checkpoint_data:
                    checkpoint_data[task_id]['status'] = 'completed'
                else:
                    checkpoint_data[task_id] = {'status': 'completed'}
                
                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)

            log_progress(task_id, "Tarea completada")
            log_worker_status(task_id, total_workers, "FINALIZADO", "")
            return f"COMPLETED:{task_id}"
        else:
            log_worker_status(task_id, total_workers, "DETENIDO", "por evento de parada")
            return f"STOPPED:{task_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        log_worker_status(task_id, total_workers, "ERROR", f"{type(e).__name__}")
        log_error(task_id, f"Error grave en worker: {error_message}")
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()
        log_worker_status(task_id, total_workers, "FINALIZADO", "")