import pandas as pd
import glob
import os
import sys
import datetime
import re
import sqlalchemy
import sys
import datetime
import shutil
import logging
# ============================================================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ============================================================================


# Configurar el logger
log_filename = f"proceso_completo_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info(f"Iniciando proceso completo de consolidación y envío a BD - {datetime.datetime.now()}")

# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN A POSTGRES
# ============================================================================

PG_LDI_Username = 'adminPg'
PG_LDI_Password = 'M#M#%6jEHh3F3HJ%'
PG_LDI_Hostname = 'pgsv-dev-eastus-001.postgres.database.azure.com'
PG_LDI_Database = 'postgres'
engine_postgres = sqlalchemy.create_engine(f'postgresql://{PG_LDI_Username}:{PG_LDI_Password}@{PG_LDI_Hostname}/{PG_LDI_Database}')

# ============================================================================
# LISTAS DE FILTROS Y LIMPIEZA
# ============================================================================

# Lista de cargos a considerar (versión literal y case-sensitive)
cargo_list = [
    'DDO.',
    'AB.DDO.',
    'AP.DDO.',
    'DDO.SOL',
    'IMPUTAD.',
    'QDO.',
    'DDO.SUBSIDIARIO',
    'DNDO.',
    'AB.DDOR.',
    'DDOR.',
    'AP. DDOR.',
    'DDO. SOL.',
    'Apod.Dndo.',
    'AB.DDO.SOL.',
    'ABG.DNDO.',
    'AB.DDO',
    'AP.DDO',
    'DDO.SO',
    'DDO.SU',
    'REQDO.',
    'DDO.SOL.',
    'DDO.SOLID.',
    'DDO. SUB.',
    'AB.REQDO.',
    'AB.DDO.SUB.',
    'Defensor',
    'DDO.SUB.',
    'ABG.ACUSADO',
    'Abogado del Acusado',
    'ABG.DNDO',
    'AP.DND',
    'DNCDO.',
    'Denunciado.',
    'Querellado.',
    'Defensor.', 
    'Defensor privado.',
    'Defensor penal público'
]

# Lista de nombres a eliminar
nombre_list = [
    'TESTIGO', 'DENUNCIANTE', 'VICTIMA', 'NOT AL TELEFONO FORMA ESP', 'NOT EMAIL', 'NOT EMIAL', 'NOT IMP X FONO',
    'NOT IMPO X MAIL', 'NOT IMPUTADOCORREO ELECT', 'NOT MAIL IMPUTADO', 'NOT X IMPUTADO', 'NOT X FONO IMPUTADO',
    'NOT X MAIL IMPUTADA', 'NOT X MAIL IMPUTADO', 'NOT X MAIL IMP', 'NOT X MAIL IMPUTADA', 'NOTIFICA DOMICILIO DOS',
    'NOTIFICA DOMICILIO TRES', 'NOTIFICA DOMICILIO UNO', 'NOTIFICA MP', 'NOTIFICA MP QUERELLA', 'NOTIFICA PDI',
    'NOTIFICA QUERELLA', 'NOTIFICA QUERELLA MP', 'NOTIFICACION', 'NOTIFICACION MP', 'NOTIFICACION QUERELLA MP',
    'NOTIFICACION TELEFONICA IMPUTA', 'NOTIFICACIONES HOMECENTER', 'NOTIFICACIONES MP', 'NOTIFICACIONES PDI',
    'NOTIFICACIONES PDI FUNCIONARIO', 'DOMICILIO 1', 'DOMICILIO 2', 'DOMICILIO 3', 'DOMICILIO 4', 'DOMICILIO 5',
    'DOMICILIO 6', 'DOMICILIO DOS', 'DOMICILIO IMPUTADO', 'DOMICILIO N2', 'MAIL', 'NOT EMAIL', 'IMPUTADO',
    'MAIL IMPUTADA', 'NOT X', 'MAIL IMP', 'NOTIFICA DOMICILIO', 'DOM 2', 'DOM 13', 'CORREO IMPUTADA', 'IMP',
    'IMPUT', 'IMPUTADA', 'NN', 'CONFIDENCIAL', 'RESPONSABLES', 'NNN', 'N N N', 'N N', 'IMPUTADO', 'DOMICILIO 2 QUERELLADO'
]

