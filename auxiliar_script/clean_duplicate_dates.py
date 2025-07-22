import os
import json
from typing import Dict, List, Tuple
from collections import Counter

def load_checkpoint_json(checkpoint_path: str) -> Dict:
    """
    Carga el archivo JSON de checkpoint.
    
    Args:
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
        
    Returns:
        Dict: Contenido del archivo JSON o diccionario vacío si hay error
    """
    try:
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    print(f"El archivo {checkpoint_path} está vacío.")
                    return {}
        else:
            print(f"El archivo {checkpoint_path} no existe.")
            return {}
    except json.JSONDecodeError as e:
        print(f"Error: El archivo {checkpoint_path} contiene JSON inválido: {e}")
        return {}
    except Exception as e:
        print(f"Error al leer el archivo {checkpoint_path}: {e}")
        return {}

def find_duplicate_dates(checkpoint_data: Dict) -> Tuple[List[str], Dict[str, int]]:
    """
    Encuentra fechas duplicadas en el checkpoint.
    
    Args:
        checkpoint_data (Dict): Datos del checkpoint
        
    Returns:
        Tuple[List[str], Dict[str, int]]: Lista de fechas duplicadas y contador de ocurrencias
    """
    # Contar ocurrencias de cada fecha
    date_counter = Counter(checkpoint_data.keys())
    
    # Encontrar fechas que aparecen más de una vez
    duplicates = [date for date, count in date_counter.items() if count > 1]
    
    return duplicates, dict(date_counter)

def find_invalid_dates(checkpoint_data: Dict) -> List[str]:
    """
    Encuentra fechas con formato inválido.
    
    Args:
        checkpoint_data (Dict): Datos del checkpoint
        
    Returns:
        List[str]: Lista de fechas con formato inválido
    """
    import re
    
    # Patrón para fecha válida YYYY-MM-DD
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    invalid_dates = []
    
    for date in checkpoint_data.keys():
        if not date_pattern.match(date):
            invalid_dates.append(date)
        else:
            # Verificar que sea una fecha válida
            try:
                from datetime import datetime
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                invalid_dates.append(date)
    
    return invalid_dates

def optimize_checkpoint(checkpoint_data: Dict) -> Tuple[Dict, List[str]]:
    """
    Optimiza el checkpoint eliminando entradas inválidas y ordenando por fecha.
    
    Args:
        checkpoint_data (Dict): Datos del checkpoint original
        
    Returns:
        Tuple[Dict, List[str]]: Checkpoint optimizado y lista de problemas encontrados
    """
    issues = []
    clean_data = {}
    
    # Encontrar fechas inválidas
    invalid_dates = find_invalid_dates(checkpoint_data)
    
    for date, data in checkpoint_data.items():
        # Saltar fechas inválidas
        if date in invalid_dates:
            issues.append(f"Fecha inválida eliminada: {date}")
            continue
        
        # Verificar estructura de datos
        if not isinstance(data, dict):
            issues.append(f"Datos inválidos para fecha {date}: no es un diccionario")
            continue
        
        # Verificar campos requeridos y corregir si es necesario
        corrected_data = {}
        
        # Campo status
        if 'status' in data:
            corrected_data['status'] = data['status']
        else:
            corrected_data['status'] = 'completed'
            issues.append(f"Campo 'status' faltante en {date}, asignado 'completed'")
        
        # Campo last_page
        if 'last_page' in data:
            try:
                corrected_data['last_page'] = int(data['last_page'])
            except (ValueError, TypeError):
                corrected_data['last_page'] = 1
                issues.append(f"Campo 'last_page' inválido en {date}, asignado 1")
        else:
            corrected_data['last_page'] = 1
            issues.append(f"Campo 'last_page' faltante en {date}, asignado 1")
        
        clean_data[date] = corrected_data
    
    # Ordenar por fecha
    sorted_data = dict(sorted(clean_data.items()))
    
    return sorted_data, issues

