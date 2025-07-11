# Archivo: main_civil.py

import argparse
import multiprocessing
import json
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from worker_civil import scrape_worker
from verificacion_worker_civil import verificacion_worker
from utils_civil import forzar_cierre_navegadores, quedan_procesos_navegador
import shutil
import glob
import tempfile
import logging

# --- INICIO: Configuración Centralizada ---

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
NOMBRE_MODULO = os.path.basename(DIRECTORIO_ACTUAL)
RUTA_SALIDA = os.path.join(DIRECTORIO_ACTUAL, '..', 'Resultados_Globales')
os.makedirs(RUTA_SALIDA, exist_ok=True)
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, f"checkpoint_{NOMBRE_MODULO}.json")
NORDVPN_PATH = r"C:\Program Files\NordVPN"
PAISES_NORDVPN = ["Chile", "Argentina", "Bolivia", "Paraguay", "Uruguay", "Peru"]

TRIBUNALES_CIVIL = [
    {'id': '2', 'nombre': '1º Juzgado de Letras de Arica'},
    {'id': '1400', 'nombre': '1º Juzgado De Letras de Arica ex 4°'},
    {'id': '3', 'nombre': '2º Juzgado de Letras de Arica'},
    {'id': '1401', 'nombre': '2º Juzgado De Letras de Arica ex 4°'},
    {'id': '4', 'nombre': '3º Juzgado de Letras de Arica'},
    {'id': '5', 'nombre': '3º Juzgado de Letras de Arica Ex 4º'},
    {'id': '6', 'nombre': 'Juzgado de Letras y Gar. Pozo Almonte'},
    {'id': '9', 'nombre': '1º Juzgado de Letras de Iquique'},
    {'id': '10', 'nombre': '2º Juzgado de Letras de Iquique'},
    {'id': '11', 'nombre': '3º Juzgado de Letras de Iquique'},
    {'id': '13', 'nombre': 'Juzgado de Letras Tocopilla'},
    {'id': '14', 'nombre': 'Juzgado de Letras y Gar.de María Elena'},
    {'id': '16', 'nombre': '1º Juzgado de Letras de Calama'},
    {'id': '17', 'nombre': '2º Juzgado de Letras de Calama'},
    {'id': '658', 'nombre': '3º Juzgado de Letras de Calama'},
    {'id': '26', 'nombre': 'Juzgado de Letras y Gar. de Taltal'},
    {'id': '1041', 'nombre': '1º Juzgado de Letras Civil de Antofagasta'},
    {'id': '1042', 'nombre': '2º Juzgado de Letras Civil de Antofagasta'},
    {'id': '1043', 'nombre': '3º Juzgado de Letras Civil de Antofagasta'},
    {'id': '1044', 'nombre': '4 ° Juzgado de Letras Civil de Antofagasta'},
    {'id': '1501', 'nombre': 'Juzgado de Letras y Garantía Mejillones'},
    {'id': '27', 'nombre': 'Juzgado de Letras y Gar. de Chañaral'},
    {'id': '29', 'nombre': 'Juzgado de Letras de Diego de Almagro'},
    {'id': '31', 'nombre': '1º Juzgado de Letras de Copiapó'},
    {'id': '32', 'nombre': '2º Juzgado de Letras de Copiapó'},
    {'id': '33', 'nombre': '3º Juzgado de Letras de Copiapó'},
    {'id': '34', 'nombre': 'Juzgado de Letras y Gar.de Freirina'},
    {'id': '926', 'nombre': '4º Juzgado de Letras de Copiapó'},
    {'id': '36', 'nombre': '1º Juzgado de Letras de Vallenar'},
    {'id': '37', 'nombre': '2º Juzgado de Letras de Vallenar'},
    {'id': '386', 'nombre': 'Juzgado de Letras y Gar.de Caldera'},
    {'id': '40', 'nombre': '1º Juzgado de Letras de la Serena'},
    {'id': '41', 'nombre': '2º Juzgado de Letras de la Serena'},
    {'id': '42', 'nombre': '3º Juzgado de Letras de la Serena'},
    {'id': '43', 'nombre': '1º Juzgado de Letras de Coquimbo'},
    {'id': '44', 'nombre': '2º Juzgado de Letras de Coquimbo'},
    {'id': '45', 'nombre': '3º Juzgado de Letras de Coquimbo'},
    {'id': '46', 'nombre': 'Juzgado de Letras de Vicuña'},
    {'id': '47', 'nombre': 'Juzgado de letras y garantía de Andacollo'},
    {'id': '48', 'nombre': '1º Juzgado de Letras de Ovalle'},
    {'id': '49', 'nombre': '2º Juzgado de Letras de Ovalle'},
    {'id': '50', 'nombre': '3º Juzgado de Letras de Ovalle'},
    {'id': '51', 'nombre': 'Juzgado de Letras y Gar.de Combarbalá'},
    {'id': '52', 'nombre': 'Juzgado de Letras de Illapel'},
    {'id': '53', 'nombre': 'Juzgado de Letras y Gar. de los Vilos'},
    {'id': '56', 'nombre': '1º Juzgado Civil de Valparaíso'},
    {'id': '55', 'nombre': '2º Juzgado Civil de Valparaíso'},
    {'id': '54', 'nombre': '3º Juzgado Civil de Valparaíso'},
    {'id': '59', 'nombre': '4º Juzgado Civil de Valparaíso'},
    {'id': '60', 'nombre': '5º Juzgado Civil de Valparaíso'},
    {'id': '57', 'nombre': '1º Juzgado Civil de Viña del Mar'},
    {'id': '58', 'nombre': '2º Juzgado Civil de Viña del Mar'},
    {'id': '61', 'nombre': '3º Juzgado Civil de Viña del Mar'},
    {'id': '83', 'nombre': '1º Juzgado de Letras de Quilpue'},
    {'id': '84', 'nombre': '2º Juzgado de Letras de Quilpue'},
    {'id': '85', 'nombre': 'Juzgado de Letras de Villa Alemana'},
    {'id': '86', 'nombre': 'Juzgado de Letras de Casablanca'},
    {'id': '87', 'nombre': 'Juzgado de Letras de La Ligua'},
    {'id': '88', 'nombre': 'Juzgado de Letras y Gar. de Petorca'},
    {'id': '89', 'nombre': '1º Juzgado de Letras de Los Andes'},
    {'id': '90', 'nombre': '2º Juzgado de Letras de Los Andes'},
    {'id': '92', 'nombre': '1º Juzgado de Letras de San Felipe'},
    {'id': '93', 'nombre': '1º Juzgado de Letras de San Felipe Ex 2º'},
    {'id': '94', 'nombre': 'Juzgado de Letras y Gar.de Putaendo'},
    {'id': '96', 'nombre': '1º Juzgado de Letras de Quillota'},
    {'id': '97', 'nombre': '2º Juzgado de Letras de Quillota'},
    {'id': '98', 'nombre': 'Juzgado de Letras de La Calera'},
    {'id': '99', 'nombre': 'Juzgado de Letras de Limache'},
    {'id': '101', 'nombre': '1º Juzgado de Letras de San Antonio'},
    {'id': '102', 'nombre': '2º Juzgado de Letras de San Antonio'},
    {'id': '103', 'nombre': 'Juzgado de Letras y Gar. de Isla de Pascua'},
    {'id': '660', 'nombre': 'Juzgado de Letras y Gar.de Quintero'},
    {'id': '110', 'nombre': '1º Juzgado Civil de Rancagua'},
    {'id': '969', 'nombre': '2º Juzgado Civil de Rancagua'},
    {'id': '111', 'nombre': '1º Juzgado de Letras de Rengo'},
    {'id': '113', 'nombre': 'Juzgado de Letras de San Vicente de Tagua Tagua'},
    {'id': '114', 'nombre': '1º Juzgado de Letras y Gar.de Peumo'},
    {'id': '115', 'nombre': '1º Juzgado de Letras de San Fernando'},
    {'id': '116', 'nombre': '2º Juzgado de Letras de San Fernando'},
    {'id': '117', 'nombre': '1º Juzgado de Letras de Santa Cruz'},
    {'id': '118', 'nombre': '1º Juzgado De Letras De Santa Cruz Ex 2°'},
    {'id': '119', 'nombre': 'Juzgado de Letras y Gar.de Pichilemu'},
    {'id': '1150', 'nombre': 'Juzgado de Letras y Gar.de Litueche'},
    {'id': '1151', 'nombre': 'Juzgado de Letras y Gar.de Peralillo'},
    {'id': '122', 'nombre': '1º Juzgado de Letras de Talca'},
    {'id': '123', 'nombre': '2º Juzgado de Letras de Talca'},
    {'id': '124', 'nombre': '3º Juzgado de Letras de Talca'},
    {'id': '125', 'nombre': '4º Juzgado de Letras de Talca'},
    {'id': '126', 'nombre': 'Juzgado de Letras de Constitución'},
    {'id': '127', 'nombre': 'Juzgado De Letras Y Gar. de Curepto'},
    {'id': '129', 'nombre': '1º Juzgado de Letras de Curicó'},
    {'id': '130', 'nombre': '2º Juzgado de Letras de Curicó'},
    {'id': '131', 'nombre': '2º Juzgado de Letras de Curicó Ex 3°'},
    {'id': '132', 'nombre': 'Juzgado De Letras Y Gar. de Licantén'},
    {'id': '133', 'nombre': 'Juzgado de Letras de Molina'},
    {'id': '135', 'nombre': '1º Juzgado de Letras de Linares'},
    {'id': '136', 'nombre': '2º Juzgado de Letras de Linares'},
    {'id': '138', 'nombre': 'Juzgado de Letras de San Javier'},
    {'id': '139', 'nombre': 'Juzgado de Letras de Cauquenes'},
    {'id': '140', 'nombre': 'Juzgado de Letras y Gar. de Chanco'},
    {'id': '141', 'nombre': 'Juzgado de Letras de Parral'},
    {'id': '145', 'nombre': '1º Juzgado Civil de Chillán'},
    {'id': '146', 'nombre': '2º Juzgado Civil de Chillán'},
    {'id': '147', 'nombre': '1º Juzgado de Letras de San Carlos'},
    {'id': '149', 'nombre': 'Juzgado de Letras de Yungay'},
    {'id': '150', 'nombre': 'Juzgado de Letras y Gar. de Bulnes'},
    {'id': '151', 'nombre': 'Juzgado de Letras y Gar.de Coelemu'},
    {'id': '152', 'nombre': 'Juzgado de Letras y Gar.de Quirihue'},
    {'id': '154', 'nombre': '1º Juzgado de Letras de Los Angeles'},
    {'id': '155', 'nombre': '2º Juzgado de Letras de Los Angeles'},
    {'id': '156', 'nombre': '2° Juzgado de Letras de Los Angeles ex 3°'},
    {'id': '157', 'nombre': 'Juzgado de Letras y Gar. de Mulchen'},
    {'id': '158', 'nombre': 'Juzgado de Letras y Gar.de Nacimiento'},
    {'id': '159', 'nombre': 'Juzgado de Letras y Gar.de Laja'},
    {'id': '160', 'nombre': 'Juzgado de Letras y Gar.de Yumbel'},
    {'id': '161', 'nombre': '1º Juzgado Civil de Concepción'},
    {'id': '162', 'nombre': '2º Juzgado Civil de Concepción'},
    {'id': '163', 'nombre': '3º Juzgado Civil de Concepción'},
    {'id': '179', 'nombre': '1º Juzgado Civil de Talcahuano'},
    {'id': '180', 'nombre': '2º Juzgado Civil de Talcahuano'},
    {'id': '187', 'nombre': 'Juzgado de Letras de Tomé'},
    {'id': '188', 'nombre': 'Juzgado de Letras y Gar.de Florida'},
    {'id': '189', 'nombre': 'Juzgado de Letras y Gar.de Santa Juana'},
    {'id': '190', 'nombre': 'Juzgado de Letras y Gar. de Lota'},
    {'id': '191', 'nombre': '1º Juzgado de Letras de Coronel'},
    {'id': '192', 'nombre': '2º Juzgado de Letras de Coronel'},
    {'id': '193', 'nombre': 'Juzgado de Letras y Gar.de Lebu'},
    {'id': '194', 'nombre': 'Juzgado de Letras de Arauco'},
    {'id': '195', 'nombre': 'Juzgado de Letras y Gar.de Curanilahue'},
    {'id': '196', 'nombre': 'Juzgado de Letras de Cañete'},
    {'id': '385', 'nombre': 'Juzgado de Letras y Gar. Santa Bárbara'},
    {'id': '1152', 'nombre': 'Juzgado de Letras y Gar.de Cabrero'},
    {'id': '197', 'nombre': '1º Juzgado Civil de Temuco'},
    {'id': '198', 'nombre': '2º Juzgado Civil de Temuco'},
    {'id': '204', 'nombre': 'Juzgado de Letras de Angol'},
    {'id': '206', 'nombre': 'Juzgado de Letras y Gar.de Collipulli'},
    {'id': '207', 'nombre': 'Juzgado de Letras y Gar.de Traiguén'},
    {'id': '208', 'nombre': 'Juzgado de Letras de Victoria'},
    {'id': '209', 'nombre': 'Juzgado de Letras y Gar.de Curacautin'},
    {'id': '210', 'nombre': 'Juzgado de Letras Loncoche'},
    {'id': '211', 'nombre': 'Juzgado de Letras de Pitrufquen'},
    {'id': '212', 'nombre': 'Juzgado de Letras de Villarrica'},
    {'id': '213', 'nombre': 'Juzgado de Letras de Nueva Imperial'},
    {'id': '214', 'nombre': 'Juzgado de Letras y Gar.de Pucón'},
    {'id': '215', 'nombre': 'Juzgado de Letras de Lautaro'},
    {'id': '216', 'nombre': 'Juzgado de Letras y Gar.de Carahue'},
    {'id': '406', 'nombre': '3º Juzgado Civil de Temuco'},
    {'id': '946', 'nombre': 'Juzgado de Letras y Gar.de Tolten'},
    {'id': '947', 'nombre': 'Juzgado de Letras y Gar.de Puren'},
    {'id': '220', 'nombre': '1º Juzgado Civil de Valdivia'},
    {'id': '221', 'nombre': '2º Juzgado Civil de Valdivia'},
    {'id': '222', 'nombre': 'Juzgado de Letras de Mariquina'},
    {'id': '223', 'nombre': 'Juzgado de Letras y Gar.de Paillaco'},
    {'id': '224', 'nombre': 'Juzgado de Letras Los Lagos'},
    {'id': '225', 'nombre': 'Juzgado de Letras y Gar. de Panguipulli'},
    {'id': '226', 'nombre': 'Juzgado de Letras y Gar.de la Unión'},
    {'id': '227', 'nombre': 'Juzgado de Letras y Gar.de Río Bueno'},
    {'id': '229', 'nombre': '1º Juzgado de Letras de Osorno'},
    {'id': '230', 'nombre': '2º Juzgado de Letras de Osorno'},
    {'id': '233', 'nombre': 'Juzgado de Letras de Rio Negro'},
    {'id': '237', 'nombre': '1º Juzgado Civil de Puerto Montt'},
    {'id': '1012', 'nombre': '2º Juzgado Civil de Puerto Montt'},
    {'id': '238', 'nombre': 'Juzgado de Letras de Puerto Varas'},
    {'id': '240', 'nombre': 'Juzgado de Letras y Gar.de Calbuco'},
    {'id': '241', 'nombre': 'Juzgado de Letras y Gar. de Maullin'},
    {'id': '242', 'nombre': 'Juzgado de Letras de Castro'},
    {'id': '243', 'nombre': 'Juzgado de Letras de Ancud'},
    {'id': '244', 'nombre': 'Juzgado de Letras y Garantía de Achao'},
    {'id': '245', 'nombre': 'Juzgado de Letras y Gar. de Chaitén'},
    {'id': '659', 'nombre': 'Juzgado de Letras y Gar. de Los Muermos'},
    {'id': '662', 'nombre': 'Juzgado de Letras y Gar. de Quellón'},
    {'id': '1013', 'nombre': 'Juzgado de Letras y Gar. de Hualaihue'},
    {'id': '246', 'nombre': '1º Juzgado de Letras de Coyhaique'},
    {'id': '247', 'nombre': '1º Juzgado de Letras de Coyhaique Ex 2º'},
    {'id': '248', 'nombre': 'Juzgado de Letras y Gar.de pto.Aysen'},
    {'id': '249', 'nombre': 'Juzgado de Letras y Gar.de Chile Chico'},
    {'id': '250', 'nombre': 'Juzgado de Letras y Gar.de Cochrane'},
    {'id': '996', 'nombre': 'Juzgado de Letras y Gar.de Puerto Cisnes'},
    {'id': '253', 'nombre': '1º Juzgado de Letras de Punta Arenas'},
    {'id': '254', 'nombre': '2º Juzgado de Letras de Punta Arenas'},
    {'id': '255', 'nombre': '3º Juzgado de Letras de Punta Arenas'},
    {'id': '257', 'nombre': 'Juzgado de Letras y Gar. de Puerto Natales'},
    {'id': '258', 'nombre': 'Juzgado de Letras y Gar.de Porvenir'},
    {'id': '1502', 'nombre': 'Juzgado de Letras y Garantía de Cabo de Hornos'},
    {'id': '259', 'nombre': '1º Juzgado Civil de Santiago'},
    {'id': '260', 'nombre': '2º Juzgado Civil de Santiago'},
    {'id': '261', 'nombre': '3º Juzgado Civil de Santiago'},
    {'id': '262', 'nombre': '4º Juzgado Civil de Santiago'},
    {'id': '263', 'nombre': '5º Juzgado Civil de Santiago'},
    {'id': '264', 'nombre': '6º Juzgado Civil de Santiago'},
    {'id': '265', 'nombre': '7º Juzgado Civil de Santiago'},
    {'id': '266', 'nombre': '8º Juzgado Civil de Santiago'},
    {'id': '267', 'nombre': '9º Juzgado Civil de Santiago'},
    {'id': '268', 'nombre': '10º Juzgado Civil de Santiago'},
    {'id': '269', 'nombre': '11º Juzgado Civil de Santiago'},
    {'id': '270', 'nombre': '12º Juzgado Civil de Santiago'},
    {'id': '271', 'nombre': '13º Juzgado Civil de Santiago'},
    {'id': '272', 'nombre': '14º Juzgado Civil de Santiago'},
    {'id': '273', 'nombre': '15º Juzgado Civil de Santiago'},
    {'id': '274', 'nombre': '16º Juzgado Civil de Santiago'},
    {'id': '275', 'nombre': '17º Juzgado Civil de Santiago'},
    {'id': '276', 'nombre': '18º Juzgado Civil de Santiago'},
    {'id': '277', 'nombre': '19º Juzgado Civil de Santiago'},
    {'id': '278', 'nombre': '20º Juzgado Civil de Santiago'},
    {'id': '279', 'nombre': '21º Juzgado Civil de Santiago'},
    {'id': '280', 'nombre': '22º Juzgado Civil de Santiago'},
    {'id': '281', 'nombre': '23º Juzgado Civil de Santiago'},
    {'id': '282', 'nombre': '24º Juzgado Civil de Santiago'},
    {'id': '283', 'nombre': '25º Juzgado Civil de Santiago'},
    {'id': '284', 'nombre': '26º Juzgado Civil de Santiago'},
    {'id': '285', 'nombre': '27º Juzgado Civil de Santiago'},
    {'id': '286', 'nombre': '28º Juzgado Civil de Santiago'},
    {'id': '287', 'nombre': '29º Juzgado Civil de Santiago'},
    {'id': '288', 'nombre': '30º Juzgado Civil de Santiago'},
    {'id': '387', 'nombre': 'Juzgado de Letras de Colina'},
    {'id': '343', 'nombre': '1º Juzgado Civil de San Miguel'},
    {'id': '344', 'nombre': '2º Juzgado Civil de San Miguel'},
    {'id': '345', 'nombre': '3º Juzgado Civil de San Miguel'},
    {'id': '390', 'nombre': '4º Juzgado Civil de San Miguel'},
    {'id': '364', 'nombre': '1º Juzgado Civil de Puente Alto'},
    {'id': '373', 'nombre': '1º Juzgado De Letras De Talagante'},
    {'id': '374', 'nombre': '2º Juzgado De Letras De Talagante'},
    {'id': '375', 'nombre': '1º Juzgado de Letras de Melipilla'},
    {'id': '377', 'nombre': '1º Juzgado de Letras de Buin'},
    {'id': '378', 'nombre': '2º Juzgado de Letras de Buin'},
    {'id': '388', 'nombre': 'Juzgado de Letras de Peñaflor'},
    {'id': '400', 'nombre': '1º Juzgado de Letras de San Bernardo'},
    {'id': '1402', 'nombre': '1º Juzgado de Letras de San Bernardo Ex 3°'},
    {'id': '401', 'nombre': '2º Juzgado de Letras de San Bernardo'},
    {'id': '1403', 'nombre': '2º Juzgado de Letras de San Bernardo Ex 3°'},
]