# Lista de valores a limpiar de la columna 'denominacion'
nombre_list1 = [
    'DOM 1', 'DOM 2', 'DOM 3', 'DOM 4', 'DOM 5', 'DOM 6', 'DOM 7', 'DOM 8', 'DOM 9', 'DOM 10',
    'DOMICILIO 2', 'DOMICILIO 3', 'DOMICILIO 4', 'DOMICILIO 5', 'DOMICILIO 6', 'DOMICILIO 7',
    'DOMICILIO 8', 'DOMICILIO 9', 'DOMICILIO 10', 'DOMICILIO 1', 'DOMICILIO 1 IMPUTADO'
]

# ============================================================================
# FUNCIÓN DE LIMPIEZA (única función necesaria por repetirse en el proceso)
# ============================================================================

def limpiar_nombre(texto):
    """Limpia palabras no deseadas de la denominación"""
    if pd.isna(texto):
        return ''
    palabras = texto.split()
    palabras_filtradas = [p for p in palabras if p.upper() not in nombre_list1]
    return ' '.join(palabras_filtradas)

# Lista de estados de causa a conservar
estados_validos = [
    'Fallada',
    'Fallada-Impugnada',
    'Fallada o Concluida',
    'Fallada-Terminada',
    'Concluido',
    'Concluida.',
    'En Tramitación',
    'Tramitación',
    'Tramitación.',
    'Trámite en Sala',
    'En Acuerdo',
    'Medida Mejor Resolver',
    'Elev. Excma. Corte Suprema',
    'Deja Sin Efecto',
    'Cumplimiento',
    'Terminada Masiva'
]

def extraer_estado_causa(row):
    """Extrae el estado de la causa desde la columna de observaciones."""
    observaciones = row.get('observaciones', '')
    institucion = row.get('institucion', '')
    
    if not isinstance(observaciones, str):
        return None

    try:
        if institucion == 'Corte Suprema':
            if 'Estado: ' in observaciones:
                return observaciones.split('Estado: ')[1].strip()
        else:
            if 'Estado Causa: ' in observaciones:
                parte = observaciones.split('Estado Causa: ')[1]
                return parte.split('|')[0].strip()
    except IndexError:
        return None
    
    return None

# ============================================================================
# PASO 1: BUSCAR Y CARGAR ARCHIVOS CSV
# ============================================================================

print("\n=== PASO 1: CARGA DE ARCHIVOS CSV ===")
base_path = r'C:\Worldsys\Scrap-Poder-Judicial-CL\Resultados_Globales'
pattern = os.path.join(base_path, '**', '*.csv')
archivos = glob.glob(pattern, recursive=True)
print(f'Archivos encontrados: {len(archivos)}')
print(f'Buscando en: {base_path}')
for archivo in archivos:
    print(f'  - {archivo}')

# ============================================================================
# PASO 2: LEER Y CONCATENAR TODOS LOS ARCHIVOS
# ============================================================================

print("\n=== PASO 2: LECTURA Y CONCATENACIÓN ===")
dfs = []
for archivo in archivos:
    df_temp = pd.read_csv(archivo, sep=';', dtype=str)
    print(f'Procesando: {os.path.basename(archivo)} - Registros: {len(df_temp)}')
    
    # Normalizar nombres de columnas
    df_temp.columns = [col.lower().strip() for col in df_temp.columns]
    
    # Verificar y renombrar columnas si es necesario
    if 'denominacion' not in df_temp.columns:
        if 'nombre' in df_temp.columns:
            df_temp = df_temp.rename(columns={'nombre': 'denominacion'})
        else:
            print(f"Advertencia: El archivo {archivo} no tiene columna 'denominacion' ni 'nombre'. Se omite.")
            continue
    
    dfs.append(df_temp)

if not dfs:
    raise ValueError("No se encontraron archivos válidos con columna 'denominacion' o 'nombre'.")

# Concatenar todos los DataFrames
df = pd.concat(dfs, ignore_index=True)
print(f'Registros totales cargados: {len(df)}')
print(f'Columnas disponibles: {df.columns.tolist()}')

# ============================================================================
# PASO 3: APLICAR FILTROS Y LIMPIEZA
# ============================================================================

print("\n=== PASO 3: APLICACIÓN DE FILTROS ===")
print(f'Registros iniciales: {len(df)}')

# Initialize df_filtrado with the full DataFrame before applying filters
df_filtrado = df.copy()

