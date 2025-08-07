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

# PASO 5.1: Detectar competencia desde el nombre del archivo
def detectar_competencia(nombre_archivo):
    """
    Detecta la competencia basándose en el nombre del archivo CSV.
    
    Patrones:
    - Apelaciones: resultados_YYYY-MM-DD_numero.csv
    - Civil: contiene 'civil'
    - Cobranza: contiene 'cobranza'
    - Penal: contiene 'penal'
    - Suprema: resultados_YYYY-MM-DD.csv (sin número al final)
    - Laboral: contiene 'laboral'
    """
    # Remover la extensión .csv para el análisis
    nombre_sin_ext = nombre_archivo.replace('.csv', '')
    
    competencia_patterns = {
        # Orden importante: suprema debe ir antes que apelaciones para evitar conflictos
        'suprema': r'^resultados_\d{4}-\d{2}-\d{2}$',
        'apelaciones': r'^resultados_\d{4}-\d{2}-\d{2}_\d+$',
        'civil': r'.*civil.*',
        'cobranza': r'.*cobranza.*',
        'penal': r'.*penal.*',
        'laboral': r'.*laboral.*'
    }
    
    for competencia, patron in competencia_patterns.items():
        if re.search(patron, nombre_sin_ext, re.IGNORECASE):
            logging.info(f"Archivo '{nombre_archivo}' detectado como competencia: {competencia}")
            return competencia
    
    logging.warning(f"Archivo '{nombre_archivo}' no coincide con ningún patrón conocido. Asignando competencia: 'general'")
    return 'general'

# ============================================================================
# PARSERS ESPECÍFICOS POR COMPETENCIA
# ============================================================================

