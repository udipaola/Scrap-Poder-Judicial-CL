# Plan de Acción

Este documento detalla el plan de acción para la reorganización del proyecto, incluyendo la estructura de directorios y la modificación de los archivos `main_*.py` y `worker_*.py` para adaptarse a la nueva configuración.

### **2. Plan de Ejecución Detallado**

Aplica las siguientes modificaciones de forma genérica para cada módulo, adaptando los nombres de archivo según corresponda.

#### **Paso 1: Modificar `main_*.py` (Plantilla Genérica)**

Este archivo orquesta las tareas y será el centro de la nueva configuración.

**Acción:** Reemplaza el contenido de cada `main_*.py` con la siguiente plantilla, asegurándote de rellenar las listas de `items` en `COMPETENCIAS_CONFIG` según corresponda para cada módulo.

```python
# Plantilla para main_*.py

import argparse
import multiprocessing
import json
import os
import time
from datetime import datetime, timedelta

# Asume que los workers y utils están en el mismo directorio
from worker import scrape_worker
from utils import forzar_cierre_navegadores # Y otras funciones de utils

# --- INICIO: Configuración Centralizada ---

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
NOMBRE_MODULO = os.path.basename(DIRECTORIO_ACTUAL)
RUTA_SALIDA = os.path.join(DIRECTORIO_ACTUAL, '..', 'Resultados_Globales')
os.makedirs(RUTA_SALIDA, exist_ok=True)
CHECKPOINT_FILE = os.path.join(RUTA_SALIDA, f"checkpoint_{NOMBRE_MODULO}.json")

# Define aquí las listas de items (Cortes/Tribunales) para este módulo.
# Ejemplo para un main_tribunales_civil.py
TRIBUNALES_CIVIL = [
    {'id': '2', 'nombre': '1º Juzgado de Letras de Arica'},
    # ... Rellenar lista completa para Civil ...
]
COMPETENCIAS_CONFIG = {
    "Civil": {
        "value": "3", "selector_id": "fecTribunal", "items": TRIBUNALES_CIVIL,
        "item_key_id": "tribunal_id", "item_key_nombre": "tribunal_nombre"
    }
}
# Nota: Cada main_*.py tendrá su propia y única COMPETENCIAS_CONFIG.

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

def main():
    # ... (Parser de argumentos sin cambios) ...
    
    es_modulo_tribunal = 'tribunales' in NOMBRE_MODULO
    tasks = generar_tareas(args.desde, args.hasta, es_tribunal=es_modulo_tribunal)
    
    # ... (El resto de la lógica de main, multiprocessing, etc., permanece igual)
    # Asegúrate de que no haya código de limpieza de perfiles aquí.

if __name__ == "__main__":
    # La limpieza de perfiles podría añadirse aquí si se desea
    multiprocessing.freeze_support()
    main() # Simplificado para que el bucle while no sea necesario si la lógica está bien contenida
```

#### **Paso 2: Modificar `worker_*.py` (Plantilla Genérica)**

El worker debe ser capaz de manejar tanto fechas únicas como rangos de fechas, y guardar los resultados en la ruta centralizada.

**Acción:** En cada directorio, abre el archivo `worker_*.py` y ajústalo para que coincida con esta plantilla.

```python
# Plantilla para worker_*.py

import os
# ... otras importaciones

def scrape_worker(task_info):
    task, lock, headless_mode, stop_event = task_info
    
    # 1. Extraer la ruta de salida y las fechas
    ruta_salida = task['ruta_salida']
    task_id = task['id']
    fecha_desde_str = task['fecha_desde']
    fecha_hasta_str = task['fecha_hasta']
    
    # ... (Lógica de desempaquetado de item_id, item_nombre, etc.)

    try:
        # ... (Configuración de Chrome y Selenium)
        
        # 2. Modificar la inserción de fechas para usar el rango
        try:
            # ... (Lógica de selección de competencia y tribunal/corte)
            
            input_desde = wait.until(EC.presence_of_element_located((By.ID, "fecDesde")))
            input_hasta = wait.until(EC.presence_of_element_located((By.ID, "fecHasta")))
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_desde_str}';", input_desde)
            driver.execute_script(f"arguments[0].removeAttribute('readonly'); arguments[0].value='{fecha_hasta_str}';", input_hasta)
            
            # ...
        except Exception as e:
            # ... (Manejo de errores)
            # 3. Guardar screenshot en la ruta centralizada
            screenshot_path = os.path.join(ruta_salida, f"error_screenshot_{task_id}.png")
            driver.save_screenshot(screenshot_path)
            # ...

        # ... (Lógica de scraping y paginación)

            # Dentro del bucle de guardado a CSV:
            # 4. Guardar CSV en la ruta centralizada
            nombre_archivo_csv = os.path.join(ruta_salida, f"resultados_{task_id}.csv")
            df_pagina.to_csv(nombre_archivo_csv, mode='a', #...)
            
    # ... (resto del script)
```