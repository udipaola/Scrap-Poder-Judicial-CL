import os
import json
from datetime import datetime, timedelta

def analizar_resultados_por_competencia(checkpoint_path, competencia, rango_completo):
    print(f'--- Analizando competencia: {competencia} ---')
    fechas_encontradas = set()

    if not os.path.exists(checkpoint_path):
        # Si el archivo no existe, lo creamos con una estructura vacía
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump({'completed_ranges': []}, f)
        print(f'Advertencia: No se encontró el archivo checkpoint en {checkpoint_path}. Se ha creado uno nuevo.')

    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            if not content.strip():
                print(f'Advertencia: El archivo checkpoint para {competencia} está vacío.')
                return

            checkpoint_data = json.loads(content)
            # Procesar fechas individuales (formato Corte_suprema)
            for key, value in checkpoint_data.items():
                if isinstance(value, dict) and value.get('status') == 'completed':
                    try:
                        # Intentar procesar como fecha individual
                        fecha = datetime.strptime(key, '%Y-%m-%d')
                        fechas_encontradas.add(fecha)
                        continue
                    except ValueError:
                        # Si no es una fecha individual, intentar procesar como rango
                        parts = key.split('_')
                        if len(parts) >= 4 and 'to' in parts:
                            try:
                                # Encontrar las partes de fecha en el string
                                date_parts = [p for p in parts if p[0].isdigit()]
                                if len(date_parts) >= 2:
                                    fecha_inicio_rango = datetime.strptime(date_parts[0], '%Y-%m-%d')
                                    fecha_fin_rango = datetime.strptime(date_parts[1], '%Y-%m-%d')
                                    delta = fecha_fin_rango - fecha_inicio_rango
                                    for i in range(delta.days + 1):
                                        fechas_encontradas.add(fecha_inicio_rango + timedelta(days=i))
                            except (ValueError, IndexError):
                                continue
        except json.JSONDecodeError:
            print(f'Error: El archivo checkpoint para {competencia} está mal formado.')
            return
        except Exception as e:
            print(f"Ocurrió un error inesperado al procesar {checkpoint_path}: {e}")
            return

    # Calcular días faltantes
    fechas_faltantes = sorted(list(rango_completo - fechas_encontradas))

    if not fechas_faltantes:
        print(f'¡Rango completo para la competencia {competencia}!')
    else:
        print(f'Se encontraron {len(fechas_faltantes)} días faltantes para la competencia {competencia}.')
        # Descomentar la siguiente línea para ver las fechas faltantes específicas
        # for fecha in fechas_faltantes:
        #     print(f'  - {fecha.strftime("%Y-%m-%d")}')
    print('\n')

def analizar_resultados():
    # Definir el rango de fechas
    fecha_inicio = datetime(2021, 1, 1)
    fecha_fin = datetime(2025, 7, 20)
    rango_completo = set(fecha_inicio + timedelta(days=x) for x in range((fecha_fin - fecha_inicio).days + 1))

    # Directorio base de las competencias
    directorio_base = 'C:\\Worldsys\\Scrap-Poder-Judicial-CL\\Resultados_Globales'

    competencias_map = {
        'Corte_suprema': ('Resultados_suprema', 'checkpoint_suprema.json'),
        'Corte_apelaciones': ('Resultados_apelaciones', 'checkpoint_apelaciones.json'),
        'tribunales_civil': ('Resultados_civil', 'checkpoint_tribunales_civil.json'),
        'tribunales_cobranza': ('Resultados_cobranza', 'checkpoint_tribunales_cobranza.json'),
        'tribunales_laboral': ('Resultados_laboral', 'checkpoint.json'),
        'tribunales_penal': ('Resultados_penal', 'checkpoint_tribunales_penal.json')
    }

    for competencia_nombre, (dir_competencia, checkpoint_file) in competencias_map.items():
        directorio_competencia_full = os.path.join(directorio_base, dir_competencia)
        checkpoint_path = os.path.join(directorio_competencia_full, checkpoint_file)
        
        analizar_resultados_por_competencia(checkpoint_path, competencia_nombre, rango_completo.copy())

if __name__ == '__main__':
    analizar_resultados()