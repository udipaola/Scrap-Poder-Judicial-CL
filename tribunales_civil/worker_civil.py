# Archivo: worker.py

import sys
import os
# --- Asegura que el path raíz esté en sys.path para los imports absolutos ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import pandas as pd
import random
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from utils_civil import forzar_cierre_navegadores, is_ip_blocked_con_reintentos, log_worker_status, log_debug, log_progress, log_error
from selenium.webdriver.common.keys import Keys
import logging
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

# Constantes para manejo de errores robusto
MAX_REINTENTOS_PAGINA = 3

# Funciones de logging ahora importadas desde utils_civil

# Checkpoint file will be determined from task info

import tempfile

def scrape_worker(task_info):
    task, lock, headless_mode, debug_mode, stop_event = task_info
    task_id = task['id']
    total_workers = task.get('total_workers', 1)
    
    # Configurar DEBUG_MODE basado en el parámetro recibido
    global DEBUG_MODE
    DEBUG_MODE = debug_mode
    
    # 1. Extraer la ruta de salida y las fechas
    ruta_salida = task['ruta_salida']
    fecha_desde_str = task['fecha_desde']
    fecha_hasta_str = task['fecha_hasta']
    
    # --- Verificación inicial del evento de parada ---
    if stop_event.is_set():
        log_worker_status(task_id, total_workers, "DETENIDO", "evento de parada")
        return f"STOPPED_BY_EVENT:{task_id}"

    profile_path = None
    driver = None
    try:
        profile_path = os.path.join(tempfile.gettempdir(), f"pjud_profile_{task_id}")
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        if headless_mode:
            options.add_argument("--window-position=-2000,0")

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        wait = WebDriverWait(driver, 25)

        # --- Verificación de IP ---
        log_worker_status(task_id, total_workers, "INICIANDO", "verificando IP")
        
        if is_ip_blocked_con_reintentos(driver, task_id):
            log_worker_status(task_id, total_workers, "ERROR", "IP bloqueada")
            stop_event.set()
            return f"IP_BLOCKED:{task_id}"
            
        log_worker_status(task_id, total_workers, "CONFIGURANDO", "filtros de búsqueda")

        # 2. Desempaquetado genérico de la tarea
        competencia_nombre = task['competencia_nombre']
        competencia_value = task['competencia_value']
        selector_id = task['selector_id']

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
            log_debug(task_id, total_workers, "Configurando filtros", DEBUG_MODE)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            
            # Paso 2: Seleccionar la Competencia principal (ej. Civil)
            time.sleep(1) # Pequeña pausa para asegurar que la UI se estabilice
            select_competencia_element = wait.until(EC.visibility_of_element_located((By.ID, "fecCompetencia")))
            select_competencia = Select(select_competencia_element)
            select_competencia.select_by_value(competencia_value)

            time.sleep(2)

            # Paso 3: Espera robusta con LAMBDA a que el menú secundario se pueble vía AJAX
            wait.until(
                lambda d: len(Select(d.find_element(By.ID, selector_id)).options) > 1
            )

            # Paso 4: Seleccionar el ítem específico (Corte o Tribunal)
            time.sleep(1)  # Espera breve para que cargue el listado de tribunales
            select_item = Select(driver.find_element(By.ID, selector_id))
            select_item.select_by_value(item_id)
        
            # Paso 5: Ingresar fechas y buscar (usando rango de fechas)
            input_desde = driver.find_element(By.ID, "fecDesde")
            input_hasta = driver.find_element(By.ID, "fecHasta")
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_desde_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_hasta_str}';", input_hasta)
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
            
            time.sleep(3);
            
        except Exception as e:
            log_error(task_id, total_workers, f"Error en la configuración de filtros: {e}")
            # Capturar screenshot de error
            try:
                screenshot_path = os.path.join(ruta_salida, f"error_filtros_{task_id}.png")
                driver.save_screenshot(screenshot_path)
                log_progress(task_id, total_workers, f"Screenshot de error guardado en: {screenshot_path}")
            except Exception as screenshot_error:
                log_error(task_id, total_workers, f"Error al guardar screenshot: {screenshot_error}")
            return f"ERROR_FILTROS:{task_id}"

        # --- FIN: LÓGICA DE SELECCIÓN DE FILTROS UNIFICADA ---

        pagina_inicial = task.get('pagina_a_empezar', 1)
        
        # Aplicación de checkpoint con verificación robusta usando utils
        if apply_checkpoint_pagination(driver, pagina_inicial, task_id, total_workers, DEBUG_MODE, log_progress, log_error):
            pagina_actual = get_current_page_number(driver)
            log_progress(task_id, total_workers, f"Checkpoint aplicado exitosamente. Iniciando desde página {pagina_actual}")
        else:
            pagina_actual = 1
            log_progress(task_id, total_workers, f"Error aplicando checkpoint. Iniciando desde página 1")
            
        log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")

        # Variables para manejo de reintentos
        reintentos_pagina = 0
        error_reintentar_pagina = False

        while not stop_event.is_set():
            registros_pagina = []
            
            # Verificar si hay mensaje de "No se encontraron resultados"
            try:
                no_results = driver.find_element(By.XPATH, "//td[contains(text(), 'No se encontraron resultados')]")
                log_progress(task_id, total_workers, "Sin resultados - Finalizando")
                break
            except NoSuchElementException:
                pass  # Hay resultados, continuar
            
            log_debug(task_id, total_workers, f"Procesando página {pagina_actual}", DEBUG_MODE)
            
            # Esperar a que la tabla se cargue
            try:
                wait.until(EC.presence_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                log_error(task_id, total_workers, f"Timeout en página {pagina_actual}")
                break

            # Extraer datos de la página actual
            try:
                filas_causas = driver.find_elements(By.XPATH, "//tbody[@id='verDetalleFecha']/tr[td[2]]")
                headers_principales_elems = driver.find_elements(By.XPATH, "//table[@id='dtaTableDetalleFecha']/thead/tr/th")
                headers_principales = {header.text.strip(): i for i, header in enumerate(headers_principales_elems)}
                for i, fila in enumerate(filas_causas):
                    if stop_event.is_set():
                        break
                    
                    try:
                        celdas = fila.find_elements(By.TAG_NAME, "td")
                        if not celdas or len(celdas) < 5:
                            continue
                        # Construir observaciones con datos principales
                        rol = celdas[headers_principales.get('Rol', 1)].text
                        fecha = celdas[headers_principales.get('Fecha', 2)].text
                        caratulado = celdas[headers_principales.get('Caratulado', 3)].text
                        tribunal = celdas[headers_principales.get('Tribunal', 4)].text
                        observaciones = f"Rol: {rol} | Fecha: {fecha} | Caratulado: {caratulado} | Tribunal: {tribunal}"
                        
                        # Click en la lupa (detalle) con detección de ElementClickInterceptedException
                        try:
                            boton_detalle = celdas[0].find_element(By.CSS_SELECTOR, ".toggle-modal")
                            driver.execute_script("arguments[0].click();", boton_detalle)
                        except Exception as e_click:
                            from selenium.common.exceptions import ElementClickInterceptedException
                            if isinstance(e_click, ElementClickInterceptedException) or 'element click intercepted' in str(e_click):
                                log_error(task_id, total_workers, f"ElementClickInterceptedException al hacer click en la lupa. Reintentando página completa...")
                                error_reintentar_pagina = True
                                break
                            else:
                                log_error(task_id, total_workers, f"Error al hacer click en la lupa: {e_click}")
                                continue
                        
                        # Esperar modal y verificar si la causa está reservada
                        try:
                            modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleCivil")))
                            
                            # Verificar si la causa está reservada
                            if "causa se encuentra reservada" not in modal.text:
                                # Click en tab de litigantes si existe
                                try:
                                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#litigantesCiv"]'))).click()
                                except Exception:
                                    pass  # Puede estar ya activo
                                
                                # Extraer tabla de litigantes
                                try:
                                    tabla_litigantes = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#litigantesCiv table")))
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
                                            "OBSERVACIONES": observaciones
                                        })
                                except Exception as e_litigantes:
                                    log_error(task_id, total_workers, f"Error extrayendo tabla de litigantes: {e_litigantes}")
                            else:
                                log_debug(task_id, total_workers, "Causa reservada detectada - saltando extracción de litigantes", DEBUG_MODE)
                        except Exception as e_modal:
                            log_error(task_id, total_workers, f"Error extrayendo litigantes: {e_modal}")
                        finally:
                            # Cerrar modal
                            try:
                                driver.find_element(By.CSS_SELECTOR, "#modalDetalleCivil .close").click()
                                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleCivil")))
                            except Exception:
                                pass
                    
                    except Exception as e_row:
                        from selenium.common.exceptions import ElementClickInterceptedException
                        error_message = str(e_row).split('\n')[0]
                        if isinstance(e_row, ElementClickInterceptedException) or 'element click intercepted' in error_message:
                            log_error(task_id, total_workers, f"ElementClickInterceptedException detectado. Reintentando página completa...")
                            error_reintentar_pagina = True
                            break
                        log_error(task_id, total_workers, f"Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}")
                        continue
                        
            except StaleElementReferenceException:
                log_error(task_id, total_workers, "Error de referencia estancada. Reintentando la página.")
                continue

            # Manejo de reintentos después del bucle de filas
            if error_reintentar_pagina:
                reintentos_pagina += 1
                if reintentos_pagina > MAX_REINTENTOS_PAGINA:
                    log_error(task_id, total_workers, f"Se superó el máximo de reintentos ({MAX_REINTENTOS_PAGINA}) para la página {pagina_actual}. Cerrando worker y notificando al main para reintentar desde el checkpoint...")
                    if driver:
                        driver.quit()
                    return f"RETRY:{task_id}:page_{pagina_actual}"
                else:
                    log_progress(task_id, total_workers, f"Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})...")
                    time.sleep(3)
                    error_reintentar_pagina = False
                continue

            # Guardar datos y checkpoint
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                # 4. Guardar CSV en la ruta centralizada
                nombre_archivo_csv = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                header = not os.path.exists(nombre_archivo_csv)
                df.to_csv(nombre_archivo_csv, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
                
                log_progress(task_id, total_workers, f"Página {pagina_actual}: {len(registros_pagina)} registros guardados")
            else:
                log_debug(task_id, total_workers, f"Página {pagina_actual}: Sin registros", DEBUG_MODE)
            
            # Usar checkpoint centralizado
            checkpoint_file = os.path.join(ruta_salida, f"checkpoint_{os.path.basename(os.path.dirname(__file__))}.json")
            with lock:
                try:
                    with open(checkpoint_file, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}

                checkpoint_data[task_id] = {
                    "status": "in_progress",
                    "last_page": pagina_actual
                }

                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
                
                log_debug(task_id, total_workers, f"Checkpoint guardado en página {pagina_actual}", DEBUG_MODE)

            # === PAGINACIÓN UNIFICADA USANDO UTILS ===
            if not navigate_to_next_page(driver, task_id, total_workers, DEBUG_MODE, log_debug, log_error):
                log_progress(task_id, total_workers, "Fin de la paginación detectado.")
                break
            
            # Actualizar página actual
            pagina_actual = get_current_page_number(driver)
            log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")
            continue

        # --- Finalización ---
        if not stop_event.is_set():
            checkpoint_file = os.path.join(ruta_salida, f"checkpoint_{os.path.basename(os.path.dirname(__file__))}.json")
            with lock:
                try:
                    with open(checkpoint_file, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                
                if task_id in checkpoint_data:
                    checkpoint_data[task_id]['status'] = 'completed'
                else:
                    checkpoint_data[task_id] = {'status': 'completed'}
                
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)

            log_worker_status(task_id, total_workers, "FINALIZADO", "tarea completada")
            log_progress(task_id, total_workers, "Tarea completada y marcada en checkpoint")
            return f"COMPLETED:{task_id}"
        else:
            log_worker_status(task_id, total_workers, "DETENIDO", "evento de parada")
            return f"STOPPED:{task_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        log_worker_status(task_id, total_workers, "ERROR", f"fallo general: {str(e)[:50]}")
        log_error(task_id, total_workers, f"Error grave en worker: {type(e).__name__} - {error_message}")
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()
        log_worker_status(task_id, total_workers, "FINALIZADO", "")