# Filtrar por cargo_list
if 'cargo' in df_filtrado.columns:
    # Guardar los cargos que se van a excluir
    cargos_excluidos_df = df_filtrado[~df_filtrado['cargo'].str.upper().isin(cargo_list)]
    cargos_unicos_excluidos = cargos_excluidos_df['cargo'].unique()
    
    with open('cargos_excluidos.txt', 'w', encoding='utf-8') as f:
        for cargo in cargos_unicos_excluidos:
            f.write(f"{cargo}\n")
    logging.info(f"Se han guardado {len(cargos_unicos_excluidos)} cargos únicos excluidos en 'cargos_excluidos.txt'.")

    # Aplicar el filtro
    df_filtrado = df_filtrado[df_filtrado['cargo'].str.upper().isin(cargo_list)]
    print(f'Tras filtro de cargo: {len(df_filtrado)}')
else:
    logging.warning("La columna 'cargo' no se encuentra en el DataFrame, no se aplicará el filtro por cargo.")

# Eliminar filas con nombres no deseados
df_filtrado = df_filtrado[~df_filtrado['denominacion'].str.startswith(tuple(nombre_list), na=False)]
print(f'Tras filtro de nombres: {len(df_filtrado)}')

# Eliminar denominaciones muy cortas
df_filtrado = df_filtrado[df_filtrado['denominacion'].str.len() > 3]
print(f'Tras filtro de longitud: {len(df_filtrado)}')

# Limpiar valores de la columna 'denominacion'
df_filtrado['denominacion'] = df_filtrado['denominacion'].apply(limpiar_nombre)

# Eliminar filas vacías en 'denominacion'
df_filtrado = df_filtrado[df_filtrado['denominacion'].notna() & (df_filtrado['denominacion'] != '')]
print(f'Tras limpiar vacíos: {len(df_filtrado)}')

# Eliminar registros con RUT inválido
if 'documento' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['documento'] != '0-0']
    print(f'Tras eliminar RUT 0-0: {len(df_filtrado)}')
else:
    print("Advertencia: Columna 'documento' no encontrada. Se omite el filtro de RUT.")
print(f'Tras eliminar RUT 0-0: {len(df_filtrado)}')

# --- Lógica para eliminar duplicados por fecha de causa ---
print("\n--- Eliminando duplicados por fecha de causa ---")

# Función para extraer la fecha de la causa de las observaciones
def extraer_fecha_causa(obs):
    if not isinstance(obs, str):
        return None
    # Buscar patrones 'Fecha Ingreso: DD/MM/YYYY', 'Fecha: DD/MM/YYYY' o 'Ingreso: DD/MM/YYYY'
    match = re.search(r'(?:Fecha Ingreso:|Fecha:|Ingreso:)\s*(\d{2}/\d{2}/\d{4})', obs)
    if match:
        return pd.to_datetime(match.group(1), format='%d/%m/%Y', errors='coerce')
    return None

df_filtrado['fecha_causa'] = df_filtrado['observaciones'].apply(extraer_fecha_causa)

# Extraer ROL, RIT, RUC de las observaciones
def extraer_identificador(obs):
    if not isinstance(obs, str):
        return None, None, None
    rol = re.search(r'Rol: (\S+)', obs)
    rit = re.search(r'RIT: (\S+)', obs)
    ruc = re.search(r'RUC: (\S+)', obs)
    return rol.group(1) if rol else None, rit.group(1) if rit else None, ruc.group(1) if ruc else None

df_filtrado[['rol', 'rit', 'ruc']] = df_filtrado['observaciones'].apply(lambda x: pd.Series(extraer_identificador(x)))

# Definir la clave para identificar duplicados
columnas_clave = ['rol', 'rit', 'ruc', 'denominacion']
if 'documento' in df_filtrado.columns:
    columnas_clave.append('documento')

# Rellenar NaT en fecha_causa con una fecha muy antigua para que no sean descartados si son únicos
fecha_minima = pd.Timestamp('1900-01-01')
df_filtrado['fecha_causa'] = df_filtrado['fecha_causa'].fillna(fecha_minima)

# Ordenar por fecha de causa (más reciente primero) y luego eliminar duplicados
df_filtrado = df_filtrado.sort_values(by='fecha_causa', ascending=False)
df_filtrado = df_filtrado.drop_duplicates(subset=columnas_clave, keep='first')

# Opcional: volver a poner NaT donde estaba la fecha mínima para no guardar fechas incorrectas
df_filtrado.loc[df_filtrado['fecha_causa'] == fecha_minima, 'fecha_causa'] = pd.NaT

print(f'Tras eliminar duplicados por fecha de causa: {len(df_filtrado)}')


print("\n--- Filtrado por Estado de Causa ---")
# Aplicar la función para crear la nueva columna 'estado_causa'
df_filtrado['estado_causa'] = df_filtrado.apply(extraer_estado_causa, axis=1)