COMPETENCIAS_CONFIG = {
    "Civil": {
        "value": "3", "selector_id": "fecTribunal", "items": TRIBUNALES_CIVIL,
        "item_key_id": "tribunal_id", "item_key_nombre": "tribunal_nombre"
    }
}

# --- FIN: Configuración Centralizada ---

def generar_tareas(start_date_str, end_date_str, es_tribunal=False):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date
    tareas = []

    incremento = timedelta(days=7) if es_tribunal else timedelta(days=1)

    while current_date <= end_date:
        fecha_inicio_web = current_date.strftime('%d/%m/%Y')
        fecha_id_base = current_date.strftime('%Y-%m-%d')
        
        # Determinar el fin del rango
        if es_tribunal:
            fin_rango = min(current_date + timedelta(days=6), end_date)
            fecha_fin_web = fin_rango.strftime('%d/%m/%Y')
        else:
            fecha_fin_web = fecha_inicio_web

        for comp_nombre, comp_data in COMPETENCIAS_CONFIG.items():
            for item in comp_data["items"]:
                tarea_id = f"{comp_nombre.lower()}_{fecha_id_base}_{item['id']}"
                tarea = {
                    'id': tarea_id, 'ruta_salida': RUTA_SALIDA,
                    'fecha_desde': fecha_inicio_web, 'fecha_hasta': fecha_fin_web,
                    'competencia_nombre': comp_nombre, 'competencia_value': comp_data['value'],
                    'selector_id': comp_data['selector_id'],
                    comp_data["item_key_id"]: item['id'], comp_data["item_key_nombre"]: item['nombre']
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
    parser = argparse.ArgumentParser(description="Orquestador de scraping judicial solo para competencia Civil.")
    parser.add_argument('--modo', choices=['diario', 'historico'], default='historico')
    parser.add_argument('--desde', default="2024-01-01")
    parser.add_argument('--hasta', default="2024-01-31")
    parser.add_argument('--procesos', type=int, default=4, help="Número MÁXIMO de procesos concurrentes.")
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--tanda_size', type=int, default=2, help="Cuántos procesos iniciar a la vez.")
    parser.add_argument('--delay_tanda', type=int, default=90, help="Segundos de espera entre el inicio de cada tanda.")
    args = parser.parse_args()

    es_modulo_tribunal = 'tribunales' in NOMBRE_MODULO
    tasks = generar_tareas(args.desde, args.hasta, es_tribunal=es_modulo_tribunal) if args.modo == 'historico' else []

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