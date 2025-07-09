# Archivo: worker_suprema.py (CORREGIDO)

import time
import pandas as pd
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from utils_suprema import forzar_cierre_navegadores, is_ip_blocked_con_reintentos

CHECKPOINT_FILE = 'checkpoint.json'

def scrape_worker(task):
    """
    Tarea principal que extrae, transforma y carga los datos.
    """
    dia_a_procesar, lock, headless_mode, stop_event = task
    dia_id = dia_a_procesar['id']

    if stop_event.is_set():
        print(f"[{dia_id}] Evento de parada activado. El worker no se iniciará.")
        return f"STOPPED_BY_EVENT:{dia_id}"

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    options.add_argument("--window-position=-2000,0")
    if headless_mode:
        options.add_argument("--headless")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        wait = WebDriverWait(driver, 25) # Aumentamos un poco el wait general

        if is_ip_blocked_con_reintentos(driver, dia_id):
            print(f"[{dia_id}] Bloqueo de IP detectado al inicio. Señalando parada.")
            stop_event.set()
            return f"IP_BLOCKED:{dia_id}"

        print(f"[{dia_id}] Acceso verificado. Procediendo con el scraping.")

        fecha_str = dia_a_procesar['fecha']
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="#BusFecha"]'))).click()
            
            input_desde = wait.until(EC.presence_of_element_located((By.ID, "fecDesde")))
            input_hasta = wait.until(EC.presence_of_element_located((By.ID, "fecHasta")))
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_str}';", input_hasta)
            time.sleep(1)
            
            wait.until(EC.element_to_be_clickable((By.ID, "btnConConsultaFec"))).click()
        except Exception as e:
            print(f"Error grave en worker {dia_id} durante la configuración de filtros: {e}")
            driver.save_screenshot(f"error_screenshot_{dia_id}.png")
            stop_event.set()
            return f"ERROR:{dia_id}"
        
        pagina_a_empezar = dia_a_procesar.get('pagina_a_empezar', 1)
        pagina_actual = 1

        # ==== INICIO DE LA LÓGICA ROBUSTA DE PAGINACIÓN ====
        MAX_REINTENTOS_PAGINA = 3
        reintentos_pagina = 0
        while not stop_event.is_set():
            # Salto real de página si corresponde
            if pagina_actual < pagina_a_empezar:
                print(f"[{dia_id}] Saltando a la página {pagina_a_empezar}...")
                try:
                    while pagina_actual < pagina_a_empezar:
                        # Esperar a que el paginador esté visible
                        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "li.page-item.active > span.page-link")))
                        # Hacer scroll al paginador
                        paginador_elem = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", paginador_elem)
                        pagina_activa_antes = paginador_elem.text.strip()
                        boton_siguiente = wait.until(EC.element_to_be_clickable((By.ID, "sigId")))
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_siguiente)
                        driver.execute_script("arguments[0].click();", boton_siguiente)
                        time.sleep(2)  # Espera entre saltos
                        # Esperar a que el paginador esté visible de nuevo
                        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "li.page-item.active > span.page-link")))
                        paginador_elem = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link")
                        pagina_activa_despues = paginador_elem.text.strip()
                        print(f"[{dia_id}] Avanzando: {pagina_activa_antes} -> {pagina_activa_despues}")
                        if pagina_activa_antes == pagina_activa_despues:
                            print(f"[{dia_id}] No se pudo avanzar más allá de la página {pagina_actual}. Fin de la paginación.")
                            break
                        pagina_actual = int(pagina_activa_despues)
                except Exception as e:
                    print(f"[{dia_id}] Error al saltar páginas: {e}")
                    break
                if pagina_actual < pagina_a_empezar:
                    print(f"[{dia_id}] No se pudo alcanzar la página solicitada. Fin de la tarea.")
                    break

            print(f"--- [{dia_id}] Procesando Página {pagina_actual} ---")
            try:
                wait.until(EC.visibility_of_element_located((By.ID, "dtaTableDetalleFecha")))
            except TimeoutException:
                print(f"[{dia_id}] La tabla de resultados no apareció. Verificando bloqueo.")
                if is_ip_blocked_con_reintentos(driver, dia_id):
                    stop_event.set()
                    return f"IP_BLOCKED:{dia_id}"
                else:
                    print(f"[{dia_id}] No parece ser un bloqueo. Se asume que no hay más resultados.")
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
                            print(f"[{dia_id}] ElementClickInterceptedException al hacer click en la lupa. Reintentando página completa...")
                            error_reintentar_pagina = True
                            break
                        else:
                            raise
                    
                    # (Tu lógica de modal aquí... es correcta)
                    try:
                        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#modalDetalleSuprema")))
                    except TimeoutException:
                        print(f"[{dia_id}] Timeout esperando modal. Reintentando página completa...")
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
                    print(f"[{dia_id}] Stale element en la página {pagina_actual}. Se reintentará la página completa.")
                    error_reintentar_pagina = True
                    break
                except Exception as e_row:
                    from selenium.common.exceptions import ElementClickInterceptedException
                    error_message = str(e_row).split('\n')[0]
                    if isinstance(e_row, ElementClickInterceptedException) or 'element click intercepted' in error_message:
                        print(f"[{dia_id}] ElementClickInterceptedException detectado. Reintentando página completa...")
                        error_reintentar_pagina = True
                        break
                    print(f"[{dia_id}] Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}")
                    continue
            if error_reintentar_pagina:
                reintentos_pagina += 1
                if reintentos_pagina > MAX_REINTENTOS_PAGINA:
                    print(f"[{dia_id}] Se superó el máximo de reintentos ({MAX_REINTENTOS_PAGINA}) para la página {pagina_actual}. Saltando a la siguiente página.")
                    pagina_actual += 1
                    reintentos_pagina = 0
                else:
                    print(f"[{dia_id}] Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})...")
                    time.sleep(3)
                continue
            
            # Este bloque 'else' solo se ejecuta si el 'for' termina SIN un 'break'
            if registros_pagina:
                df = pd.DataFrame(registros_pagina)
                header = not os.path.exists(f"resultados_{dia_id}.csv")
                df.to_csv(f"resultados_{dia_id}.csv", mode='a', sep=';', index=False, encoding='utf-8-sig', header=header)
            
            with lock:
                # (Tu lógica de checkpoint aquí... es correcta)
                try:
                    with open(CHECKPOINT_FILE, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                checkpoint_data[dia_id] = {"status": "in_progress", "last_page": pagina_actual}
                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
                print(f"[{dia_id}] Checkpoint guardado en página {pagina_actual}.")

            try:
                # 1. Obtener número de página activa ANTES del clic
                pagina_activa_antes = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()
                print(f"[{dia_id}] Página activa actual: {pagina_activa_antes}.")
                # 2. Intentar hacer clic en 'Siguiente'
                boton_siguiente = wait.until(EC.element_to_be_clickable((By.ID, "sigId")))
                driver.execute_script("arguments[0].click();", boton_siguiente)
                # 3. Esperar a que la página reaccione
                time.sleep(4) # Pausa crucial para que el DOM se actualice
                # 4. Obtener número de página activa DESPUÉS del clic
                pagina_activa_despues = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link").text.strip()
                print(f"[{dia_id}] Página activa después de paginar: {pagina_activa_despues}.")
                # 5. Comparar para detectar bucle infinito
                if pagina_activa_antes == pagina_activa_despues:
                    print(f"[{dia_id}] El número de página no cambió ({pagina_activa_despues}). Fin de la paginación detectado.")
                    break # Salir del bucle while
                else:
                    print(f"[{dia_id}] Paginación exitosa a la página {pagina_activa_despues}.")
                    pagina_actual = int(pagina_activa_despues)
            except (NoSuchElementException, TimeoutException):
                print(f"[{dia_id}] No se encontró el botón 'Siguiente' o el paginador. Fin de la tarea.")
                break # Salir del bucle while
            continue
        # ==== FIN DE LA LÓGICA ROBUSTA ====

        if not stop_event.is_set():
            with lock:
                # (Tu lógica de marcar como completado aquí... es correcta)
                try:
                    with open(CHECKPOINT_FILE, 'r+') as f:
                        checkpoint_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    checkpoint_data = {}
                if dia_id in checkpoint_data:
                    checkpoint_data[dia_id]['status'] = 'completed'
                else:
                    checkpoint_data[dia_id] = {'status': 'completed'}
                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint_data, f, indent=4)
            print(f"[{dia_id}] Tarea completada.")
            return f"COMPLETED:{dia_id}"
        else:
            print(f"[{dia_id}] Tarea detenida por evento de parada.")
            return f"STOPPED:{dia_id}"

    except Exception as e:
        error_message = str(e).split('\n')[0]
        print(f"Error MUY grave en worker {dia_id}: {type(e).__name__} - {error_message}")
        stop_event.set() # Señalamos a todos que paren
        return f"ERROR:{dia_id}" # Retornamos un error claro
    finally:
        if driver:
            driver.quit()