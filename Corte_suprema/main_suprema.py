# Archivo: main.py

import argparse
import multiprocessing
import json
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_suprema import scrape_worker
from verificacion_worker_suprema import verificacion_worker
from utils_suprema import forzar_cierre_navegadores, quedan_procesos_navegador

# Configuración centralizada
RUTA_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Resultados_Globales')
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, 'checkpoint_suprema.json')
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

# Asegurar que el directorio de salida existe
os.makedirs(RUTA_SALIDA, exist_ok=True)

def generar_tareas(start_date_str, end_date_str, module_name='Corte_suprema'):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []
    
    # Para módulos Corte, usar rangos diarios
    while current_date <= end_date:
        fecha_desde_str = current_date.strftime('%Y-%m-%d')
        fecha_hasta_str = current_date.strftime('%Y-%m-%d')
        fecha_formato_web = current_date.strftime('%d/%m/%Y')
        
        tareas.append({
            'id': fecha_desde_str,
            'fecha': fecha_formato_web,
            'fecha_desde_str': fecha_desde_str,
            'fecha_hasta_str': fecha_hasta_str,
            'ruta_salida': RUTA_SALIDA
        })
        current_date += timedelta(days=1)
    return tareas

def rotar_y_verificar_ip(headless_mode):
    print("\n" + "="*50)
    print("INICIANDO PROCESO DE ROTACIÓN Y VERIFICACIÓN DE IP")
    print("="*50)
    
    while True:
        time.sleep(5)
        
        # Se asegura de cerrar todos los navegadores antes de rotar la IP
        print("[CIERRE FORZADO] Cerrando todos los navegadores...")
        forzar_cierre_navegadores()
        time.sleep(5)
        pais_elegido = random.choice(PAISES_NORDVPN)
        print(f"[IP ROTATION] Conectando a: {pais_elegido}")
        os.system(f'cd "{NORDVPN_PATH}" && nordvpn -c -g "{pais_elegido}"')
        
        print("[IP ROTATION] Esperando 40s para estabilizar conexión...")
        time.sleep(4)

        print("[IP VERIFICATION] Lanzando worker de prueba...")
        with multiprocessing.Pool(processes=1) as verification_pool:
            verification_task = [(headless_mode,)]
            resultado_verificacion = verification_pool.map(verificacion_worker, verification_task)[0]

        if resultado_verificacion:
            print("[IP VERIFICATION] ¡ÉXITO! La nueva IP es funcional.")
            print("="*50 + "\n")
            return True
        else:
            print("[IP VERIFICATION] ¡FALLO! La IP no funciona. Reintentando...")
            time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Orquestador de scraping judicial.")
    parser.add_argument('--modo', choices=['diario', 'historico'], default='historico')
    parser.add_argument('--desde', default="2024-01-01")
    parser.add_argument('--hasta', default="2024-01-31")
    parser.add_argument('--procesos', type=int, default=4, help="Número MÁXIMO de procesos concurrentes.")
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--tanda_size', type=int, default=2, help="Cuántos procesos iniciar a la vez.")
    parser.add_argument('--delay_tanda', type=int, default=15, help="Segundos de espera entre el inicio de cada tanda.")
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
            print("¡Proceso completado! No hay más tareas pendientes.")
            break

        # Reiniciamos el evento de parada para la nueva ronda
        stop_event.clear()

        print(f"Se lanzarán hasta {args.procesos} workers. El inicio se hará en tandas de {args.tanda_size} cada {args.delay_tanda}s.")

        with multiprocessing.Pool(processes=args.procesos) as pool:
            tasks_para_pool = [(task, lock, args.headless, stop_event) for task in tareas_pendientes]
            results_async = []
            
            print(f"Encolando {len(tasks_para_pool)} workers...")
            for i, task_con_lock in enumerate(tasks_para_pool):
                if stop_event.is_set():
                    print("Se ha activado la señal de parada. No se encolarán más workers.")
                    break
                # Encolamos una tarea para ser ejecutada
                res = pool.apply_async(scrape_worker, args=(task_con_lock,))
                results_async.append(res)
                print(f"  -> Worker {i+1}/{len(tasks_para_pool)} para la fecha {task_con_lock[0]['id']} encolado.")
                
                # Si hemos alcanzado el tamaño de la tanda, esperamos
                if (i + 1) % args.tanda_size == 0 and i < len(tasks_para_pool) - 1:
                    print(f"--- Tanda de {args.tanda_size} workers encolada. Esperando {args.delay_tanda}s... ---")
                    time.sleep(args.delay_tanda)

            print("\nTodos los workers han sido encolados. Esperando a que terminen...")
            
            ip_bloqueada_detectada = False
            retry_tasks = []
            for idx, res in enumerate(results_async):
                try:
                    resultado = res.get(timeout=30) # Aumentamos timeout por si acaso
                    print(f"Resultado de un worker: {resultado}")

                    # Detectamos 'RETRY' para reencolar la tarea
                    if isinstance(resultado, str) and resultado.startswith('RETRY:'):
                        # Extraer el id de la tarea
                        parts = resultado.split(':')
                        if len(parts) >= 2:
                            retry_id = parts[1]
                            print(f"[MAIN] Tarea {retry_id} marcada para reintento (RETRY). Se reencolará en la próxima tanda.")
                            # Buscar el task original y agregarlo a retry_tasks
                            for t in tareas_pendientes:
                                if t['id'] == retry_id:
                                    retry_tasks.append(t)
                                    break
                        continue

                    # Ahora detectamos 'IP_BLOCKED' o 'ERROR' como fallos críticos
                    if isinstance(resultado, str) and (resultado.startswith('IP_BLOCKED') or resultado.startswith('ERROR')):
                        ip_bloqueada_detectada = True
                        print(f"¡SEÑAL DE FALLO CRÍTICO ({resultado}) RECIBIDA! Activando evento de parada...")
                        stop_event.set()
                        pool.terminate() # Terminamos el pool inmediatamente
                        break # Salimos del bucle de resultados

                except multiprocessing.TimeoutError:
                    print("Timeout esperando resultado de un worker. Probablemente ya fue terminado por el stop_event.")
                    continue
                except Exception as e:
                    print(f"Error crítico obteniendo resultado de un worker: {e}")
                    ip_bloqueada_detectada = True
                    stop_event.set()
                    pool.terminate()
                    break

            # Esperamos a que todos los procesos del pool terminen limpiamente
            pool.join()

            # Si hay tareas a reintentar, las agregamos al principio de la lista para la próxima ronda
            if retry_tasks:
                print(f"[MAIN] {len(retry_tasks)} tareas serán reintentadas en la próxima tanda.")
                # Insertar al principio para que se prioricen
                tasks = retry_tasks + [t for t in tasks if t not in retry_tasks]

            if ip_bloqueada_detectada:
                print("\nLimpieza final: Iniciando proceso de cierre forzado de navegadores...")
                intentos = 0
                while quedan_procesos_navegador() and intentos < 10:
                    print(f"[CIERRE FORZADO - Intento {intentos + 1}] Aún quedan procesos activos. Reintentando cierre...")
                    forzar_cierre_navegadores()
                    time.sleep(3) # Damos tiempo extra para que los procesos terminen
                    intentos += 1
                if quedan_procesos_navegador():
                    print("[CIERRE FORZADO] ¡ADVERTENCIA! No se pudieron cerrar todos los procesos de navegador tras varios intentos.")
                else:
                    print("[CIERRE FORZADO] Éxito. Todos los procesos de navegador han sido cerrados.")
                print("\nProceso de rotación de IP iniciado.")
                rotar_y_verificar_ip(args.headless)
                print("\nIP rotada. Reiniciando el ciclo de procesamiento...")
                continue
            else:
                print("\nTodas las tareas se completaron sin detectar bloqueos.")

if __name__ == "__main__":
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
            print("\n¡Todas las fechas solicitadas han sido procesadas! Cerrando el ciclo automático.")
            break
        else:
            print("\nReiniciando ciclo para continuar con las fechas pendientes...")