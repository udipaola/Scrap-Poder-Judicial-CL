# Archivo: main_tribunales_penal.py

import argparse
import multiprocessing
import json
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_penal import scrape_worker
from verificacion_worker_penal import verificacion_worker
from utils_penal import forzar_cierre_navegadores, quedan_procesos_navegador
import shutil
import glob
import tempfile
import logging

# Configuración centralizada
RUTA_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Resultados_Globales')
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, 'checkpoint_tribunales_penal.json')
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

# --- Solo Penal ---
TRIBUNALES_PENAL = [
    {'id': '6', 'nombre': 'Juzgado De Letras Y Garantía De Pozo Almonte.'},
    {'id': '14', 'nombre': 'Juzgado De Letras Y Garantía De María Elena.'},
    {'id': '26', 'nombre': 'Juzgado De Letras Y Garantía De Taltal.'},
    {'id': '27', 'nombre': 'Juzgado De Letras Y Garantía De Chañaral.'},
    {'id': '34', 'nombre': 'Juzgado De Letras Y Garantía De Freirina.'},
    {'id': '47', 'nombre': 'Juzgado De Letras Y Garantía De Andacollo.'},
    {'id': '51', 'nombre': 'Juzgado De Letras Y Garantía De Combarbala.'},
    {'id': '53', 'nombre': 'Juzgado De Letras Y Garantía De Los Vilos.'},
    {'id': '88', 'nombre': 'Juzgado De Letras Y Garantía De Petorca.'},
    {'id': '94', 'nombre': 'Juzgado De Letras Y Garantía De Putaendo.'},
    {'id': '103', 'nombre': 'Juzgado De Letras Y Garantía De Isla De Pascua.'},
    {'id': '114', 'nombre': '1º Juzgado De Letras Y Garantía De Peumo.'},
    {'id': '119', 'nombre': 'Juzgado De Letras Y Garantía De Pichilemu.'},
    {'id': '127', 'nombre': 'Juzgado De Letras Y Garantía De Curepto.'},
    {'id': '132', 'nombre': 'Juzgado De Letras Y Garantía De Licanten.'},
    {'id': '140', 'nombre': 'Juzgado De Letras Y Garantía De Chanco.'},
    {'id': '150', 'nombre': 'Juzgado De Letras Y Garantía De Bulnes.'},
    {'id': '151', 'nombre': 'Juzgado De Letras Y Garantía De Coelemu.'},
    {'id': '152', 'nombre': 'Juzgado De Letras Y Garantía De Quirihue.'},
    {'id': '157', 'nombre': 'Juzgado De Letras Y Garantía De Mulchen.'},
    {'id': '158', 'nombre': 'Juzgado De Letras Y Garantía De Nacimiento.'},
    {'id': '159', 'nombre': 'Juzgado De Letras Y Garantía De Laja.'},
    {'id': '160', 'nombre': 'Juzgado De Letras Y Garantía De Yumbel.'},
    {'id': '188', 'nombre': 'Juzgado De Letras Y Garantía De Florida.'},
    {'id': '189', 'nombre': 'Juzgado De Letras Y Garantía De Santa Juana.'},
    {'id': '190', 'nombre': 'Juzgado De Letras Y Garantía De Lota.'},
    {'id': '193', 'nombre': 'Juzgado De Letras Y Garantía De Lebu.'},
    {'id': '195', 'nombre': 'Juzgado De Letras Y Garantía De Curanilahue.'},
    {'id': '206', 'nombre': 'Juzgado De Letras Y Garantía De Collipulli.'},
    {'id': '207', 'nombre': 'Juzgado De Letras Y Garantía De Traiguen.'},
    {'id': '209', 'nombre': 'Juzgado De Letras Y Garantía De Curacautin.'},
    {'id': '214', 'nombre': 'Juzgado De Letras Y Garantía De Pucon.'},
    {'id': '216', 'nombre': 'Juzgado De Letras Y Garantía De Carahue.'},
    {'id': '223', 'nombre': 'Juzgado De Letras Y Garantía De Paillaco.'},
    {'id': '225', 'nombre': 'Juzgado De Letras Y Garantía De Panguipulli.'},
    {'id': '226', 'nombre': 'Juzgado De Letras Y Garantia De La Union.'},
    {'id': '227', 'nombre': 'Juzgado De Letras Y Garantía De Río Bueno.'},
    {'id': '240', 'nombre': 'Juzgado De Letras Y Garantía De Calbuco.'},
    {'id': '241', 'nombre': 'Juzgado De Letras Y Garantía De Maullin.'},
    {'id': '244', 'nombre': 'Juzgado De Letras Y Garantía De Achao.'},
    {'id': '245', 'nombre': 'Juzgado De Letras Y Garantía De Chaiten.'},
    {'id': '248', 'nombre': 'Juzgado De Letras Y Garantía De Puerto Aysen.'},
    {'id': '249', 'nombre': 'Juzgado De Letras Y Garantía De Chile Chico.'},
    {'id': '250', 'nombre': 'Juzgado De Letras Y Garantía De Cochrane.'},
    {'id': '257', 'nombre': 'Juzgado De Letras Y Garantía De Puerto Natales.'},
    {'id': '258', 'nombre': 'Juzgado De Letras Y Garantía De Porvenir.'},
    {'id': '385', 'nombre': 'Juzgado De Letras Y Garantía De Santa Barbara.'},
    {'id': '386', 'nombre': 'Juzgado De Letras Y Garantía De Caldera.'},
    {'id': '659', 'nombre': 'Juzgado De Letras Y Garantía De Los Muermos.'},
    {'id': '660', 'nombre': 'Juzgado De Letras Y Garantía De Quintero.'},
    {'id': '662', 'nombre': 'Juzgado De Letras Y Garantía De Quellon.'},
    {'id': '927', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De La Serena.'},
    {'id': '928', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Ovalle.'},
    {'id': '929', 'nombre': 'Juzgado De Garantía De La Serena.'},
    {'id': '930', 'nombre': 'Juzgado De Garantía De Coquimbo.'},
    {'id': '931', 'nombre': 'Juzgado De Garantía De Vicuña.'},
    {'id': '932', 'nombre': 'Juzgado De Garantía De Ovalle.'},
    {'id': '933', 'nombre': 'Juzgado De Garantía De Illapel.'},
    {'id': '934', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Temuco.'},
    {'id': '935', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Angol.'},
    {'id': '936', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Villarrica.'},
    {'id': '937', 'nombre': 'Juzgado De Garantía De Temuco.'},
    {'id': '938', 'nombre': 'Juzgado De Garantía De Pitrufquen.'},
    {'id': '939', 'nombre': 'Juzgado De Garantía De Villarrica.'},
    {'id': '940', 'nombre': 'Juzgado De Garantía De Angol.'},
    {'id': '941', 'nombre': 'Juzgado De Garantía De Victoria.'},
    {'id': '942', 'nombre': 'Juzgado De Garantía De Nueva Imperial.'},
    {'id': '943', 'nombre': 'Juzgado De Garantía De Lautaro.'},
    {'id': '944', 'nombre': 'Juzgado De Garantía De Loncoche.'},
    {'id': '946', 'nombre': 'Juzgado De Letras Y Garantía De Tolten.'},
    {'id': '947', 'nombre': 'Juzgado De Letras Y Garantía De Puren.'},
    {'id': '948', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Calama.'},
    {'id': '949', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Antofagasta.'},
    {'id': '950', 'nombre': 'Juzgado De Garantía De Tocopilla.'},
    {'id': '951', 'nombre': 'Juzgado De Garantía De Calama.'},
    {'id': '952', 'nombre': 'Juzgado De Garantía De Antofagasta.'},
    {'id': '953', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Copiapo.'},
    {'id': '954', 'nombre': 'Juzgado De Garantía De Diego De Almagro.'},
    {'id': '955', 'nombre': 'Juzgado De Garantía De Copiapo.'},
    {'id': '956', 'nombre': 'Juzgado De Garantía De Vallenar.'},
    {'id': '957', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Curico.'},
    {'id': '958', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Talca.'},
    {'id': '959', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Linares.'},
    {'id': '960', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Cauquenes.'},
    {'id': '961', 'nombre': 'Juzgado De Garantía De Curico.'},
    {'id': '962', 'nombre': 'Juzgado De Garantía De Molina.'},
    {'id': '963', 'nombre': 'Juzgado De Garantía De Constitución.'},
    {'id': '964', 'nombre': 'Juzgado De Garantía De Talca.'},
    {'id': '965', 'nombre': 'Juzgado De Garantía De San Javier.'},
    {'id': '966', 'nombre': 'Juzgado De Garantía De Cauquenes.'},
    {'id': '967', 'nombre': 'Juzgado De Garantía De Linares.'},
    {'id': '968', 'nombre': 'Juzgado De Garantía De Parral.'},
    {'id': '988', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Arica.'},
    {'id': '989', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Iquique.'},
    {'id': '990', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Coyhaique.'},
    {'id': '991', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Punta Arenas.'},
    {'id': '992', 'nombre': 'Juzgado De Garantía De Arica.'},
    {'id': '993', 'nombre': 'Juzgado De Garantía De Iquique.'},
    {'id': '994', 'nombre': 'Juzgado De Garantía De Coyhaique.'},
    {'id': '995', 'nombre': 'Juzgado De Garantía De Punta Arenas.'},
    {'id': '996', 'nombre': 'Juzgado De Letras Y Garantía De Cisnes.'},
    {'id': '1013', 'nombre': 'Juzgado De Letras Y Garantía De Hualaihue'},
    {'id': '1045', 'nombre': 'Juzgado De Garantía De Valparaíso.'},
    {'id': '1046', 'nombre': 'Juzgado De Garantia De Viña Del Mar.'},
    {'id': '1047', 'nombre': 'Juzgado De Garantía De Quilpué.'},
    {'id': '1048', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Viña Del Mar.'},
    {'id': '1049', 'nombre': 'Juzgado De Garantía De San Antonio.'},
    {'id': '1050', 'nombre': 'Juzgado De Garantía De Casablanca.'},
    {'id': '1051', 'nombre': 'Juzgado De Garantía De La Ligua.'},
    {'id': '1052', 'nombre': 'Juzgado De Garantía De San Felipe.'},
    {'id': '1053', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Quillota.'},
    {'id': '1054', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Valparaíso.'},
    {'id': '1055', 'nombre': 'Juzgado De Garantía De Limache.'},
    {'id': '1056', 'nombre': 'Juzgado De Garantía De La Calera.'},
    {'id': '1057', 'nombre': 'Juzgado De Garantía De Quillota.'},
    {'id': '1058', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Los Andes.'},
    {'id': '1059', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De San Felipe.'},
    {'id': '1060', 'nombre': 'Juzgado De Garantía De Los Andes.'},
    {'id': '1061', 'nombre': 'Juzgado De Garantía De Villa Alemana.'},
    {'id': '1062', 'nombre': 'Tribunal De Juicio Oral En Lo Penal San Antonio.'},
    {'id': '1063', 'nombre': 'Juzgado De Garantía De San Fernando.'},
    {'id': '1064', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Santa Cruz.'},
    {'id': '1065', 'nombre': 'Juzgado De Garantía De Santa Cruz.'},
    {'id': '1067', 'nombre': 'Juzgado De Garantía De Rengo.'},
    {'id': '1068', 'nombre': 'Tribunal De Juicio Oral En Lo Penal San Fernando.'},
    {'id': '1069', 'nombre': 'Juzgado De Garantía De Graneros.'},
    {'id': '1070', 'nombre': 'Juzgado De Garantía De Rancagua.'},
    {'id': '1071', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Rancagua.'},
    {'id': '1072', 'nombre': 'Juzgado De Garantía De Chillán.'},
    {'id': '1073', 'nombre': 'Juzgado De Garantía De Yungay.'},
    {'id': '1074', 'nombre': 'Juzgado De Garantía De San Carlos.'},
    {'id': '1075', 'nombre': 'Juzgado De Garantía De San Pedro De La Paz.'},
    {'id': '1076', 'nombre': 'Juzgado De Garantía De Cañete.'},
    {'id': '1077', 'nombre': 'Juzgado De Garantía De Arauco.'},
    {'id': '1078', 'nombre': 'Juzgado De Garantía De Coronel.'},
    {'id': '1079', 'nombre': 'Juzgado De Garantía De Tomé.'},
    {'id': '1080', 'nombre': 'Juzgado De Garantía De Talcahuano.'},
    {'id': '1081', 'nombre': 'Juzgado De Garantía De Chiguayante.'},
    {'id': '1082', 'nombre': 'Juzgado De Garantía De Concepción.'},
    {'id': '1083', 'nombre': 'Juzgado De Garantía De Los Angeles.'},
    {'id': '1084', 'nombre': 'Juzgado De Garantía De Valdivia.'},
    {'id': '1085', 'nombre': 'Juzgado De Garantía De Mariquina.'},
    {'id': '1086', 'nombre': 'Juzgado De Garantía De Los Lagos.'},
    {'id': '1087', 'nombre': 'Juzgado De Garantía De Río Negro.'},
    {'id': '1088', 'nombre': 'Juzgado De Garantía De Osorno.'},
    {'id': '1089', 'nombre': 'Juzgado De Garantía De Castro.'},
    {'id': '1090', 'nombre': 'Juzgado De Garantía De Puerto Montt.'},
    {'id': '1091', 'nombre': 'Juzgado De Garantía De Puerto Varas.'},
    {'id': '1092', 'nombre': 'Juzgado De Garantía De Ancud.'},
    {'id': '1093', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Chillán.'},
    {'id': '1094', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Concepción.'},
    {'id': '1095', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Valdivia.'},
    {'id': '1096', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Puerto Montt.'},
    {'id': '1097', 'nombre': 'Juzgado De Garantía De San Vicente De Tagua-Tagua.'},
    {'id': '1150', 'nombre': 'Juzgado De Letras Y Garantía De Litueche.'},
    {'id': '1151', 'nombre': 'Juzgado De Letras Y Garantía De Peralillo.'},
    {'id': '1152', 'nombre': 'Juzgado De Letras Y Garantía De Cabrero.'},
    {'id': '1220', 'nombre': '1º Juzgado De Garantía De Santiago'},
    {'id': '1221', 'nombre': '2º Juzgado De Garantía De Santiago'},
    {'id': '1222', 'nombre': '3º Juzgado De Garantía De Santiago'},
    {'id': '1223', 'nombre': '4º Juzgado De Garantía De Santiago'},
    {'id': '1224', 'nombre': '5º Juzgado De Garantía De Santiago'},
    {'id': '1225', 'nombre': '6º Juzgado De Garantía De Santiago'},
    {'id': '1226', 'nombre': '7º Juzgado De Garantía De Santiago'},
    {'id': '1227', 'nombre': '8º Juzgado De Garantía De Santiago'},
    {'id': '1228', 'nombre': '9º Juzgado De Garantía De Santiago'},
    {'id': '1229', 'nombre': '10º Juzgado De Garantía De Santiago'},
    {'id': '1230', 'nombre': '11º Juzgado De Garantía De Santiago'},
    {'id': '1231', 'nombre': '12º Juzgado De Garantía De Santiago'},
    {'id': '1232', 'nombre': '13º Juzgado De Garantía De Santiago'},
    {'id': '1233', 'nombre': '14º Juzgado De Garantía De Santiago'},
    {'id': '1234', 'nombre': '15º Juzgado De Garantía De Santiago'},
    {'id': '1235', 'nombre': 'Juzgado De Garantía De Colina'},
    {'id': '1236', 'nombre': 'Juzgado De Garantía De Puente Alto'},
    {'id': '1237', 'nombre': 'Juzgado De Garantía De San Bernardo'},
    {'id': '1238', 'nombre': 'Juzgado De Garantía De Melipilla'},
    {'id': '1239', 'nombre': 'Juzgado De Garantía De Curacaví'},
    {'id': '1240', 'nombre': 'Juzgado De Garantía De Talagante'},
    {'id': '1244', 'nombre': '1º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1245', 'nombre': '2º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1246', 'nombre': '3º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1247', 'nombre': '4º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1248', 'nombre': '5º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1249', 'nombre': '6º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1250', 'nombre': '7º Tribunal De Juicio Oral En Lo Penal De Santiago'},
    {'id': '1251', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Osorno'},
    {'id': '1320', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Talagante'},
    {'id': '1321', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Colina'},
    {'id': '1322', 'nombre': 'Tribunal De Juicio Oral En Lo Penal Puente Alto'},
    {'id': '1323', 'nombre': 'Tribunal De Juicio Oral En Lo Penal San Bernardo'},
    {'id': '1325', 'nombre': 'Tribunal Oral En Lo Penal De Los Angeles'},
    {'id': '1326', 'nombre': 'Tribunal Oral En Lo Penal De Cañete'},
    {'id': '1328', 'nombre': 'Tribunal Oral En Lo Penal De Castro'},
    {'id': '1355', 'nombre': 'Tribunal De Juicio Oral En Lo Penal De Melipilla'},
    {'id': '1500', 'nombre': 'Juzgado De Letras Y Garantia De Alto Hospicio'},
    {'id': '1501', 'nombre': 'Juzgado De Letras Y Garantia De Mejillones'},
    {'id': '1502', 'nombre': 'Juzgado De Letras Y Garantia De Cabo De Hornos'},
    {'id': '6000', 'nombre': 'Corte Suprema - Primera Instancia.'},
    {'id': '8002', 'nombre': 'Tribunal Juicio Oral En Lo Penal Prueba Iii'},
    {'id': '8010', 'nombre': 'Coordinacion'},
]

COMPETENCIAS_CONFIG = {
    "value": "5",  # Ajusta el value si es distinto para penal
    "selector_id": "fecTribunal",
    "items": TRIBUNALES_PENAL,
    "item_key_id": "tribunal_id",
    "item_key_nombre": "tribunal_nombre"
}

def generar_tareas(start_date_str, end_date_str, modulo_nombre="tribunales_penal"):
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
            tarea_id = f"penal_{fecha_id_base}_{item['id']}"
            tarea = {
                'id': tarea_id,
                'fecha_desde_str': fecha_desde_str,
                'fecha_hasta_str': fecha_hasta_str,
                'competencia_nombre': 'Penal',
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
    parser = argparse.ArgumentParser(description="Orquestador de scraping judicial solo para competencia Penal.")
    parser.add_argument('--modo', choices=['diario', 'historico'], default='historico')
    parser.add_argument('--desde', default="2024-01-01")
    parser.add_argument('--hasta', default="2024-01-31")
    parser.add_argument('--procesos', type=int, default=4, help="Número MÁXIMO de procesos concurrentes.")
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--debug', action='store_true', help="Activar modo debug para logs detallados.")
    parser.add_argument('--tanda_size', type=int, default=2, help="Cuántos procesos iniciar a la vez.")
    parser.add_argument('--delay_tanda', type=int, default=90, help="Segundos de espera entre el inicio de cada tanda.")
    args = parser.parse_args()

    tasks = generar_tareas(args.desde, args.hasta, "tribunales_penal") if args.modo == 'historico' else []

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
            tasks_para_pool = [(task, lock, args.headless, args.debug, stop_event) for task in tareas_pendientes]
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
            # Usar print o logging.warning si está configurado
            print(f"ADVERTENCIA: No se pudo borrar el perfil huérfano '{perfil}'. Causa: {e}")
            
    print(f"--- Limpieza finalizada. Se eliminaron {borrados}/{len(perfiles_a_borrar)} perfiles. ---")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    limpiar_perfiles_antiguos()
    forzar_cierre_navegadores() # Cierre forzado al inicio
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