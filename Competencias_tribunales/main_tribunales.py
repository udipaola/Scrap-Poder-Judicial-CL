# Archivo: main.py

import argparse
import multiprocessing
import json
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_tribunales import scrape_worker
from verificacion_worker_tribunales import verificacion_worker
from utils_tribunales import forzar_cierre_navegadores, quedan_procesos_navegador

CHECKPOINT_FILE = 'checkpoint.json'
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

# TAREA 1.1 y 1.2: Reemplazar la constante CORTES_APELACIONES por este bloque completo.
# Contiene las listas de datos y la nueva configuración maestra.

CORTES_APELACIONES = [
    {'id': '10', 'nombre': 'C.A. de Arica'}, {'id': '11', 'nombre': 'C.A. de Iquique'},
    {'id': '15', 'nombre': 'C.A. de Antofagasta'}, {'id': '20', 'nombre': 'C.A. de Copiapó'},
    {'id': '25', 'nombre': 'C.A. de La Serena'}, {'id': '30', 'nombre': 'C.A. de Valparaíso'},
    {'id': '35', 'nombre': 'C.A. de Rancagua'}, {'id': '40', 'nombre': 'C.A. de Talca'},
    {'id': '45', 'nombre': 'C.A. de Chillan'}, {'id': '46', 'nombre': 'C.A. de Concepción'},
    {'id': '50', 'nombre': 'C.A. de Temuco'}, {'id': '55', 'nombre': 'C.A. de Valdivia'},
    {'id': '56', 'nombre': 'C.A. de Puerto Montt'}, {'id': '60', 'nombre': 'C.A. de Coyhaique'},
    {'id': '61', 'nombre': 'C.A. de Punta Arenas'}, {'id': '90', 'nombre': 'C.A. de Santiago'},
    {'id': '91', 'nombre': 'C.A. de San Miguel'}
]

TRIBUNALES_CIVIL = [
    {'id': '2', 'nombre': '1º Juzgado de Letras de Arica'}, {'id': '1400', 'nombre': '1º Juzgado De Letras de Arica ex 4°'},
    {'id': '3', 'nombre': '2º Juzgado de Letras de Arica'}, {'id': '1401', 'nombre': '2º Juzgado De Letras de Arica ex 4°'},
    {'id': '4', 'nombre': '3º Juzgado de Letras de Arica'}, {'id': '5', 'nombre': '3º Juzgado de Letras de Arica Ex 4º'},
    {'id': '6', 'nombre': 'Juzgado de Letras y Gar. Pozo Almonte'}, {'id': '9', 'nombre': '1º Juzgado de Letras de Iquique'},
    {'id': '10', 'nombre': '2º Juzgado de Letras de Iquique'}, {'id': '11', 'nombre': '3º Juzgado de Letras de Iquique'},
    {'id': '13', 'nombre': 'Juzgado de Letras Tocopilla'}, {'id': '14', 'nombre': 'Juzgado de Letras y Gar.de María Elena'},
    {'id': '16', 'nombre': '1º Juzgado de Letras de Calama'}, {'id': '17', 'nombre': '2º Juzgado de Letras de Calama'},
    {'id': '658', 'nombre': '3º Juzgado de Letras de Calama'}, {'id': '26', 'nombre': 'Juzgado de Letras y Gar. de Taltal'},
    {'id': '1041', 'nombre': '1º Juzgado de Letras Civil de Antofagasta'}, {'id': '1042', 'nombre': '2º Juzgado de Letras Civil de Antofagasta'},
    {'id': '1043', 'nombre': '3º Juzgado de Letras Civil de Antofagasta'}, {'id': '1044', 'nombre': '4 ° Juzgado de Letras Civil de Antofagasta'},
    {'id': '1501', 'nombre': 'Juzgado de Letras y Garantía Mejillones'}, {'id': '27', 'nombre': 'Juzgado de Letras y Gar. de Chañaral'},
    {'id': '29', 'nombre': 'Juzgado de Letras de Diego de Almagro'}, {'id': '31', 'nombre': '1º Juzgado de Letras de Copiapó'},
    {'id': '32', 'nombre': '2º Juzgado de Letras de Copiapó'}, {'id': '33', 'nombre': '3º Juzgado de Letras de Copiapó'},
    {'id': '34', 'nombre': 'Juzgado de Letras y Gar.de Freirina'}, {'id': '926', 'nombre': '4º Juzgado de Letras de Copiapó'},
    {'id': '36', 'nombre': '1º Juzgado de Letras de Vallenar'}, {'id': '37', 'nombre': '2º Juzgado de Letras de Vallenar'},
    {'id': '386', 'nombre': 'Juzgado de Letras y Garantía de Vicuña'}
]

