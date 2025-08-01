# Archivo: main.py

import argparse
import multiprocessing
import json
import os
import subprocess
import time
import random
import shutil
import glob
import tempfile
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_apelaciones import scrape_worker
from verificacion_worker_apelaciones import verificacion_worker
from utils_apelaciones import forzar_cierre_navegadores, quedan_procesos_navegador

# Configuración centralizada
RUTA_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Resultados_Globales','Resultados_apelaciones')
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, 'checkpoint_apelaciones.json')
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

# Asegurar que el directorio de salida existe
os.makedirs(RUTA_SALIDA, exist_ok=True)

def limpiar_perfiles_antiguos():
    """Busca y elimina todos los directorios de perfiles de Chrome de ejecuciones anteriores."""
    print("--- Iniciando limpieza de perfiles de navegador antiguos... ---")
    temp_dir = tempfile.gettempdir()
    
    # Patrones para encontrar todos los perfiles relevantes
    patrones = [
        os.path.join(temp_dir, "pjud_profile_*"),
        os.path.join(temp_dir, "pjud_verification_profile_*")
    ]
    
    perfiles_a_borrar = []
    for patron in patrones:
        perfiles_a_borrar.extend(glob.glob(patron))

    if not perfiles_a_borrar:
        print("--- No se encontraron perfiles antiguos para limpiar. ---")
        return

    borrados = 0
    for perfil in perfiles_a_borrar:
        try:
            shutil.rmtree(perfil)
            borrados += 1
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo borrar el perfil huérfano '{perfil}'. Causa: {e}")
            
    print(f"--- Limpieza finalizada. Se eliminaron {borrados}/{len(perfiles_a_borrar)} perfiles. ---")

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

def generar_tareas(start_date_str, end_date_str, module_name='Corte_apelaciones'):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []
    
    # Para módulos Corte, usar rangos diarios
    while current_date <= end_date:
        fecha_desde_str = current_date.strftime('%Y-%m-%d')
        fecha_hasta_str = current_date.strftime('%Y-%m-%d')
        fecha_formato_web = current_date.strftime('%d/%m/%Y')
        
        for corte in CORTES_APELACIONES:
            tarea_id = f"{fecha_desde_str}_{corte['id']}"
            tareas.append({
                'id': tarea_id,
                'fecha': fecha_formato_web,
                'fecha_desde_str': fecha_desde_str,
                'fecha_hasta_str': fecha_hasta_str,
                'corte_id': corte['id'],
                'corte_nombre': corte['nombre'],
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
        
        #Se asegura de cerrar todos los navegadores antes de rotar la IP
        print("[CIERRE FORZADO] Cerrando todos los navegadores...")
        forzar_cierre_navegadores()
        time.sleep(5)
        
        pais_elegido = random.choice(PAISES_NORDVPN)
        print(f"[IP ROTATION] Conectando a: {pais_elegido}")
        try:
            # Usamos subprocess.run con timeout para evitar bloqueos
            comando = ['nordvpn', '-c', '-g', pais_elegido]
            print(f"[IP ROTATION] Ejecutando comando: {' '.join(comando)}")
            subprocess.run(comando, check=True, timeout=120, cwd=NORDVPN_PATH, shell=True, capture_output=True, text=True)
            print(f"[IP ROTATION] Comando de conexión a {pais_elegido} completado.")
        except subprocess.TimeoutExpired:
            print(f"[IP ROTATION ERROR] El comando para conectar a {pais_elegido} excedió el tiempo de espera de 120s.")
            continue # Reintentar con otro país
        except subprocess.CalledProcessError as e:
            print(f"[IP ROTATION ERROR] Fallo al conectar a {pais_elegido}. Error: {e.stderr}")
            continue # Reintentar con otro país
        
        print("[IP ROTATION] Esperando 40s para estabilizar conexión...")
        time.sleep(40)

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
            for res in results_async:
                try:
                    # Usamos un timeout pequeño para no quedar esperando por un worker que ya debería haber parado
                    resultado = res.get(timeout=30) # Aumentamos un poco el timeout
                    print(f"Resultado de un worker: {resultado}")
                    if isinstance(resultado, str) and (resultado.startswith('IP_BLOCKED') or resultado.startswith('ERROR')):
                        print(f"¡SEÑAL DE ERROR DETECTADA ({resultado})! Activando evento de parada...")
                        ip_bloqueada_detectada = True
                        stop_event.set()
                        pool.terminate()
                        break 
                except multiprocessing.TimeoutError:
                    print("Timeout esperando resultado de un worker. Probablemente ya fue terminado.")
                    continue
                except Exception as e:
                    print(f"Error crítico obteniendo resultado de un worker: {e}")
                    ip_bloqueada_detectada = True
                    stop_event.set()
                    pool.terminate()
                    break

            pool.close()
            pool.join()

            if ip_bloqueada_detectada:
                print("\nLimpieza final: Iniciando proceso de cierre forzado de navegadores...")
                # --- INICIO DEL BLOQUE DE CIERRE ROBUSTO ---
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
                # --- FIN DEL BLOQUE DE CIERRE ROBUSTO ---
                
                print("\nProceso de rotación de IP iniciado.")
                rotar_y_verificar_ip(args.headless)
                print("\nIP rotada. Reiniciando el ciclo de procesamiento...")
                continue
            else:
                print("\nTodas las tareas se completaron sin detectar bloqueos.")

if __name__ == "__main__":
    # La limpieza debe ser el primer paso, antes de iniciar cualquier proceso
    limpiar_perfiles_antiguos()
    
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