def remove_duplicate_dates(checkpoint_data: Dict) -> Tuple[Dict, int]:
    """
    Elimina fechas duplicadas del checkpoint, manteniendo solo la primera ocurrencia.
    
    Args:
        checkpoint_data (Dict): Datos del checkpoint original
        
    Returns:
        Tuple[Dict, int]: Checkpoint limpio y número de duplicados eliminados
    """
    # Como los diccionarios en Python 3.7+ mantienen el orden de inserción,
    # simplemente crear un nuevo diccionario eliminará automáticamente los duplicados
    original_count = len(checkpoint_data)
    
    # Crear un nuevo diccionario sin duplicados
    clean_checkpoint = {}
    duplicates_removed = 0
    
    for date, data in checkpoint_data.items():
        if date not in clean_checkpoint:
            clean_checkpoint[date] = data
        else:
            duplicates_removed += 1
            print(f"Fecha duplicada eliminada: {date}")
    
    return clean_checkpoint, duplicates_removed

def save_checkpoint_json(checkpoint_path: str, checkpoint_data: Dict, backup: bool = True) -> bool:
    """
    Guarda el diccionario de checkpoint en el archivo JSON con formato legible.
    
    Args:
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
        checkpoint_data (Dict): Datos del checkpoint a guardar
        backup (bool): Si crear una copia de seguridad del archivo original
        
    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    try:
        # Crear copia de seguridad si se solicita
        if backup and os.path.exists(checkpoint_path):
            backup_path = checkpoint_path + '.backup'
            import shutil
            shutil.copy2(checkpoint_path, backup_path)
            print(f"Copia de seguridad creada: {backup_path}")
        
        # Crear el directorio padre si no existe
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        with open(checkpoint_path, 'w', encoding='utf-8') as file:
            json.dump(checkpoint_data, file, indent=4, ensure_ascii=False, sort_keys=True)
        
        print(f"Archivo checkpoint limpio guardado: {checkpoint_path}")
        return True
        
    except Exception as e:
        print(f"Error al guardar el archivo {checkpoint_path}: {e}")
        return False

def analyze_checkpoint_structure(checkpoint_data: Dict) -> Dict:
    """
    Analiza la estructura del checkpoint para detectar inconsistencias.
    
    Args:
        checkpoint_data (Dict): Datos del checkpoint
        
    Returns:
        Dict: Análisis de la estructura
    """
    analysis = {
        'total_dates': len(checkpoint_data),
        'status_distribution': {},
        'last_page_distribution': {},
        'invalid_entries': []
    }
    
    for date, data in checkpoint_data.items():
        # Verificar estructura de la fecha
        if not isinstance(data, dict):
            analysis['invalid_entries'].append(f"Fecha {date}: datos no son un diccionario")
            continue
            
        # Analizar status
        status = data.get('status', 'missing')
        analysis['status_distribution'][status] = analysis['status_distribution'].get(status, 0) + 1
        
        # Analizar last_page
        last_page = data.get('last_page', 'missing')
        analysis['last_page_distribution'][str(last_page)] = analysis['last_page_distribution'].get(str(last_page), 0) + 1
        
        # Verificar campos requeridos
        if 'status' not in data or 'last_page' not in data:
            analysis['invalid_entries'].append(f"Fecha {date}: faltan campos requeridos")
    
    return analysis

def main(checkpoint_path: str, create_backup: bool = True, analyze_only: bool = False, optimize: bool = False):
    """
    Función principal que ejecuta la limpieza de fechas duplicadas.
    
    Args:
        checkpoint_path (str): Ruta del archivo JSON de checkpoint
        create_backup (bool): Si crear una copia de seguridad
        analyze_only (bool): Si solo analizar sin modificar el archivo
        optimize (bool): Si optimizar el archivo (ordenar, corregir formato, etc.)
    """
    print("=== Limpieza y Optimización de Checkpoint ===")
    print(f"Archivo: {checkpoint_path}")
    print(f"Crear backup: {create_backup}")
    print(f"Solo análisis: {analyze_only}")
    print(f"Optimizar: {optimize}")
    print()
    
    # Paso 1: Cargar el archivo JSON
    print("1. Cargando archivo checkpoint...")
    checkpoint_data = load_checkpoint_json(checkpoint_path)
    
    if not checkpoint_data:
        print("No se pudo cargar el archivo o está vacío.")
        return
    
    print(f"Fechas cargadas: {len(checkpoint_data)}")
    print()
    
    # Paso 2: Analizar estructura
    print("2. Analizando estructura del checkpoint...")
    analysis = analyze_checkpoint_structure(checkpoint_data)
    
    print(f"Total de fechas: {analysis['total_dates']}")
    print(f"Distribución de status: {analysis['status_distribution']}")
    print(f"Distribución de last_page: {analysis['last_page_distribution']}")
    
    if analysis['invalid_entries']:
        print(f"Entradas inválidas encontradas: {len(analysis['invalid_entries'])}")
        for entry in analysis['invalid_entries'][:5]:  # Mostrar solo las primeras 5
            print(f"  - {entry}")
        if len(analysis['invalid_entries']) > 5:
            print(f"  ... y {len(analysis['invalid_entries']) - 5} más")
    print()
    
    # Paso 3: Buscar duplicados
    print("3. Buscando fechas duplicadas...")
    duplicates, date_counter = find_duplicate_dates(checkpoint_data)
    
    if duplicates:
        print(f"Fechas duplicadas encontradas: {len(duplicates)}")
        for dup in duplicates[:10]:  # Mostrar solo las primeras 10
            print(f"  - {dup}: {date_counter[dup]} ocurrencias")
        if len(duplicates) > 10:
            print(f"  ... y {len(duplicates) - 10} más")
    else:
        print("No se encontraron fechas duplicadas.")
    print()
    
    # Paso 4: Buscar fechas inválidas
    print("4. Verificando formato de fechas...")
    invalid_dates = find_invalid_dates(checkpoint_data)
    
    if invalid_dates:
        print(f"Fechas con formato inválido encontradas: {len(invalid_dates)}")
        for inv_date in invalid_dates[:10]:  # Mostrar solo las primeras 10
            print(f"  - {inv_date}")
        if len(invalid_dates) > 10:
            print(f"  ... y {len(invalid_dates) - 10} más")
    else:
        print("Todas las fechas tienen formato válido.")
    print()
    
    if analyze_only:
        print("=== Análisis completado (no se realizaron cambios) ===")
        return
    
    # Determinar si necesita limpieza
    needs_cleaning = len(duplicates) > 0 or len(invalid_dates) > 0 or optimize
    
    if not needs_cleaning:
        print("El archivo no necesita limpieza.")
        return
    
    # Paso 5: Procesar archivo
    print("5. Procesando archivo...")
    
    if optimize:
        print("  - Optimizando estructura...")
        clean_checkpoint, optimization_issues = optimize_checkpoint(checkpoint_data)
        
        if optimization_issues:
            print(f"  - Problemas corregidos: {len(optimization_issues)}")
            for issue in optimization_issues[:5]:
                print(f"    * {issue}")
            if len(optimization_issues) > 5:
                print(f"    * ... y {len(optimization_issues) - 5} más")
    else:
        # Solo eliminar duplicados
        clean_checkpoint, removed_count = remove_duplicate_dates(checkpoint_data)
        print(f"  - Fechas duplicadas eliminadas: {removed_count}")
    
    print(f"  - Fechas finales: {len(clean_checkpoint)}")
    print()
    
    # Paso 6: Guardar archivo limpio
    print("6. Guardando archivo limpio...")
    if save_checkpoint_json(checkpoint_path, clean_checkpoint, create_backup):
        print("\n=== Proceso completado exitosamente ===")
        print(f"Fechas originales: {len(checkpoint_data)}")
        print(f"Fechas después de limpieza: {len(clean_checkpoint)}")
        
        if duplicates:
            print(f"Duplicados eliminados: {len(duplicates)}")
        if invalid_dates:
            print(f"Fechas inválidas eliminadas: {len(invalid_dates)}")
        if optimize:
            print("Archivo optimizado y ordenado por fecha")
    else:
        print("\n=== Error al completar el proceso ===")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpia fechas duplicadas del archivo JSON de checkpoint')
    parser.add_argument('--file', '-f', 
                       default=r"C:\Users\uziel\Documents\pyscripts\Data\Chile\Judiciales_scrap\suprema\checkpoint.json",
                       help='Ruta del archivo JSON de checkpoint')
    parser.add_argument('--no-backup', action='store_true',
                       help='No crear copia de seguridad del archivo original')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Solo analizar el archivo sin realizar cambios')
    parser.add_argument('--optimize', action='store_true',
                       help='Optimizar el archivo (ordenar, corregir formato, etc.)')
    
    args = parser.parse_args()
    
    # Ejecutar el proceso principal
    main(args.file, not args.no_backup, args.analyze_only, args.optimize)