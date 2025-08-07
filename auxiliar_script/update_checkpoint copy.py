import os
import json
import re
from typing import Dict, Set

def extract_dates_from_csv_files(csv_directory: str) -> Set[str]:
    """
    Extrae todas las fechas únicas en formato YYYY-MM-DD de los nombres de archivos CSV.
    
    Args:
        csv_directory (str): Ruta del directorio que contiene los archivos CSV
        
    Returns:
        Set[str]: Conjunto de fechas únicas encontradas
    """
    dates = set()
    
    # Patrón regex para encontrar fechas en formato YYYY-MM-DD
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    
    try:
        # Iterar sobre todos los archivos en el directorio
        for filename in os.listdir(csv_directory):
            if filename.endswith('.csv'):
                # Buscar la primera ocurrencia de una fecha en el nombre del archivo
                match = re.search(date_pattern, filename)
                if match:
                    dates.add(match.group())
                    
    except FileNotFoundError:
        print(f"Error: El directorio {csv_directory} no existe.")
        return set()
    except Exception as e:
        print(f"Error al leer el directorio {csv_directory}: {e}")
        return set()
    
    return dates

def load_checkpoint_json(checkpoint_path: str) -> Dict:
    """
    Carga el archivo JSON de checkpoint. Si no existe o está corrupto, retorna un diccionario vacío.
    
    Args:
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
        
    Returns:
        Dict: Contenido del archivo JSON o diccionario vacío
    """
    try:
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    print(f"El archivo {checkpoint_path} está vacío. Inicializando como objeto vacío.")
                    return {}
        else:
            print(f"El archivo {checkpoint_path} no existe. Inicializando como objeto vacío.")
            return {}
    except json.JSONDecodeError:
        print(f"Error: El archivo {checkpoint_path} contiene JSON inválido. Inicializando como objeto vacío.")
        return {}
    except Exception as e:
        print(f"Error al leer el archivo {checkpoint_path}: {e}")
        return {}

def update_checkpoint_json(checkpoint_data: Dict, dates: Set[str]) -> Dict:
    """
    Actualiza el diccionario de checkpoint con las nuevas fechas encontradas.
    
    Args:
        checkpoint_data (Dict): Datos actuales del checkpoint
        dates (Set[str]): Fechas encontradas en los archivos CSV
        
    Returns:
        Dict: Diccionario de checkpoint actualizado
    """
    updated = False
    
    for date in dates:
        if date not in checkpoint_data:
            checkpoint_data[date] = {
                "status": "completed",
                "last_page": 1
            }
            updated = True
            print(f"Agregada nueva fecha: {date}")
    
    if not updated:
        print("No se encontraron fechas nuevas para agregar.")
    
    return checkpoint_data

def save_checkpoint_json(checkpoint_path: str, checkpoint_data: Dict) -> bool:
    """
    Guarda el diccionario de checkpoint en el archivo JSON con formato legible.
    
    Args:
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
        checkpoint_data (Dict): Datos del checkpoint a guardar
        
    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    try:
        # Crear el directorio padre si no existe
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        with open(checkpoint_path, 'w', encoding='utf-8') as file:
            json.dump(checkpoint_data, file, indent=4, ensure_ascii=False)
        
        print(f"Archivo checkpoint guardado exitosamente: {checkpoint_path}")
        return True
        
    except Exception as e:
        print(f"Error al guardar el archivo {checkpoint_path}: {e}")
        return False

def main(csv_directory: str, checkpoint_path: str):
    """
    Función principal que ejecuta todo el proceso de actualización del checkpoint.
    
    Args:
        csv_directory (str): Ruta del directorio que contiene los archivos CSV
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
    """
    print("=== Iniciando actualización de checkpoint ===")
    print(f"Directorio CSV: {csv_directory}")
    print(f"Archivo checkpoint: {checkpoint_path}")
    print()
    
    # Paso 1: Extraer fechas de los archivos CSV
    print("1. Extrayendo fechas de archivos CSV...")
    dates = extract_dates_from_csv_files(csv_directory)
    
    if not dates:
        print("No se encontraron fechas en los archivos CSV.")
        return
    
    print(f"Fechas encontradas: {sorted(dates)}")
    print()
    
    # Paso 2: Cargar el archivo JSON de checkpoint
    print("2. Cargando archivo checkpoint...")
    checkpoint_data = load_checkpoint_json(checkpoint_path)
    print(f"Fechas existentes en checkpoint: {len(checkpoint_data)}")
    print()
    
    # Paso 3: Actualizar el checkpoint con las nuevas fechas
    print("3. Actualizando checkpoint...")
    updated_checkpoint = update_checkpoint_json(checkpoint_data, dates)
    print()
    
    # Paso 4: Guardar el archivo actualizado
    print("4. Guardando archivo checkpoint actualizado...")
    if save_checkpoint_json(checkpoint_path, updated_checkpoint):
        print("\n=== Proceso completado exitosamente ===")
        print(f"Total de fechas en checkpoint: {len(updated_checkpoint)}")
    else:
        print("\n=== Error al completar el proceso ===")

# Función de compatibilidad con la versión anterior
def update_checkpoint_from_csv_names():
    """
    Función de compatibilidad que mantiene la funcionalidad original.
    """
    CSV_DIR = r'C:\Users\uziel\Documents\pyscripts\Data\Chile\Judiciales_scrap\suprema\csvs'
    CHECKPOINT_FILE = r'C:\Users\uziel\Documents\pyscripts\Data\Chile\Judiciales_scrap\suprema\checkpoint.json'
    main(CSV_DIR, CHECKPOINT_FILE)

if __name__ == "__main__":
    # Rutas de ejemplo (puedes modificar estas rutas según tus necesidades)
    CSV_DIRECTORY = r"C:\Users\uziel\Documents\pyscripts\Data\Chile\Judiciales_scrap\suprema\csvs"
    CHECKPOINT_PATH = r"C:\Users\uziel\Documents\pyscripts\Data\Chile\Judiciales_scrap\suprema\checkpoint.json"
    
    # Ejecutar el proceso principal
    main(CSV_DIRECTORY, CHECKPOINT_PATH)