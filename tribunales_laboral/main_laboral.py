# Archivo: main_laboral.py

import argparse
import multiprocessing
import json
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_laboral import scrape_worker
from verificacion_worker_laboral import verificacion_worker
from utils_laboral import forzar_cierre_navegadores, quedan_procesos_navegador

# Configuración centralizada
RUTA_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Resultados_Globales')
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, 'checkpoint_tribunales_laboral.json')
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

# --- Solo Laboral ---
TRIBUNALES_LABORAL = [
    {'id': '6', 'nombre': 'Juzgado de Letras y Garantía de Pozo Almonte'},
    {'id': '13', 'nombre': 'Juzgado de Letras de Tocopilla'},
    {'id': '14', 'nombre': 'Juzgado de Letras y Garantía de María Elena'},
    {'id': '26', 'nombre': 'Juzgado de Letras y Garantía de Taltal'},
    {'id': '27', 'nombre': 'Juzgado de Letras y Garantia de Chañaral'},
    {'id': '29', 'nombre': 'Juzgado de Letras de Diego de Almagro'},
    {'id': '34', 'nombre': 'Juzgado de Letras y Garantía de Freirina'},
    {'id': '36', 'nombre': '1° Juzgado de Letras de Vallenar'},
    {'id': '37', 'nombre': '2° Juzgado de Letras de Vallenar'},
    {'id': '46', 'nombre': 'Juzgado de Letras de Vicuña'},
    {'id': '47', 'nombre': 'Juzgado de Letras y Garantía de Andacollo'},
    {'id': '48', 'nombre': '1º Juzgado de Letras de Ovalle'},
    {'id': '49', 'nombre': '2º Juzgado de Letras de Ovalle'},
    {'id': '50', 'nombre': '3° Juzgado de Letras de Ovalle'},
    {'id': '51', 'nombre': 'Juzgado de Letras y Garantía de Combarbalá'},
    {'id': '52', 'nombre': 'Juzgado de Letras de Illapel'},
    {'id': '53', 'nombre': 'Juzgado de Letras y Garantía de los Vilos'},
    {'id': '83', 'nombre': '1º Juzgado de Letras de Quilpue'},
    {'id': '84', 'nombre': '2º Juzgado de Letras de Quilpue'},
    {'id': '85', 'nombre': 'Juzgado de Letras de Villa Alemana'},
    {'id': '86', 'nombre': 'Juzgado de Letras de Casablanca'},
    {'id': '87', 'nombre': 'Juzgado de Letras de La Ligua'},
    {'id': '88', 'nombre': 'Juzgado de Letras y Garantía de Petorca'},
    {'id': '89', 'nombre': '1º Juzgado de Letras de Los Andes'},
    {'id': '90', 'nombre': '2º Juzgado de Letras de Los Andes'},
    {'id': '94', 'nombre': 'Juzgado de Letras y Garantía de Putaendo'},
    {'id': '96', 'nombre': '1º Juzgado de Letras de Quillota'},
    {'id': '97', 'nombre': '2º Juzgado de Letras de Quillota'},
    {'id': '98', 'nombre': 'Juzgado de Letras de La Calera'},
    {'id': '99', 'nombre': 'Juzgado de Letras de Limache'},
    {'id': '101', 'nombre': '1° Juzgado de Letras de San Antonio'},
    {'id': '102', 'nombre': '2° Juzgado de Letras de San Antonio'},
    {'id': '103', 'nombre': 'Juzgado de Letras y Garantía de Isla de Pascua'},
    {'id': '111', 'nombre': '1º Juzgado de Letras de Rengo'},
    {'id': '113', 'nombre': 'Juzgado de Letras de San Vicente'},
    {'id': '114', 'nombre': '1º Juzgado de Letras y Garantia de Peumo'},
    {'id': '115', 'nombre': '1º Juzgado de Letras de San Fernando'},
    {'id': '116', 'nombre': '2º Juzgado de Letras de San Fernando'},
    {'id': '117', 'nombre': '1º Juzgado de Letras de Santa Cruz'},
    {'id': '119', 'nombre': 'Juzgado de Letras y Garantia de Pichilemu'},
    {'id': '126', 'nombre': 'Juzgado de Letras de Constitución'},
    {'id': '127', 'nombre': 'Juzgado de Letras y Garantía de Curepto'},
    {'id': '132', 'nombre': 'Juzgado de Letras y Garantía de Licantén'},
    {'id': '133', 'nombre': 'Juzgado de Letras de Molina'},
    {'id': '135', 'nombre': '1° Juzgado de Letras de Linares'},
    {'id': '136', 'nombre': '2° Juzgado de Letras de Linares'},
    {'id': '138', 'nombre': 'Juzgado de Letras de San Javier'},
    {'id': '139', 'nombre': 'Juzgado de Letras de Cauquenes'},
    {'id': '140', 'nombre': 'Juzgado de Letras y Garantía de Chanco'},
    {'id': '141', 'nombre': 'Juzgado de Letras de Parral'},
    {'id': '147', 'nombre': '1° Juzgado de Letras de San Carlos'},
    {'id': '149', 'nombre': 'Juzgado de Letras de Yungay'},
    {'id': '150', 'nombre': 'Juzgado de Letras y Garantía de Bulnes'},
    {'id': '151', 'nombre': 'Juzgado de Letras y Garantía de Coelemu'},
    {'id': '152', 'nombre': 'Juzgado de Letras y Garantía de Quirihue'},
    {'id': '157', 'nombre': 'Juzgado de Letras y Garantía de Mulchén'},
    {'id': '158', 'nombre': 'Juzgado de Letras y Garantía de Nacimiento'},
    {'id': '159', 'nombre': 'Juzgado de Letras y Garantía de Laja'},
    {'id': '160', 'nombre': 'Juzgado de Letras y Garantía de Yumbel'},
    {'id': '187', 'nombre': 'Juzgado de Letras de Tomé'},
    {'id': '188', 'nombre': 'Juzgado de Letras y Garantía de Florida'},
    {'id': '189', 'nombre': 'Juzgado de Letras y Garantía de Santa Juana'},
    {'id': '190', 'nombre': 'Juzgado de Letras y Garantía de Lota'},
    {'id': '191', 'nombre': '1er Juzgado de Letras de Coronel'},
    {'id': '192', 'nombre': '2do Juzgado de Letras de Coronel'},
    {'id': '193', 'nombre': 'Juzgado de Letras y Garantía de Lebu'},
    {'id': '194', 'nombre': 'Juzgado de Letras de Arauco'},
    {'id': '195', 'nombre': 'Juzgado de Letras y Garantía de Curanilahue'},
    {'id': '196', 'nombre': 'Juzgado de Letras de Cañete'},
    {'id': '204', 'nombre': '1º Juzgado de Letras de Angol'},
    {'id': '206', 'nombre': 'Juzgado de Letras y Garantía de Collipulli'},
    {'id': '207', 'nombre': 'Juzgado de Letras y Garantía de Traiguen'},
    {'id': '208', 'nombre': 'Juzgado de Letras de Victoria'},
    {'id': '209', 'nombre': 'Juzgado de Letras y Garantía de Curacautín'},
    {'id': '210', 'nombre': 'Juzgado de Letras de Loncoche'},
    {'id': '211', 'nombre': 'Juzgado de Letras de Pitrufquén'},
    {'id': '212', 'nombre': 'Juzgado de Letras de Villarrica'},
    {'id': '213', 'nombre': 'Juzgado de Letras de Nueva Imperial'},
    {'id': '214', 'nombre': 'Juzgado de Letras y Garantía de Pucón'},
    {'id': '215', 'nombre': 'Juzgado de Letras de Lautaro'},
    {'id': '216', 'nombre': 'Juzgado de Letras y Garantía de Carahue'},
    {'id': '222', 'nombre': 'Juzgado de Letras de Mariquina'},
    {'id': '223', 'nombre': 'Juzgado de Letras y Garantía de Paillaco'},
    {'id': '224', 'nombre': 'Juzgado de Letras de Los Lagos'},
    {'id': '225', 'nombre': 'Juzgado de Letras y Garantía de Panguipulli'},
    {'id': '226', 'nombre': 'Juzgado de Letras y Garantía de La Unión'},
    {'id': '227', 'nombre': 'Juzgado de Letras y Garantía de Río Bueno'},
    {'id': '238', 'nombre': '1º Juzgado de Letras de Puerto Varas'},
    {'id': '240', 'nombre': 'Juzgado de Letras y Garantía de Calbuco'},
    {'id': '241', 'nombre': 'Juzgado de Letras y Garantía de Maullín'},
    {'id': '243', 'nombre': 'Juzgado de Letras de Ancud'},
    {'id': '244', 'nombre': 'Juzgado de Letras y Garantía de Achao'},
    {'id': '245', 'nombre': 'Juzgado de Letras y Garantía de Chaitén'},
    {'id': '248', 'nombre': 'Juzgado de Letras y Garantía de Aysén'},
    {'id': '249', 'nombre': 'Juzgado de Letras y Garantía de Chile Chico'},
    {'id': '250', 'nombre': 'Juzgado de Letras y Garantía de Cochrane'},
    {'id': '257', 'nombre': 'Juzgado de Letras y Garantía de Puerto Natales'},
    {'id': '258', 'nombre': 'Juzgado de Letras y Garantía de Porvenir'},
    {'id': '373', 'nombre': '1° Juzgado de Letras de Talagante'},
    {'id': '374', 'nombre': '2do Juzgado de Letras de Talagante'},
    {'id': '375', 'nombre': '1er Juzgado de Letras de Melipilla'},
    {'id': '377', 'nombre': '1er Juzgado de Letras de Buin'},
    {'id': '378', 'nombre': '2do Juzgado de Letras de Buin'},
    {'id': '385', 'nombre': 'Juzgado de Letras y Garantía de Santa Bárbara'},
    {'id': '386', 'nombre': 'Juzgado de Letras y Garantía de Caldera'},
    {'id': '387', 'nombre': 'Juzgado de Letras de Colina'},
    {'id': '388', 'nombre': 'Juzgado de Letras de Peñaflor'},
    {'id': '659', 'nombre': 'Juzgado de Letras y Garantía de Los Muermos'},
    {'id': '660', 'nombre': 'Juzgado de Letras y Garantía de Quintero'},
    {'id': '946', 'nombre': 'Juzgado de Letras y Garantía de Toltén'},
    {'id': '947', 'nombre': 'Juzgado de Letras y Garantía de Purén'},
    {'id': '996', 'nombre': 'Juzgado de Letras y Garantía de Puerto Cisnes'},
    {'id': '1013', 'nombre': 'Juzgado de Letras y Garantía de Hualaihue'},
    {'id': '1150', 'nombre': 'Juzgado de Letras y Garantia de Litueche'},
    {'id': '1151', 'nombre': 'Juzgado de Letras y Garantia de Peralillo'},
    {'id': '1152', 'nombre': 'Juzgado de Letras y Garantía de Cabrero'},
    {'id': '1333', 'nombre': 'Juzgado de Letras del Trabajo de Arica'},
    {'id': '1334', 'nombre': 'Juzgado de Letras del Trabajo de Iquique'},
    {'id': '1335', 'nombre': 'Juzgado de Letras del Trabajo de Antofagasta'},
    {'id': '1336', 'nombre': 'Juzgado de Letras del Trabajo de Copiapó'},
    {'id': '1337', 'nombre': 'Juzgado de Letras del Trabajo de La Serena'},
    {'id': '1338', 'nombre': 'Juzgado de Letras del Trabajo de Valparaíso'},
    {'id': '1339', 'nombre': 'Juzgado de Letras del Trabajo de Rancagua'},
    {'id': '1340', 'nombre': 'Juzgado de Letras del Trabajo de Curicó'},
    {'id': '1341', 'nombre': 'Juzgado de Letras del Trabajo de Talca'},
    {'id': '1342', 'nombre': 'Juzgado de Letras del Trabajo de Chillán'},
    {'id': '1343', 'nombre': 'Juzgado de Letras del Trabajo de Concepción'},
    {'id': '1344', 'nombre': 'Juzgado de Letras del Trabajo de Temuco'},
    {'id': '1345', 'nombre': 'Juzgado de Letras del Trabajo de Valdivia'},
    {'id': '1346', 'nombre': 'Juzgado de Letras del Trabajo de Puerto Montt'},
    {'id': '1347', 'nombre': 'Juzgado de Letras del Trabajo de Punta Arenas'},
    {'id': '1348', 'nombre': '1º Juzgado de Letras del Trabajo de Santiago'},
    {'id': '1349', 'nombre': '2º Juzgado de Letras del Trabajo de Santiago'},
    {'id': '1351', 'nombre': 'Juzgado de Letras del Trabajo de San Miguel'},
    {'id': '1352', 'nombre': 'Juzgado de Letras del Trabajo de San Bernardo'},
    {'id': '1357', 'nombre': 'Juzgado de Letras del Trabajo de Calama'},
    {'id': '1358', 'nombre': 'Juzgado de Letras del Trabajo de San Felipe'},
    {'id': '1359', 'nombre': 'Juzgado de Letras del Trabajo de Los Angeles'},
    {'id': '1360', 'nombre': 'Juzgado de Letras del Trabajo de Osorno'},
    {'id': '1361', 'nombre': 'Juzgado de Letras del Trabajo de Castro'},
    {'id': '1362', 'nombre': 'Juzgado de Letras del Trabajo de Coyhaique'},
    {'id': '1363', 'nombre': 'Juzgado de Letras del Trabajo de Puente Alto'},
    {'id': '1500', 'nombre': 'Juzgado de Letras y Garantía de Alto Hospicio'},
    {'id': '1501', 'nombre': 'Juzgado de Letras de Mejillones'},
    {'id': '1502', 'nombre': 'Juzgado de Letras de Cabo de Hornos'},
    {'id': '9003', 'nombre': 'Portal'},
    {'id': '9005', 'nombre': 'Juzgado de Prueba 4º'},
    {'id': '9006', 'nombre': 'Juzgado de Prueba 5°'},
]

