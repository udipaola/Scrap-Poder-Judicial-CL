# Archivo: main.py

import argparse
import multiprocessing
import json
import os
import time
import shutil # Added
import glob # Added
import tempfile # Added
import random
import logging # Added
from logging.handlers import TimedRotatingFileHandler # Added
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker import scrape_worker
from verificacion_worker_apelaciones import verificacion_worker
from utils import forzar_cierre_navegadores, quedan_procesos_navegador

CHECKPOINT_FILE = 'checkpoint.json'
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

CORTES_APELACIONES = [
    {'id': '10', 'nombre': 'C.A. de Arica'},
    {'id': '11', 'nombre': 'C.A. de Iquique'},
    {'id': '15', 'nombre': 'C.A. de Antofagasta'},
    {'id': '20', 'nombre': 'C.A. de Copiapó'},
    {'id': '25', 'nombre': 'C.A. de La Serena'},
    {'id': '30', 'nombre': 'C.A. de Valparaíso'},
    {'id': '35', 'nombre': 'C.A. de Rancagua'},
    {'id': '40', 'nombre': 'C.A. de Talca'},
    {'id': '45', 'nombre': 'C.A. de Chillan'},
    {'id': '46', 'nombre': 'C.A. de Concepción'},
    {'id': '50', 'nombre': 'C.A. de Temuco'},
    {'id': '55', 'nombre': 'C.A. de Valdivia'},
    {'id': '56', 'nombre': 'C.A. de Puerto Montt'},
    {'id': '60', 'nombre': 'C.A. de Coyhaique'},
    {'id': '61', 'nombre': 'C.A. de Punta Arenas'},
    {'id': '90', 'nombre': 'C.A. de Santiago'},
    {'id': '91', 'nombre': 'C.A. de San Miguel'}
]