def normalizar_fecha(fecha_str):
    """
    Normaliza fechas desde diferentes formatos a YYYY-MM-DD.
    Maneja formatos: DD/MM/YYYY, DD/MM/YY, YYYY-MM-DD
    Corrige años de 2 dígitos para evitar interpretación como 00XX
    """
    if pd.isna(fecha_str) or not fecha_str or fecha_str.strip() == '':
        return None
    
    fecha_str = str(fecha_str).strip()
    
    # Formato DD/MM/YYYY (4 dígitos de año)
    if re.match(r'\d{2}/\d{2}/\d{4}', fecha_str):
        try:
            # Verificar si el año está mal formateado (0023 -> 2023)
            partes = fecha_str.split('/')
            if len(partes) == 3:
                dia, mes, año = partes
                año_int = int(año)
                
                # Corregir años mal interpretados (0023 -> 2023, 0024 -> 2024, etc.)
                if 20 <= año_int <= 99:  # Años 0020-0099 -> 2020-2099
                    año_corregido = 2000 + año_int
                    fecha_corregida = f"{dia}/{mes}/{año_corregido}"
                    return pd.to_datetime(fecha_corregida, format='%d/%m/%Y').strftime('%Y-%m-%d')
                elif año_int < 20:  # Años 0000-0019 -> 2000-2019
                    año_corregido = 2000 + año_int
                    fecha_corregida = f"{dia}/{mes}/{año_corregido}"
                    return pd.to_datetime(fecha_corregida, format='%d/%m/%Y').strftime('%Y-%m-%d')
                else:
                    # Año normal (1900-2099)
                    return pd.to_datetime(fecha_str, format='%d/%m/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.warning(f"Error procesando fecha DD/MM/YYYY '{fecha_str}': {e}")
            pass
    
    # Formato YYYY-MM-DD (ya normalizado)
    if re.match(r'\d{4}-\d{2}-\d{2}', fecha_str):
        return fecha_str
    
    # Formato DD/MM/YY (2 dígitos de año)
    if re.match(r'\d{2}/\d{2}/\d{2}', fecha_str):
        try:
            partes = fecha_str.split('/')
            if len(partes) == 3:
                dia, mes, año = partes
                año_int = int(año)
                
                # Convertir años de 2 dígitos a 4 dígitos
                # Asumimos que 00-30 = 2000-2030, 31-99 = 1931-1999
                if año_int <= 30:
                    año_completo = 2000 + año_int
                else:
                    año_completo = 1900 + año_int
                
                fecha_completa = f"{dia}/{mes}/{año_completo}"
                return pd.to_datetime(fecha_completa, format='%d/%m/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.warning(f"Error procesando fecha DD/MM/YY '{fecha_str}': {e}")
            pass
    
    logging.warning(f"Formato de fecha no reconocido: {fecha_str}")
    return None

def parsear_observaciones_apelaciones(observaciones):
    """
    Parser para competencia Apelaciones.
    Formato: Rol: Protección-872-2021 | Corte: C.A. de Punta Arenas | Caratulado: ... | Fecha Ingreso: 05/06/2021 | Estado Causa: Fallada-Terminada | Fecha Ubicación: 22/10/2021 | Ubicación: Archivo
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    # Extraer campos usando regex
    patterns = {
        'rol': r'Rol:\s*([^|]+)',
        'tribunal': r'Corte:\s*([^|]+)',
        'caratulado': r'Caratulado:\s*([^|]+)',
        'fecha_ingreso': r'Fecha Ingreso:\s*([^|]+)',
        'estado_causa': r'Estado Causa:\s*([^|]+)',
        'fecha_ubicacion': r'Fecha Ubicación:\s*([^|]+)',
        'ubicacion': r'Ubicación:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo in ['fecha_ingreso', 'fecha_ubicacion']:
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    return datos

def parsear_observaciones_civil(observaciones):
    """
    Parser para competencia Civil.
    Formato: Rol: C-2414-2021 | Fecha: 30/09/2021 | Caratulado: PROMOTORA CMR FALABELLA S.A./PIZARRO | Tribunal: 3º Juzgado de Letras de Calama
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    patterns = {
        'rol': r'Rol:\s*([^|]+)',
        'fecha_ingreso': r'Fecha:\s*([^|]+)',
        'caratulado': r'Caratulado:\s*([^|]+)',
        'tribunal': r'Tribunal:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo == 'fecha_ingreso':
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    return datos

def parsear_observaciones_cobranza(observaciones):
    """
    Parser para competencia Cobranza.
    Formato complejo con múltiples campos duplicados
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    patterns = {
        'rit': r'RIT:\s*([^|]+)',
        'tribunal': r'Tribunal:\s*([^|]+)',
        'caratulado': r'Caratulado:\s*([^|]+)',
        'fecha_ingreso': r'Fecha Ingreso:\s*([^|]+)',
        'estado_causa': r'Estado Procesal:\s*([^|]+)',
        'ruc': r'RUC:\s*([^|]+)',
        'procedimiento': r'Proc\.:\s*([^|]+)',
        'forma_inicio': r'Forma Inicio\.:\s*([^|]+)',
        'etapa': r'Etapa:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo == 'fecha_ingreso':
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    # Buscar estado alternativo si no se encontró el principal
    if 'estado_causa' not in datos:
        match = re.search(r'Estado Proc\.:\s*([^|]+)', observaciones)
        if match:
            datos['estado_causa'] = match.group(1).strip()
    
    return datos

def parsear_observaciones_suprema(observaciones):
    """
    Parser para competencia Suprema.
    Formato: Rol: 9128-2024 | Recurso: (Crimen) Apelación Amparo | Ingreso: 02/03/2024 | Estado: Fallada
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    patterns = {
        'rol': r'Rol:\s*([^|]+)',
        'recurso': r'Recurso:\s*([^|]+)',
        'fecha_ingreso': r'Ingreso:\s*([^|]+)',
        'estado_causa': r'Estado:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo == 'fecha_ingreso':
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    return datos

def parsear_observaciones_penal(observaciones):
    """
    Parser para competencia Penal.
    Formato complejo con información duplicada
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    patterns = {
        'rit': r'RIT:\s*([^|]+)',
        'ruc': r'RUC:\s*([^|]+)',
        'tribunal': r'Tribunal:\s*([^|]+)',
        'caratulado': r'Caratulado:\s*([^|]+)',
        'fecha_ingreso': r'Fecha Ingreso:\s*([^|]+)',
        'estado_causa': r'Estado Causa:\s*([^|]+)',
        'etapa': r'Etapa:\s*([^|]+)',
        'forma_inicio': r'Forma Inicio:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo == 'fecha_ingreso':
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    # Buscar estado alternativo
    if 'estado_causa' not in datos:
        match = re.search(r'Estado Actual:\s*([^|]+)', observaciones)
        if match:
            datos['estado_causa'] = match.group(1).strip()
    
    return datos

def parsear_observaciones_laboral(observaciones):
    """
    Parser para competencia Laboral.
    Formato similar a cobranza pero con algunas diferencias
    """
    datos = {}
    if not isinstance(observaciones, str):
        return datos
    
    patterns = {
        'rit': r'RIT:\s*([^|]+)',
        'tribunal': r'Tribunal:\s*([^|]+)',
        'caratulado': r'Caratulado:\s*([^|]+)',
        'fecha_ingreso': r'Fecha Ingreso:\s*([^|]+)',
        'estado_causa': r'Estado Causa:\s*([^|]+)',
        'ruc': r'RUC:\s*([^|]+)',
        'procedimiento': r'Proc\.:\s*([^|]+)',
        'forma_inicio': r'Forma Inicio:\s*([^|]+)',
        'etapa': r'Etapa:\s*([^|]+)'
    }
    
    for campo, patron in patterns.items():
        match = re.search(patron, observaciones)
        if match:
            valor = match.group(1).strip()
            if campo == 'fecha_ingreso':
                datos[campo] = normalizar_fecha(valor)
            else:
                datos[campo] = valor
    
    # Buscar fecha alternativa
    if 'fecha_ingreso' not in datos:
        match = re.search(r'F\. Ing\.:\s*([^|]+)', observaciones)
        if match:
            datos['fecha_ingreso'] = normalizar_fecha(match.group(1).strip())
    
    # Buscar estado alternativo
    if 'estado_causa' not in datos:
        match = re.search(r'Estado Proc\.:\s*([^|]+)', observaciones)
        if match:
            datos['estado_causa'] = match.group(1).strip()
    
    return datos

def parsear_observaciones_por_competencia(observaciones, competencia):
    """
    Función coordinadora que llama al parser específico según la competencia.
    """
    parsers = {
        'apelaciones': parsear_observaciones_apelaciones,
        'civil': parsear_observaciones_civil,
        'cobranza': parsear_observaciones_cobranza,
        'suprema': parsear_observaciones_suprema,
        'penal': parsear_observaciones_penal,
        'laboral': parsear_observaciones_laboral
    }
    
    parser = parsers.get(competencia)
    if parser:
        return parser(observaciones)
    else:
        logging.warning(f"No hay parser específico para competencia: {competencia}")
        return {}
    
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
    df_temp['archivo_origen'] = os.path.basename(archivo) # Guardar origen
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
# PASO 5: PREPARAR DATOS PARA BASE DE DATOS CON PARSERS ESPECÍFICOS
# ============================================================================

print("\n=== PASO 5: PREPARACIÓN PARA BD CON PARSERS ESPECÍFICOS ===")

# Detectar competencia para cada registro
df_filtrado['competencia_detectada'] = df_filtrado.apply(
    lambda row: detectar_competencia(row.get('archivo_origen', '')), axis=1
)

# Aplicar parsers específicos por competencia
print("Aplicando parsers específicos por competencia...")
campos_parseados = []

for idx, row in df_filtrado.iterrows():
    competencia = row['competencia_detectada']
    observaciones = row.get('observaciones', '')
    
    # Parsear observaciones según competencia
    datos_parseados = parsear_observaciones_por_competencia(observaciones, competencia)
    
    # Agregar datos básicos del registro
    datos_parseados.update({
        'index_original': idx,
        'competencia': competencia,
        'denominacion': row.get('denominacion', ''),
        'documento': row.get('documento', ''),
        'cargo': row.get('cargo', ''),
        'institucion': row.get('institucion', ''),
        'observaciones': observaciones,
        'archivo_origen': row.get('archivo_origen', '')
    })
    
    campos_parseados.append(datos_parseados)

# Crear DataFrame con datos parseados
df_parseado = pd.DataFrame(campos_parseados)

print(f"Registros procesados con parsers: {len(df_parseado)}")

# Mostrar estadísticas por competencia
print("\nEstadísticas por competencia:")
for competencia in df_parseado['competencia'].unique():
    count = len(df_parseado[df_parseado['competencia'] == competencia])
    print(f"  - {competencia}: {count} registros")

# Mapear columnas al formato requerido por la tabla de destino
df_final = pd.DataFrame({
    'fuente_competencia': df_parseado.get('competencia', ''),  # Nuevo campo
    'competencia': df_parseado.get('competencia', ''),
    'denominacion': df_parseado.get('denominacion', ''),
    'documento': df_parseado.get('documento', ''),
    'cargo': df_parseado.get('cargo', ''),
    'institucion': df_parseado.get('institucion', ''),
    'rol': df_parseado.get('rol', ''),
    'rit': df_parseado.get('rit', ''),
    'ruc': df_parseado.get('ruc', ''),
    'tribunal': df_parseado.get('tribunal', ''),
    'caratulado': df_parseado.get('caratulado', ''),
    'estado_causa': df_parseado.get('estado_causa', ''),
    'fecha_ingreso': df_parseado.get('fecha_ingreso', ''),
    'etapa': df_parseado.get('etapa', ''),
    'forma_inicio': df_parseado.get('forma_inicio', ''),
    'procedimiento': df_parseado.get('procedimiento', ''),
    'recurso': df_parseado.get('recurso', ''),
    'ubicacion': df_parseado.get('ubicacion', ''),
    'fecha_ubicacion': df_parseado.get('fecha_ubicacion', ''),
    'fuente': 'Oficina del Poder Judicial',
    'observaciones': df_parseado.get('observaciones', ''),
    'fecha_novedad': datetime.datetime.now().strftime('%Y-%m-%d')
})

# Limpiar valores nulos y vacíos
for col in df_final.columns:
    if col not in ['fecha_ingreso', 'fecha_ubicacion', 'fecha_novedad']:
        df_final[col] = df_final[col].fillna('').astype(str)
        df_final[col] = df_final[col].replace('nan', '')

# Eliminar duplicados finales
df_final = df_final.drop_duplicates()
print(f'Registros finales para envío: {len(df_final)}')

# Mostrar muestra de datos parseados
print("\nMuestra de datos parseados por competencia:")
for competencia in df_final['competencia'].unique():
    muestra = df_final[df_final['competencia'] == competencia].head(1)
    if not muestra.empty:
        print(f"\n--- {competencia.upper()} ---")
        for col in ['rol', 'rit', 'ruc', 'tribunal', 'caratulado', 'estado_causa', 'fecha_ingreso']:
            valor = muestra.iloc[0][col]
            if valor and valor != '':
                print(f"  {col}: {valor}")

# Validar campos críticos
print("\nValidación de campos críticos:")
campos_criticos = ['rol', 'rit', 'ruc', 'tribunal', 'caratulado', 'estado_causa']
for campo in campos_criticos:
    no_vacios = len(df_final[df_final[campo] != ''])
    porcentaje = (no_vacios / len(df_final)) * 100
    print(f"  {campo}: {no_vacios}/{len(df_final)} ({porcentaje:.1f}%) registros con datos")

# ============================================================================
# PASO 6: Mapeo final a estructura de la BD
# ============================================================================

def mapear_a_esquema_bd(df):
    """
    Mapea el DataFrame final al esquema de la base de datos.
    Maneja conversión de fechas y tipos de datos.
    """
    df_mapeado = df.copy()
    
    # Convertir fechas
    df_mapeado['fecha_ingreso'] = pd.to_datetime(df_mapeado['fecha_ingreso'], errors='coerce')
    df_mapeado['fecha_ubicacion'] = pd.to_datetime(df_mapeado['fecha_ubicacion'], errors='coerce')
    df_mapeado['fecha_novedad'] = pd.to_datetime(df_mapeado['fecha_novedad'], errors='coerce')
    
    # Asegurar que los campos de texto no excedan límites de la BD
    campos_texto = ['denominacion', 'cargo', 'institucion', 'tribunal', 'caratulado', 
                   'estado_causa', 'etapa', 'forma_inicio', 'procedimiento', 'recurso', 'ubicacion']
    
    for campo in campos_texto:
        if campo in df_mapeado.columns:
            # Limitar longitud y limpiar caracteres especiales
            df_mapeado[campo] = df_mapeado[campo].astype(str).str[:500]  # Límite de 500 caracteres
            df_mapeado[campo] = df_mapeado[campo].str.replace('\n', ' ').str.replace('\r', ' ')
            df_mapeado[campo] = df_mapeado[campo].str.strip()
    
    # Campos identificadores (ROL, RIT, RUC) - límite más corto
    campos_id = ['rol', 'rit', 'ruc', 'documento']
    for campo in campos_id:
        if campo in df_mapeado.columns:
            df_mapeado[campo] = df_mapeado[campo].astype(str).str[:50]
            df_mapeado[campo] = df_mapeado[campo].str.strip()
    
    return df_mapeado

print("\n=== PASO 6: MAPEO FINAL A ESTRUCTURA DE BD ===")

# Aplicar mapeo
df_para_bd = mapear_a_esquema_bd(df_final)

# Verificar que el campo fuente_competencia esté presente
if 'fuente_competencia' not in df_para_bd.columns:
    logging.error("El campo 'fuente_competencia' no está presente en el DataFrame final")
    df_para_bd['fuente_competencia'] = df_para_bd['competencia']  # Fallback

print(f"Campos incluidos en el envío a BD: {list(df_para_bd.columns)}")
print(f"Registros preparados para BD: {len(df_para_bd)}")

# Verificar distribución por fuente_competencia
print("\nDistribución por fuente_competencia:")
distribucion = df_para_bd['fuente_competencia'].value_counts()
for competencia, count in distribucion.items():
    print(f"  - {competencia}: {count} registros")

# ============================================================================
# PASO 6.5: GUARDAR COPIA DE DATOS FINALES PARA REPROCESAMIENTO
# ============================================================================

print("\n=== PASO 6.5: GUARDANDO COPIA PARA REPROCESAMIENTO ===")

# Crear carpeta para datos finales si no existe
carpeta_datos_finales = r'C:\Worldsys\Scrap-Poder-Judicial-CL\Resultados_Globales\Datos_Finales_BD'
if not os.path.exists(carpeta_datos_finales):
    os.makedirs(carpeta_datos_finales)
    print(f"✓ Carpeta creada: {carpeta_datos_finales}")

# Preparar DataFrame para guardar (convertir fechas a string para CSV)
df_para_csv = df_para_bd.copy()

# Convertir fechas a formato string para CSV
columnas_fecha = ['fecha_ingreso', 'fecha_ubicacion', 'fecha_novedad']
for col in columnas_fecha:
    if col in df_para_csv.columns:
        df_para_csv[col] = df_para_csv[col].dt.strftime('%Y-%m-%d').fillna('')

# Reemplazar NaN con strings vacíos
df_para_csv = df_para_csv.fillna('')

# Guardar por competencia para facilitar reprocesamiento
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archivos_guardados = []

for competencia in df_para_csv['fuente_competencia'].unique():
    if competencia and competencia != '':
        df_competencia = df_para_csv[df_para_csv['fuente_competencia'] == competencia]
        
        # Nombre del archivo con timestamp
        nombre_archivo = f"datos_finales_{competencia}_{timestamp}.csv"
        ruta_archivo = os.path.join(carpeta_datos_finales, nombre_archivo)
        
        # Guardar con separador ; para consistencia con archivos originales
        df_competencia.to_csv(ruta_archivo, sep=';', index=False, encoding='utf-8')
        archivos_guardados.append(nombre_archivo)
        
        print(f"✓ Guardado: {nombre_archivo} ({len(df_competencia)} registros)")
        logging.info(f"Datos finales guardados: {ruta_archivo} - {len(df_competencia)} registros")

# También guardar archivo consolidado
nombre_consolidado = f"datos_finales_consolidado_{timestamp}.csv"
ruta_consolidado = os.path.join(carpeta_datos_finales, nombre_consolidado)
df_para_csv.to_csv(ruta_consolidado, sep=';', index=False, encoding='utf-8')
archivos_guardados.append(nombre_consolidado)

print(f"✓ Guardado consolidado: {nombre_consolidado} ({len(df_para_csv)} registros)")
logging.info(f"Datos finales consolidados guardados: {ruta_consolidado} - {len(df_para_csv)} registros")

print(f"\n📁 Archivos guardados en: {carpeta_datos_finales}")
for archivo in archivos_guardados:
    print(f"  - {archivo}")

print(f"\n💡 NOTA: Para reprocesar estos datos:")
print(f"   1. Copia los archivos CSV a cualquier subcarpeta dentro de Resultados_Globales")
print(f"   2. Ejecuta nuevamente ejecutar_envio.py")
print(f"   3. Los archivos serán detectados automáticamente por la búsqueda recursiva")

# Definir tipos de datos para PostgreSQL
tipos_bd = {
    'fecha_ingreso': sqlalchemy.Date(),
    'fecha_ubicacion': sqlalchemy.Date(),
    'fecha_novedad': sqlalchemy.Date(),
    'fuente_competencia': sqlalchemy.String(50),
    'competencia': sqlalchemy.String(50),
    'rol': sqlalchemy.String(50),
    'rit': sqlalchemy.String(50),
    'ruc': sqlalchemy.String(50),
    'documento': sqlalchemy.String(50)
}
'''
# Envío a PostgreSQL
try:
    df_para_bd.to_sql(
        name='causas_judiciales',
        con=engine_postgres,
        schema='chile',
        if_exists='append',
        index=False,
        dtype=tipos_bd
    )
    print("✓ Datos enviados exitosamente a PostgreSQL")
except Exception as e:
    logging.error(f"Error al enviar datos a PostgreSQL: {str(e)}")
    print(f"✗ Error al enviar datos a PostgreSQL: {str(e)}")
    raise
'''
# ============================================================================
# PASO 7: MOVER ARCHIVOS PROCESADOS (Solo si el envío fue exitoso)
# ============================================================================

print("\n=== PASO 7: MOVIENDO ARCHIVOS PROCESADOS ===")
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
        logging.info(f"Archivo movido exitosamente: {archivo} -> {destino_archivo}")
    except Exception as e:
        print(f"✗ Error al mover {archivo}: {str(e)}")
        logging.error(f"Error al mover archivo {archivo}: {str(e)}")

print(f"✓ Archivos movidos exitosamente: {archivos_movidos}/{len(archivos)}")
logging.info(f"Archivos movidos: {archivos_movidos}/{len(archivos)}")

# ============================================================================
# FINALIZACIÓN Y ESTADÍSTICAS DETALLADAS
# ============================================================================

print(f"\n=== PROCESO COMPLETADO - {datetime.datetime.now()} ===")

# Estadísticas generales
print(f"\n📊 RESUMEN GENERAL:")
print(f"- Archivos procesados: {len(archivos)}")
print(f"- Registros iniciales: {len(df) if 'df' in locals() else 0}")
print(f"- Registros tras filtros: {len(df_filtrado) if 'df_filtrado' in locals() else 0}")
print(f"- Registros finales enviados a BD: {len(df_final)}")
print(f"- Archivos movidos: {archivos_movidos if 'archivos_movidos' in locals() else 0}")

# Estadísticas por competencia
if 'df_final' in locals() and len(df_final) > 0:
    print(f"\n📈 ESTADÍSTICAS POR COMPETENCIA:")
    stats_competencia = df_final['fuente_competencia'].value_counts()
    for competencia, count in stats_competencia.items():
        porcentaje = (count / len(df_final)) * 100
        print(f"  - {competencia}: {count} registros ({porcentaje:.1f}%)")
    
    # Estadísticas de campos parseados
    print(f"\n🔍 EFECTIVIDAD DE PARSERS:")
    campos_importantes = ['rol', 'rit', 'ruc', 'tribunal', 'caratulado', 'estado_causa', 'fecha_ingreso']
    for campo in campos_importantes:
        if campo in df_final.columns:
            no_vacios = len(df_final[df_final[campo].notna() & (df_final[campo] != '') & (df_final[campo] != 'nan')])
            porcentaje = (no_vacios / len(df_final)) * 100
            print(f"  - {campo}: {no_vacios}/{len(df_final)} ({porcentaje:.1f}%) registros con datos")

# Logging final
logging.info("=== PROCESO COMPLETADO ===")
logging.info(f"Archivos procesados: {len(archivos)}")
logging.info(f"Registros finales: {len(df_final) if 'df_final' in locals() else 0}")
logging.info(f"Archivos movidos: {archivos_movidos if 'archivos_movidos' in locals() else 0}")

if 'df_final' in locals() and len(df_final) > 0:
    for competencia, count in df_final['fuente_competencia'].value_counts().items():
        logging.info(f"Competencia {competencia}: {count} registros")

print(f"\n✅ PROCESO COMPLETO FINALIZADO")
print(f"📝 Log guardado en: {log_filename}")
print(f"🗄️  Datos enviados a PostgreSQL: chile.causas_judiciales")
print(f"📁 Archivos procesados movidos a: {carpeta_destino}")

# Verificación final
if 'df_para_bd' in locals() and len(df_para_bd) > 0:
    print(f"\n🎯 VERIFICACIÓN FINAL:")
    print(f"✓ Campo 'fuente_competencia' incluido: {'fuente_competencia' in df_para_bd.columns}")
    print(f"✓ Registros con fuente_competencia válida: {len(df_para_bd[df_para_bd['fuente_competencia'] != ''])}")
    print(f"✓ Parsers aplicados correctamente por competencia")
    print(f"✓ Datos estructurados y enviados a base de datos")
else:
    print(f"\n⚠️  ADVERTENCIA: No se procesaron datos para envío a BD")

