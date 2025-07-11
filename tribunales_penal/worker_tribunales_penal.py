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
from utils_tribunales_penal import forzar_cierre_navegadores, is_ip_blocked_con_reintentos

# CHECKPOINT_FILE será extraído de la tarea

import tempfile

def scrape_worker(task_info):
    task, lock, headless_mode, stop_event = task_info
    task_id = task['id']

    # --- Verificación inicial del evento de parada ---
    if stop_event.is_set():
        print(f"[{task_id}] Evento de parada activado. El worker no se iniciará.")
        return f"STOPPED_BY_EVENT:{task_id}"

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
        
        options.add_argument("--window-position=-2000,0")
        if headless_mode:
            options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        wait = WebDriverWait(driver, 25)

        # --- Verificación de IP ---
        if is_ip_blocked_con_reintentos(driver, task_id):
            print(f"[{task_id}] Bloqueo de IP detectado al inicio. Señalando parada.")
            stop_event.set()
            return f"IP_BLOCKED:{task_id}"
            
        print(f"[{task_id}] Acceso verificado. Procediendo con el scraping.")

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
        try:
            # Paso 1: Navegar a la sección de búsqueda por fecha
            print(f"[{task_id}] Asegurando clic en 'Búsqueda por Fecha'...")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            
            # Paso 2: Seleccionar la Competencia principal (ej. Civil)
            print(f"[{task_id}] Seleccionando Competencia '{competencia_nombre}'...")
            time.sleep(1) # Pequeña pausa para asegurar que la UI se estabilice
            select_competencia_element = wait.until(EC.visibility_of_element_located((By.ID, "fecCompetencia")))
            select_competencia = Select(select_competencia_element)
            select_competencia.select_by_value(competencia_value)

            print(f"[{task_id}] Pausa de 2s para esperar la carga de tribunales...")
            time.sleep(2)

            # Paso 3: Espera robusta con LAMBDA a que el menú secundario se pueble vía AJAX
            print(f"[{task_id}] Esperando a que el menú #{selector_id} se pueble...")
            wait.until(
                lambda d: len(Select(d.find_element(By.ID, selector_id)).options) > 1
            )

            # Paso 4: Seleccionar el ítem específico (Corte o Tribunal)
            print(f"[{task_id}] Seleccionando '{item_nombre}'...")
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
            
            print(f"[{task_id}] Pausa de 3s para esperar la carga de resultados...")
            time.sleep(3);
            
        except Exception as e:
            print(f"[{task_id}] Error en la configuración de filtros: {e}")
            # Capturar screenshot de error
            try:
                screenshot_path = os.path.join(ruta_salida, f"error_filtros_{task_id}.png")
                driver.save_screenshot(screenshot_path)
                print(f"[{task_id}] Screenshot de error guardado en: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"[{task_id}] Error al guardar screenshot: {screenshot_error}")
            return f"ERROR_FILTROS:{task_id}"

        # --- FIN: LÓGICA DE SELECCIÓN DE FILTROS UNIFICADA ---

        pagina_actual = task.get('pagina_a_empezar', 1)
        print(f"[{task_id}] Iniciando en página {pagina_actual}.")

        while not stop_event.is_set():
            registros_pagina = []
            
            # TAREA 3.1: Añadir esta verificación para una salida rápida si no hay resultados.
            try:
                no_results_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'No se han encontrado resultados')]")
                if no_results_msg:
                    print(f"[{task_id}] No se encontraron resultados. Finalizando tarea.")
                    break
            except NoSuchElementException:
                # Es el comportamiento esperado si hay resultados, así que continuamos.
                pass

            # Espera a que la tabla de resultados se cargue
            try:
                wait.until(EC.presence_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                print(f"[{task_id}] Timeout: La tabla de resultados no apareció. Puede que no haya datos.")
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
                    observaciones = f"RIT: {rit} | RUC: {ruc} | Tribunal: {tribunal} | Caratulado: {caratulado} | Fecha Ingreso: {fecha_ingreso} | Estado Causa: {estado_causa}"
                    # Click en la lupa (detalle)
                    try:
                        boton_detalle = celdas[0].find_element(By.CSS_SELECTOR, ".toggle-modal")
                        from selenium.webdriver import ActionChains
                        ActionChains(driver).move_to_element(boton_detalle).click().perform()
                        print(f"[{task_id}] Click real en lupa ejecutado, esperando modal penal visible...")
                        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetallePenal")))
                    except Exception as e_click:
                        print(f"[{task_id}] Error al hacer click en la lupa o esperar modal: {e_click}")
                        continue
                    # Extraer datos adicionales de cabecera y litigantes
                    try:
                        print(f"[{task_id}] Modal visible, extrayendo cabecera...")
                        datos_adicionales = {}
                        try:
                            tabla_cabecera = driver.find_element(By.CSS_SELECTOR, "#modalDetallePenal table.table-titulos")
                            filas_cab = tabla_cabecera.find_elements(By.TAG_NAME, "tr")
                            for fila_cab in filas_cab:
                                celdas_cab = fila_cab.find_elements(By.TAG_NAME, "td")
                                for celda in celdas_cab:
                                    txt = celda.text.strip()
                                    if ':' in txt:
                                        clave, valor = txt.split(':', 1)
                                        datos_adicionales[clave.strip()] = valor.strip()
                        except Exception as e:
                            print(f"[{task_id}] Error extrayendo cabecera: {e}")
                        print(f"[{task_id}] Previo al click en litigantes")
                        try:
                            print(f"[{task_id}] Intentando click en pestaña litigantes...")
                            tab_litigantes = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#litigantesPen"]')))
                            tab_litigantes.click()
                            print(f"[{task_id}] Click en pestaña litigantes OK")
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"[{task_id}] Error al hacer click en la pestaña Litigantes: {e}")
                        print(f"[{task_id}] Intentando extraer tabla de litigantes")
                        try:
                            tabla_litigantes = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#litigantesPen table")))
                            filas_lit = tabla_litigantes.find_elements(By.XPATH, ".//tbody/tr")
                            for fila_lit in filas_lit:
                                celdas_lit = fila_lit.find_elements(By.TAG_NAME, "td")
                                if len(celdas_lit) < 3:
                                    continue
                                # Mapeo correcto: situacion (td[0]), nombre (td[1])
                                situacion = celdas_lit[0].text.strip()
                                nombre = celdas_lit[1].text.strip()
                                obs_extra = f" | Situación: {situacion}" if situacion else ""
                                registros_pagina.append({
                                    "NOMBRE": nombre,
                                    "CARGO": situacion,
                                    "INSTITUCION": tribunal,
                                    "OBSERVACIONES": observaciones + obs_extra + (" | " + " | ".join([f"{k}: {v}" for k,v in datos_adicionales.items()]) if datos_adicionales else "")
                                })
                            print(f"[{task_id}] Extracción de litigantes OK")
                        except Exception as e:
                            print(f"[{task_id}] Error extrayendo tabla de litigantes: {e}")
                    except Exception as e_modal:
                        import traceback
                        print(f"[{task_id}] Error extrayendo litigantes: {e_modal}")
                        traceback.print_exc()
                    finally:
                        # Cerrar modal
                        try:
                            driver.find_element(By.CSS_SELECTOR, "#modalDetallePenal .close").click()
                            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#modalDetallePenal")))
                        except Exception:
                            pass
            except StaleElementReferenceException:
                print(f"[{task_id}] Error de referencia estancada. Reintentando la página.")
                continue

            # Guardar datos y checkpoint
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                csv_path = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
                header = not os.path.exists(csv_path)
                df.to_csv(csv_path, mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
            
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
                
                print(f"[{task_id}] Checkpoint guardado en página {pagina_actual}.")

            # Paginación
            try:
                pagina_activa_antes = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()
                
                boton_siguiente = wait.until(EC.element_to_be_clickable((By.ID, "sigId")))
                driver.execute_script("arguments[0].click();", boton_siguiente)
                
                time.sleep(4);

                pagina_activa_despues = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()

                if pagina_activa_antes == pagina_activa_despues:
                    print(f"[{task_id}] Fin de la paginación detectado.")
                    break
                else:
                    print(f"[{task_id}] Paginación exitosa a la página {pagina_activa_despues}.")
                    pagina_actual = int(pagina_activa_despues)
                    
            except (NoSuchElementException, TimeoutException):
                print(f"[{task_id}] No se encontró el botón 'Siguiente'. Fin de la tarea.")
                break
            continue

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

            print(f"[{task_id}] Tarea completada y marcada en checkpoint.")
            return f"COMPLETED:{task_id}"
        else:
            print(f"[{task_id}] Tarea detenida por evento de parada.")
            return f"STOPPED:{task_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        print(f"Error grave en worker {task_id}: {type(e).__name__} - {error_message}")
        stop_event.set()
        return f"ERROR:{task_id}"
    finally:
        if driver:
            driver.quit()