# --- Logging Setup Function ---
def setup_logging(directorio_actual):
    """Configura el logging para rotar diariamente y mantener 7 días de historial."""
    log_filename = os.path.join(directorio_actual, 'scraping.log')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evitar añadir manejadores duplicados
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - [%(processName)s-%(process)d] - [%(levelname)s] - %(message)s')

    # Manejador para la consola
    consola_handler = logging.StreamHandler()
    consola_handler.setFormatter(formatter)

    # Manejador para el archivo con rotación diaria
    archivo_handler = TimedRotatingFileHandler(
        filename=log_filename,
        when="D",
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    archivo_handler.setFormatter(formatter)

    logger.addHandler(consola_handler)
    logger.addHandler(archivo_handler)
# --- End of Logging Setup ---

# --- Function to clean old profiles ---
def limpiar_perfiles_antiguos():
    """Busca y elimina todos los directorios de perfiles temporales de ejecuciones anteriores."""
    logging.info("--- Iniciando limpieza de perfiles de navegador antiguos... ---")
    temp_dir = tempfile.gettempdir()

    patrones_a_buscar = [
        os.path.join(temp_dir, "pjud_profile_*"),
        os.path.join(temp_dir, "pjud_verification_profile_*")
    ]
    perfiles_a_borrar = []
    for patron in patrones_a_buscar:
        perfiles_a_borrar.extend(glob.glob(patron))

    if not perfiles_a_borrar:
        logging.info("--- No se encontraron perfiles antiguos para limpiar. ---")
        return

    borrados = 0
    for perfil in perfiles_a_borrar:
        try:
            shutil.rmtree(perfil)
            borrados += 1
        except Exception as e:
            logging.warning(f"No se pudo borrar el perfil '{perfil}'. Causa: {e}")

    logging.info(f"--- Limpieza finalizada. Se eliminaron {borrados}/{len(perfiles_a_borrar)} perfiles antiguos. ---")
# --- End of function ---

def generar_tareas(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []
    while current_date <= end_date:
        fecha_id_base = current_date.strftime('%Y-%m-%d')
        fecha_formato_web = current_date.strftime('%d/%m/%Y')
        for corte in CORTES_APELACIONES:
            # El ID de la tarea ahora es único para la combinación fecha-corte
            tarea_id = f"{fecha_id_base}_{corte['id']}"
            tareas.append({
                'id': tarea_id,
                'fecha': fecha_formato_web,
                'corte_id': corte['id'],
                'corte_nombre': corte['nombre']
            })
        current_date += timedelta(days=1)
    return tareas

def rotar_y_verificar_ip(headless_mode):
    logging.info("\n" + "="*50)
    logging.info("INICIANDO PROCESO DE ROTACIÓN Y VERIFICACIÓN DE IP")
    logging.info("="*50)
    
    while True:
        logging.info("[IP ROTATION] Desconectando de NordVPN...")
        os.system(f'cd "{NORDVPN_PATH}" && nordvpn -d')
        time.sleep(5)
        
        #Se asegura de cerrar todos los navegadores antes de rotar la IP
        logging.info("[CIERRE FORZADO] Cerrando todos los navegadores...")
        forzar_cierre_navegadores() 
        
        pais_elegido = random.choice(PAISES_NORDVPN)
        logging.info(f"[IP ROTATION] Conectando a: {pais_elegido}")
        os.system(f'cd "{NORDVPN_PATH}" && nordvpn -c -g "{pais_elegido}"')
        
        logging.info("[IP ROTATION] Esperando 40s para estabilizar conexión...")
        time.sleep(40)

        logging.info("[IP VERIFICATION] Lanzando worker de prueba...")
        with multiprocessing.Pool(processes=1) as verification_pool:
            verification_task = [(headless_mode,)]
            resultado_verificacion = verification_pool.map(verificacion_worker, verification_task)[0]

        if resultado_verificacion:
            logging.info("[IP VERIFICATION] ¡ÉXITO! La nueva IP es funcional.")
            logging.info("="*50 + "\n")
            return True
        else:
            logging.warning("[IP VERIFICATION] ¡FALLO! La IP no funciona. Reintentando...")
            time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Orquestador de scraping judicial.")
    parser.add_argument('--modo', choices=['diario', 'historico'], default='historico')
    parser.add_argument('--desde', default="2024-01-01")
    parser.add_argument('--hasta', default="2024-01-31")
    parser.add_argument('--procesos', type=int, default=4, help="Número MÁXIMO de procesos concurrentes.")
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--tanda_size', type=int, default=2, help="Cuántos procesos iniciar a la vez.")
    parser.add_argument('--delay_tanda', type=int, default=90, help="Segundos de espera entre el inicio de cada tanda.")
    args = parser.parse_args()

    tasks = generar_tareas(args.desde, args.hasta) if args.modo == 'historico' else []

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    stop_event = manager.Event()

    while True:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint_data = json.load(f) if os.path.getsize(CHECKPOINT_FILE) > 0 else {}
        else:
            checkpoint_data = {}
        
        tareas_pendientes = []
        for task in tasks:
            if checkpoint_data.get(task['id'], {}).get('status') != 'completed':
                if checkpoint_data.get(task['id'], {}).get('status') == 'in_progress':
                    task['pagina_a_empezar'] = checkpoint_data[task['id']].get('last_page', 1)
                tareas_pendientes.append(task)

        if not tareas_pendientes:
            logging.info("¡Proceso completado! No hay más tareas pendientes.")
            break

        # Reiniciamos el evento de parada para la nueva ronda
        stop_event.clear()

        logging.info(f"Se lanzarán hasta {args.procesos} workers. El inicio se hará en tandas de {args.tanda_size} cada {args.delay_tanda}s.")

        # 1. Creamos el pool manualmente, fuera de un bloque 'with'
        pool = multiprocessing.Pool(processes=args.procesos)

        try:
            tasks_para_pool = [(task, lock, args.headless, stop_event) for task in tareas_pendientes]
            results_async = []
            
            logging.info(f"Encolando {len(tasks_para_pool)} workers...")
            for i, task_con_lock in enumerate(tasks_para_pool):
                if stop_event.is_set():
                    logging.info("Se ha activado la señal de parada. No se encolarán más workers.")
                    break
                # Encolamos una tarea para ser ejecutada
                res = pool.apply_async(scrape_worker, args=(task_con_lock,))
                results_async.append(res)
                logging.info(f"  -> Worker {i+1}/{len(tasks_para_pool)} para la fecha {task_con_lock[0]['id']} encolado.")
                
                # Si hemos alcanzado el tamaño de la tanda, esperamos
                if (i + 1) % args.tanda_size == 0 and i < len(tasks_para_pool) - 1:
                    logging.info(f"--- Tanda de {args.tanda_size} workers encolada. Esperando {args.delay_tanda}s... ---")
                    time.sleep(args.delay_tanda)

            logging.info("\nTodos los workers han sido encolados. Esperando a que terminen...")
            
            ip_bloqueada_detectada = False
            for res in results_async:
                try:
                    # Usamos un timeout pequeño para no quedar esperando por un worker que ya debería haber parado
                    resultado = res.get(timeout=30) # Aumentamos un poco el timeout
                    logging.info(f"Resultado de un worker: {resultado}")
                    if isinstance(resultado, str) and (resultado.startswith('IP_BLOCKED') or resultado.startswith('ERROR')):
                        logging.error(f"¡SEÑAL DE ERROR DETECTADA ({resultado})! Activando evento de parada...")
                        ip_bloqueada_detectada = True
                        stop_event.set()
                        pool.terminate()
                        break 
                except multiprocessing.TimeoutError:
                    logging.warning("Timeout esperando resultado de un worker. Probablemente ya fue terminado.")
                    continue
                except Exception as e:
                    logging.error(f"Error crítico obteniendo resultado de un worker: {e}")
                    ip_bloqueada_detectada = True
                    stop_event.set()
                    pool.terminate()
                    break

        finally:
            pool.join()
            pool.close()

            if ip_bloqueada_detectada:
                logging.info("\nLimpieza final: Iniciando proceso de cierre forzado de navegadores...")
                # --- INICIO DEL BLOQUE DE CIERRE ROBUSTO ---
                intentos = 0
                while quedan_procesos_navegador() and intentos < 10:
                    logging.info(f"[CIERRE FORZADO - Intento {intentos + 1}] Aún quedan procesos activos. Reintentando cierre...")
                    forzar_cierre_navegadores()
                    time.sleep(3) # Damos tiempo extra para que los procesos terminen
                    intentos += 1

                if quedan_procesos_navegador():
                    logging.warning("[CIERRE FORZADO] ¡ADVERTENCIA! No se pudieron cerrar todos los procesos de navegador tras varios intentos.")
                else:
                    logging.info("[CIERRE FORZADO] Éxito. Todos los procesos de navegador han sido cerrados.")
                # --- FIN DEL BLOQUE DE CIERRE ROBUSTO ---
                
                logging.info("\nProceso de rotación de IP iniciado.")
                rotar_y_verificar_ip(args.headless)
                logging.info("\nIP rotada. Reiniciando el ciclo de procesamiento...")
                continue
            else:
                logging.info("\nTodas las tareas se completaron sin detectar bloqueos.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    setup_logging(script_dir) # Called first

    limpiar_perfiles_antiguos() # Called after logging setup

    logging.info(f"========== INICIO DE EJECUCIÓN DEL MÓDULO {os.path.basename(script_dir)} ==========")

    multiprocessing.freeze_support()
    while True:
        main()
        # Tras finalizar main(), revisamos si quedan tareas pendientes
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint_data = json.load(f) if os.path.getsize(CHECKPOINT_FILE) > 0 else {}
        else:
            checkpoint_data = {}
        # Si no quedan tareas pendientes, salimos del loop
        tareas_pendientes = [tid for tid, tinfo in checkpoint_data.items() if tinfo.get('status') != 'completed']
        if not tareas_pendientes:
            logging.info("\n¡Todas las fechas solicitadas han sido procesadas! Cerrando el ciclo automático.")
            break
        else:
            logging.info("\nReiniciando ciclo para continuar con las fechas pendientes...")