COMPETENCIAS_CONFIG = {
    "Apelaciones": {
        "value": "2",
        "selector_id": "fecCorte",
        "items": CORTES_APELACIONES,
        "item_key_id": "corte_id",
        "item_key_nombre": "corte_nombre"
    },
    "Civil": {
        "value": "3",
        "selector_id": "fecTribunal",
        "items": TRIBUNALES_CIVIL,
        "item_key_id": "tribunal_id",
        "item_key_nombre": "tribunal_nombre"
    }
}

# TAREA 1.3: Reemplazar la función generar_tareas existente por esta versión refactorizada.

def generar_tareas(start_date_str, end_date_str, competencia_target):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []

    competencias_a_procesar = {}
    if competencia_target.lower() == "all":
        competencias_a_procesar = COMPETENCIAS_CONFIG
    elif competencia_target in COMPETENCIAS_CONFIG:
        competencias_a_procesar = {competencia_target: COMPETENCIAS_CONFIG[competencia_target]}
    else:
        print(f"Error: La competencia '{competencia_target}' no es válida. Las opciones son: {list(COMPETENCIAS_CONFIG.keys())}")
        return []

    while current_date <= end_date:
        fecha_id_base = current_date.strftime('%Y-%m-%d')
        fecha_formato_web = current_date.strftime('%d/%m/%Y')

        for comp_nombre, comp_data in competencias_a_procesar.items():
            for item in comp_data["items"]:
                tarea_id = f"{comp_nombre.lower()}_{fecha_id_base}_{item['id']}"
                tarea = {
                    'id': tarea_id,
                    'fecha': fecha_formato_web,
                    'competencia_nombre': comp_nombre,
                    'competencia_value': comp_data['value'],
                    'selector_id': comp_data['selector_id'],
                    comp_data["item_key_id"]: item['id'],
                    comp_data["item_key_nombre"]: item['nombre']
                }
                tareas.append(tarea)
        current_date += timedelta(days=1)
    return tareas

def rotar_y_verificar_ip(headless_mode):
    print("\n" + "="*50)
    print("INICIANDO PROCESO DE ROTACIÓN Y VERIFICACIÓN DE IP")
    print("="*50)
    
    while True:
        #Se asegura de cerrar todos los navegadores antes de rotar la IP
        print("[CIERRE FORZADO] Cerrando todos los navegadores...")
        forzar_cierre_navegadores() 
        
        pais_elegido = random.choice(PAISES_NORDVPN)
        print(f"[IP ROTATION] Conectando a: {pais_elegido}")
        os.system(f'cd "{NORDVPN_PATH}" && nordvpn -c -g "{pais_elegido}"')
        
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
    parser.add_argument('--competencia', type=str, default='all', help=f"La competencia a scrapear. Opciones: {list(COMPETENCIAS_CONFIG.keys()) + ['all']}")
    args = parser.parse_args()

    tasks = generar_tareas(args.desde, args.hasta, args.competencia) if args.modo == 'historico' else []

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

        # 1. Creamos el pool manualmente, fuera de un bloque 'with'
        pool = multiprocessing.Pool(processes=args.procesos)

        try:
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

        finally:
            pool.join()
            pool.close()

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