COMPETENCIAS_CONFIG = {
    "value": "4",  # Ajusta el value si es distinto para laboral
    "selector_id": "fecTribunal",
    "items": TRIBUNALES_LABORAL,
    "item_key_id": "tribunal_id",
    "item_key_nombre": "tribunal_nombre"
}

def generar_tareas(start_date_str, end_date_str, modulo_nombre="tribunales_laboral"):
    """Genera tareas con rangos semanales para módulos tribunales_* y diarios para otros."""
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []
    
    # Determinar incremento: semanal para tribunales_*, diario para otros
    es_tribunales = modulo_nombre.startswith('tribunales_')
    incremento = timedelta(weeks=1) if es_tribunales else timedelta(days=1)
    
    while current_date <= end_date:
        if es_tribunales:
            # Para módulos tribunales: rango semanal
            fecha_hasta = min(current_date + timedelta(days=6), end_date)
            fecha_desde_str = current_date.strftime('%d/%m/%Y')
            fecha_hasta_str = fecha_hasta.strftime('%d/%m/%Y')
            fecha_id_base = f"{current_date.strftime('%Y-%m-%d')}_to_{fecha_hasta.strftime('%Y-%m-%d')}"
        else:
            # Para otros módulos: día individual
            fecha_desde_str = fecha_hasta_str = current_date.strftime('%d/%m/%Y')
            fecha_id_base = current_date.strftime('%Y-%m-%d')
        
        for item in COMPETENCIAS_CONFIG["items"]:
            tarea_id = f"laboral_{fecha_id_base}_{item['id']}"
            tarea = {
                'id': tarea_id,
                'fecha_desde_str': fecha_desde_str,
                'fecha_hasta_str': fecha_hasta_str,
                'competencia_nombre': 'Laboral',
                'competencia_value': COMPETENCIAS_CONFIG['value'],
                'selector_id': COMPETENCIAS_CONFIG['selector_id'],
                'ruta_salida': RUTA_SALIDA,
                COMPETENCIAS_CONFIG["item_key_id"]: item['id'],
                COMPETENCIAS_CONFIG["item_key_nombre"]: item['nombre']
            }
            tareas.append(tarea)
        current_date += incremento
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
    parser = argparse.ArgumentParser(description="Orquestador de scraping judicial solo para competencia Laboral.")
    parser.add_argument('--modo', choices=['diario', 'historico'], default='historico')
    parser.add_argument('--desde', default="2024-01-01")
    parser.add_argument('--hasta', default="2024-01-31")
    parser.add_argument('--procesos', type=int, default=4, help="Número MÁXIMO de procesos concurrentes.")
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--tanda_size', type=int, default=2, help="Cuántos procesos iniciar a la vez.")
    parser.add_argument('--delay_tanda', type=int, default=90, help="Segundos de espera entre el inicio de cada tanda.")
    args = parser.parse_args()

    tasks = generar_tareas(args.desde, args.hasta, "tribunales_laboral") if args.modo == 'historico' else []

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