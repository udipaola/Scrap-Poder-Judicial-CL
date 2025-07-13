# Archivo: utils/pagination_utils.py
# Funciones comunes de paginación para todos los módulos

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_current_page_number(driver):
    """Obtiene el número de página actual del paginador"""
    try:
        pagina_elem = driver.find_element(By.CSS_SELECTOR, "li.page-item.active > span.page-link")
        return int(pagina_elem.text.strip())
    except Exception:
        return 1

def navigate_to_next_page(driver, task_id, total_workers, debug_mode, log_debug, log_error):
    """Navega a la siguiente página y retorna True si exitoso"""
    try:
        # Obtener página actual antes del clic
        pagina_antes = get_current_page_number(driver)
        
        # Buscar y hacer click en "Siguiente"
        boton_siguiente = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sigId"))
        )
        
        # Verificar si el botón está deshabilitado
        if 'disabled' in boton_siguiente.get_attribute('class') or not boton_siguiente.is_enabled():
            log_debug(task_id, total_workers, f"Botón 'Siguiente' deshabilitado. Fin de paginación en página {pagina_antes}", debug_mode)
            return False
            
        # Hacer scroll y click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_siguiente)
        driver.execute_script("arguments[0].click();", boton_siguiente)
        time.sleep(2)
        
        # Verificar que la página cambió
        pagina_despues = get_current_page_number(driver)
        
        if pagina_antes == pagina_despues:
            log_debug(task_id, total_workers, f"El número de página no cambió ({pagina_despues}). Fin de la paginación detectado.", debug_mode)
            return False
            
        log_debug(task_id, total_workers, f"Paginación exitosa: {pagina_antes} → {pagina_despues}", debug_mode)
        return True
        
    except TimeoutException:
        log_debug(task_id, total_workers, "Timeout esperando el botón 'Siguiente'. Fin de la paginación detectado.", debug_mode)
        return False
    except Exception as e:
        log_error(task_id, total_workers, f"Error navegando página: {str(e)}")
        return False

def navigate_to_page(driver, target_page, task_id, total_workers, debug_mode, log_progress, log_error):
    """Navega a una página específica"""
    try:
        current_page = get_current_page_number(driver)
        
        while current_page < target_page:
            if not navigate_to_next_page(driver, task_id, total_workers, debug_mode, lambda *args: None, log_error):
                return False
            current_page = get_current_page_number(driver)
            
        return current_page == target_page
        
    except Exception as e:
        log_error(task_id, total_workers, f"Error navegando a página {target_page}: {str(e)}")
        return False

def apply_checkpoint_pagination(driver, pagina_inicial, task_id, total_workers, debug_mode, log_progress, log_error):
    """Aplica checkpoint navegando a la página inicial especificada"""
    try:
        if pagina_inicial <= 1:
            return True
            
        log_progress(task_id, total_workers, f"Aplicando checkpoint: navegando a página {pagina_inicial}...")
        
        # Usar navigate_to_page para ir a la página específica
        if not navigate_to_page(driver, pagina_inicial, task_id, total_workers, debug_mode, log_progress, log_error):
            return False
            
        # Verificar que estamos en la página correcta
        pagina_actual = get_current_page_number(driver)
        if pagina_actual != pagina_inicial:
            log_error(task_id, total_workers, f"Error: Se esperaba página {pagina_inicial}, pero estamos en página {pagina_actual}")
            return False
            
        log_progress(task_id, total_workers, f"Checkpoint aplicado exitosamente. Iniciando desde página {pagina_actual}")
        return True
        
    except Exception as e:
        log_error(task_id, total_workers, f"Error aplicando checkpoint: {str(e)}")
        return False

def get_pagination_loop_variables(driver, task_id, total_workers, debug_mode, log_debug, log_error):
    """Obtiene las variables necesarias para el loop de paginación"""
    try:
        # Obtener página actual
        pagina_actual = get_current_page_number(driver)
        
        # Obtener página antes del clic (para verificación)
        pagina_activa_antes = get_current_page_number(driver)
        
        return pagina_actual, pagina_activa_antes
        
    except Exception as e:
        log_error(task_id, total_workers, f"Error obteniendo variables de paginación: {str(e)}")
        return 1, 1