# Filtrar para mantener solo los estados válidos
df_filtrado = df_filtrado[df_filtrado['estado_causa'].isin(estados_validos)]
print(f'Tras filtro por estado de causa: {len(df_filtrado)}')


# ============================================================================
# PASO 4: EXTRAER FECHA DE INGRESO
# ============================================================================

print("\n=== PASO 4: EXTRACCIÓN DE FECHAS ===")

# Extraer fecha de ingreso desde observaciones usando regex
patron_fecha = r'(?:Fecha Ingreso:|Fecha:|Ingreso:)\s*(\d{2}/\d{2}/\d{4})'
df_filtrado['fecha_ingreso'] = df_filtrado['observaciones'].str.extract(patron_fecha, expand=False)

# Mostrar distribución de fechas
distribucion_fechas = df_filtrado['fecha_ingreso'].value_counts().sort_index()
print(f'Fechas extraídas: {len(distribucion_fechas)} fechas únicas')
print('Primeras 10 fechas con más registros:')
print(distribucion_fechas.head(10))

# ============================================================================
# PASO 5: PREPARAR DATOS PARA BASE DE DATOS
# ============================================================================

print("\n=== PASO 5: PREPARACIÓN PARA BD ===")

# Mapear columnas al formato requerido por la tabla de destino
df_final = pd.DataFrame({
    'cargo': df_filtrado.get('cargo', ''),
    'denominacion': df_filtrado.get('denominacion', ''),
    'observaciones': df_filtrado.get('observaciones', ''),
    'fuente': 'Oficina del Poder Judicial',  # Valor fijo
    'ruc': df_filtrado['documento'] if 'documento' in df_filtrado.columns else '',
    'tribunal': df_filtrado.get('institucion', '')
})

# Eliminar duplicados finales
df_final = df_final.drop_duplicates()
print(f'Registros finales para envío: {len(df_final)}')

# ===========================================================================
# PASO 7: ENVÍO A POSTGRES
# ============================================================================

print("\n=== PASO 7: ENVÍO A POSTGRES ===")
try:
    df_final.to_sql('causas_judiciales', schema='chile', con=engine_postgres, if_exists='append', index=False)
    print(f"✓ Datos enviados exitosamente a Postgres: {len(df_final)} registros")
    print(f"✓ Tabla destino: chile.causas_judiciales")
    
    # ============================================================================
    # PASO 8: MOVER ARCHIVOS PROCESADOS
    # ============================================================================
    
    print("\n=== PASO 8: MOVIENDO ARCHIVOS PROCESADOS ===")
    carpeta_destino = r'C:\Worldsys\Scrap-Poder-Judicial-CL\Resultados_enviados_bd'
    
    # Crear carpeta destino si no existe
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"✓ Carpeta destino creada: {carpeta_destino}")
    
    archivos_movidos = 0
    for archivo in archivos:
        try:
            nombre_archivo = os.path.basename(archivo)
            destino_archivo = os.path.join(carpeta_destino, nombre_archivo)
            
            # Si ya existe un archivo con el mismo nombre, agregar timestamp
            if os.path.exists(destino_archivo):
                nombre_base, extension = os.path.splitext(nombre_archivo)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f"{nombre_base}_{timestamp}{extension}"
                destino_archivo = os.path.join(carpeta_destino, nombre_archivo)
            
            shutil.move(archivo, destino_archivo)
            print(f"✓ Movido: {os.path.basename(archivo)} -> {carpeta_destino}")
            archivos_movidos += 1
        except Exception as e:
            print(f"✗ Error al mover {archivo}: {str(e)}")
    
    print(f"✓ Archivos movidos exitosamente: {archivos_movidos}/{len(archivos)}")
    
except Exception as e:
    print(f"✗ Error al enviar datos a Postgres: {str(e)}")
    print("✗ Los archivos NO se moverán debido al error en el envío a BD")

# ============================================================================
# FINALIZACIÓN Y LIMPIEZA
# ============================================================================

print(f"\n=== PROCESO COMPLETADO - {datetime.datetime.now()} ===")
print(f"Resumen final:")
print(f"- Archivos procesados: {len(archivos)}")
print(f"- Registros iniciales: {len(df) if 'df' in locals() else 0}")
print(f"- Registros finales: {len(df_final)}")
print(f"- Archivos movidos a carpeta de enviados: {archivos_movidos if 'archivos_movidos' in locals() else 0}")



print(f"\n✓ Proceso completo finalizado. Log guardado en: {log_filename}")
print(f"✓ Datos enviados a base de datos PostgreSQL")