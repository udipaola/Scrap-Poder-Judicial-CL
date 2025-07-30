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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from utils_penal import forzar_cierre_navegadores, is_ip_blocked_con_reintentos
from shared_utils import update_checkpoint

import tempfile

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

# Función worker_penal removida - la lógica está en scrape_worker

# CHECKPOINT_FILE será extraído de la tarea

def scrape_worker(task_info):
    task, lock, headless_mode, debug_mode, stop_event = task_info
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

    profile_path = None
    driver = None
    try:
        # Crear un perfil único y predecible basado en task_id
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
        log_debug(task_id, "Verificando bloqueo de IP")
        
        if is_ip_blocked_con_reintentos(driver, task_id):
            log_worker_status(task_id, total_workers, "ERROR", "IP bloqueada")
            stop_event.set()
            return f"IP_BLOCKED:{task_id}"
            
        log_worker_status(task_id, total_workers, "CONFIGURANDO", "filtros de búsqueda")

        # Extraer información de la tarea
        ruta_salida = task['ruta_salida']
        fecha_desde_str = task['fecha_desde_str']
        fecha_hasta_str = task['fecha_hasta_str']
        competencia_nombre = task['competencia_nombre']
        competencia_value = task['competencia_value']
        selector_id = task['selector_id']
        
        # Crear directorio de salida si no existe
        os.makedirs(ruta_salida, exist_ok=True)
        CHECKPOINT_FILE = os.path.join(ruta_salida, 'checkpoint_tribunales_penal.json')

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
        log_worker_status(task_id, total_workers, "CONFIGURANDO", "filtros de búsqueda")
        try:
            # Paso 1: Navegar a la sección de búsqueda por fecha
            log_debug(task_id, "Configurando filtros")
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
        
            # Paso 5: Ingresar fechas y buscar
            input_desde = driver.find_element(By.ID, "fecDesde")
            input_hasta = driver.find_element(By.ID, "fecHasta")
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_desde_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_hasta_str}';", input_hasta)
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
            
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

        pagina_actual = task.get('pagina_a_empezar', 1)
        log_progress(task_id, f"Iniciando en página {pagina_actual}")
        log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")

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
                    if not celdas or len(celdas) < 7:
                        continue
                    # Mapeo de columnas para Penal
                    rit = celdas[headers_principales.get('Rit', 1)].text
                    tribunal = celdas[headers_principales.get('Tribunal', 2)].text
                    ruc = celdas[headers_principales.get('Ruc', 3)].text
                    caratulado = celdas[headers_principales.get('Caratulado', 4)].text
                    fecha_ingreso = celdas[headers_principales.get('Fecha Ingreso', 5)].text
                    estado_causa = celdas[headers_principales.get('Estado Causa', 6)].text
                    
                    # Detección rápida de causas reservadas
                    if "reservada" in caratulado.lower() or "reservada" in estado_causa.lower():
                        observaciones = f"RIT: {rit} | RUC: {ruc} | Tribunal: {tribunal} | Caratulado: {caratulado} | Fecha Ingreso: {fecha_ingreso} | Estado Causa: {estado_causa} | CAUSA RESERVADA"
                        registros_pagina.append({
                            "NOMBRE": "CAUSA RESERVADA",
                            "CARGO": "RESERVADA",
                            "INSTITUCION": tribunal,
                            "OBSERVACIONES": observaciones
                        })
                        continue
                    
                    observaciones = f"RIT: {rit} | RUC: {ruc} | Tribunal: {tribunal} | Caratulado: {caratulado} | Fecha Ingreso: {fecha_ingreso} | Estado Causa: {estado_causa}"
                    # Click en la lupa (detalle)
                    try:
                        boton_detalle = celdas[0].find_element(By.CSS_SELECTOR, ".toggle-modal")
                        from selenium.webdriver import ActionChains
                        ActionChains(driver).move_to_element(boton_detalle).click().perform()
                        log_debug(task_id, f"Click en lupa - RIT: {rit}")
                        
                        # Detección rápida de modales con timeout reducido
                        modal_selector = None
                        fast_wait = WebDriverWait(driver, 3)  # Timeout reducido para detección rápida
                        try:
                            fast_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetallePenal")))
                            modal_selector = "#modalDetallePenal"
                        except TimeoutException:
                            try:
                                fast_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetallePenalUnificado")))
                                modal_selector = "#modalDetallePenalUnificado"
                            except TimeoutException:
                                log_error(task_id, f"No se pudo detectar modal - RIT: {rit}")
                                continue
                    except Exception as e_click:
                        log_error(task_id, f"Error click lupa - RIT: {rit} - {e_click}")
                        continue
                    # Extraer datos adicionales de cabecera y litigantes
                    try:
                        log_debug(task_id, f"Extrayendo datos modal - RIT: {rit}")
                        
                        # Verificación rápida de causa reservada en el modal
                        try:
                            modal_content = driver.find_element(By.CSS_SELECTOR, modal_selector).text.lower()
                            if "reservada" in modal_content and "acta" in modal_content:
                                observaciones_reservada = f"RIT: {rit} | RUC: {ruc} | Tribunal: {tribunal} | Caratulado: {caratulado} | Fecha Ingreso: {fecha_ingreso} | Estado Causa: {estado_causa} | CAUSA RESERVADA (Modal)"
                                registros_pagina.append({
                                    "NOMBRE": "CAUSA RESERVADA",
                                    "CARGO": "RESERVADA",
                                    "INSTITUCION": tribunal,
                                    "OBSERVACIONES": observaciones_reservada
                                })
                                # Cerrar modal y continuar
                                try:
                                    close_button = driver.find_element(By.CSS_SELECTOR, f"{modal_selector} .close")
                                    close_button.click()
                                    fast_wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_selector)))
                                except:
                                    log_debug(task_id, f"No se pudo cerrar modal causa reservada - RIT: {rit}")
                                continue
                        except Exception as e_reservada:
                            pass  # Si hay error verificando causa reservada, continuar con extracción normal
                        
                        datos_adicionales = {}
                        try:
                            tabla_cabecera = driver.find_element(By.CSS_SELECTOR, f"{modal_selector} table.table-titulos")
                            filas_cab = tabla_cabecera.find_elements(By.TAG_NAME, "tr")
                            for fila_cab in filas_cab:
                                celdas_cab = fila_cab.find_elements(By.TAG_NAME, "td")
                                for celda in celdas_cab:
                                    txt = celda.text.strip()
                                    if ':' in txt:
                                        clave, valor = txt.split(':', 1)
                                        datos_adicionales[clave.strip()] = valor.strip()
                        except Exception as e:
                            log_error(task_id, f"Fallo extracción cabecera - RIT: {rit}")
                        
                        # Intentar ambos tipos de pestañas de litigantes
                        tab_selector = None
                        table_selector = None
                        
                        try:
                            # Primero intentar #litigantesPen
                            tab_element = fast_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{modal_selector} a[href='#litigantesPen']")))
                            tab_element.click()
                            time.sleep(0.3)
                            tab_selector = "#litigantesPen"
                            table_selector = "#litigantesPen table"
                        except TimeoutException:
                            try:
                                # Si falla, intentar #litigantes
                                tab_element = fast_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"{modal_selector} a[href='#litigantes']")))
                                tab_element.click()
                                time.sleep(0.3)
                                tab_selector = "#litigantes"
                                table_selector = "#litigantes table"
                            except TimeoutException:
                                log_error(task_id, f"No se encontró pestaña litigantes - RIT: {rit}")
                                continue
                        
                        if tab_selector and table_selector:
                            try:
                                fast_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, table_selector)))
                                
                                # Extraer datos de litigantes
                                litigant_rows = driver.find_elements(By.CSS_SELECTOR, f"{table_selector} tbody tr")
                                
                                for i, row in enumerate(litigant_rows):
                                    try:
                                        cells = row.find_elements(By.TAG_NAME, "td")
                                        
                                        if len(cells) < 2:
                                            continue
                                        
                                        # Mapeo de columnas según el tipo de modal
                                        if modal_selector == "#modalDetallePenalUnificado":
                                            # Para modalDetallePenalUnificado: 3 columnas, situacion en td[0], nombre en td[2]
                                            if len(cells) >= 3:
                                                situacion = cells[0].text.strip()
                                                nombre = cells[2].text.strip()
                                            else:
                                                continue
                                        else:
                                            # Para otros modales: 2 columnas, situacion en td[0], nombre en td[1]
                                            situacion = cells[0].text.strip()
                                            nombre = cells[1].text.strip()
                                        
                                        if situacion and nombre:
                                            obs_extra = f" | Situación: {situacion}" if situacion else ""
                                            registros_pagina.append({
                                                "NOMBRE": nombre,
                                                "CARGO": situacion,
                                                "INSTITUCION": tribunal,
                                                "OBSERVACIONES": observaciones + obs_extra + (" | " + " | ".join([f"{k}: {v}" for k,v in datos_adicionales.items()]) if datos_adicionales else "")
                                            })
                                    except Exception as e_row:
                                        log_debug(task_id, f"Error fila litigante - RIT: {rit}")
                                        continue
                                
                            except Exception as e_litigants:
                                log_error(task_id, f"Fallo extracción litigantes - RIT: {rit}")
                        else:
                            log_error(task_id, f"No acceso pestaña litigantes - RIT: {rit}")
                    except Exception as e_modal:
                        log_error(task_id, f"Error extrayendo litigantes - RIT: {rit}")
                    finally:
                        # Cerrar el modal
                        try:
                            close_button = driver.find_element(By.CSS_SELECTOR, f"{modal_selector} .close")
                            close_button.click()
                            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_selector)))
                        except Exception as e_close:
                            log_debug(task_id, f"Fallo cerrando modal - RIT: {rit} - {e_close}")
            except StaleElementReferenceException:
                log_error(task_id, "Error referencia estancada. Reintentando página.")
                continue

            # Guardar registros en CSV
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                csv_path = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                header = not os.path.exists(csv_path)
                df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
            
            update_checkpoint(CHECKPOINT_FILE, task_id, {
                "status": "in_progress",
                "last_page": pagina_actual
            })
                
            print(f"[{task_id}] Checkpoint guardado en página {pagina_actual}.")

            # Paginación
            try:
                pagina_activa_antes = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()
                
                boton_siguiente = wait.until(EC.element_to_be_clickable((By.ID, "sigId")))
                driver.execute_script("arguments[0].click();", boton_siguiente)
                
                time.sleep(4);

                pagina_activa_despues = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()

                if pagina_activa_antes == pagina_activa_despues:
                    log_worker_status(task_id, total_workers, "COMPLETADO", "todas las páginas procesadas")
                    break
                else:
                    pagina_actual = int(pagina_activa_despues)
                log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")
                    
            except (NoSuchElementException, TimeoutException):
                log_worker_status(task_id, total_workers, "COMPLETADO", "fin de paginación")
                break
            continue

        # --- Finalización ---
        if not stop_event.is_set():
            update_checkpoint(CHECKPOINT_FILE, task_id, {'status': 'completed'})

            print(f"[{task_id}] Tarea completada y marcada en checkpoint.")
            return f"COMPLETED:{task_id}"
        else:
            log_worker_status(task_id, total_workers, "DETENIDO", "evento de parada")
            return f"STOPPED:{task_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        log_worker_status(task_id, total_workers, "ERROR", f"fallo general: {str(e)[:50]}")
        log_error(task_id, f"Error grave en worker: {type(e).__name__} - {error_message}")
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()
        log_worker_status(task_id, total_workers, "FINALIZADO", "")