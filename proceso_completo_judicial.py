import pandas as pd
import glob
import os
import re
import sqlalchemy
import sys
import datetime
import shutil

# ============================================================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ============================================================================

# Configurar archivo de log para capturar toda la ejecución
log_filename = f"proceso_completo_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_file = open(log_filename, "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

print(f"Iniciando proceso completo de consolidación y envío a BD - {datetime.datetime.now()}")

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

'''
# Lista de cargos a considerar
cargo_list = [
    'DENUNCIADO','DDO','RECURRIDO','QUERELLADO','IMPUTAD','QDO','DNDO','APOD',
    'DDOSOL','RECDO','DDO SOL','DDOSO','DDOSOLID','DDOSU','DDO SUB'
]

'''

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

# ============================================================================
# PASO 1: BUSCAR Y CARGAR ARCHIVOS CSV
# ============================================================================

print("\n=== PASO 1: CARGA DE ARCHIVOS CSV ===")
base_path = r'D:\RepositoriosDataWorldsys\Scrap-Poder-Judicial-CL\Resultados_Globales'
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

'''
# Filtrar por cargos válidos
df_filtrado = df[df['cargo'].str.startswith(tuple(cargo_list), na=False)]
print(f'Tras filtro de cargo: {len(df_filtrado)}')
'''
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
df_filtrado = df_filtrado[df_filtrado['documento'] != '0-0']
print(f'Tras eliminar RUT 0-0: {len(df_filtrado)}')

# Eliminar duplicados
df_filtrado = df_filtrado.drop_duplicates()
print(f'Tras eliminar duplicados: {len(df_filtrado)}')

# ============================================================================
# PASO 4: EXTRAER FECHA DE INGRESO
# ============================================================================

print("\n=== PASO 4: EXTRACCIÓN DE FECHAS ===")

# Extraer fecha de ingreso desde observaciones usando regex
patron_fecha = r'Ingreso: (\d{2}/\d{2}/\d{4})'
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
    'ruc': df_filtrado.get('documento', ''),
    'tribunal': df_filtrado.get('institucion', '')
})

# Eliminar duplicados finales
df_final = df_final.drop_duplicates()
print(f'Registros finales para envío: {len(df_final)}')

# ============================================================================
# PASO 6: GUARDAR ARCHIVO INTERMEDIO
# ============================================================================

print("\n=== PASO 6: GUARDADO DE ARCHIVO INTERMEDIO ===")
output_path = 'resultados_procesados_completo.csv'
df_final.to_csv(output_path, index=False, sep=';', encoding='utf-8')
print(f"Archivo guardado como: {output_path}")

# ============================================================================
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
    carpeta_destino = r'D:\RepositoriosDataWorldsys\Scrap-Poder-Judicial-CL\Resultados_enviados_bd'
    
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
print(f"- Archivo CSV generado: {output_path}")
print(f"- Archivos movidos a carpeta de enviados: {archivos_movidos if 'archivos_movidos' in locals() else 0}")

# Cerrar archivo de log y restaurar stdout/stderr
log_file.close()
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

print(f"\n✓ Proceso completo finalizado. Log guardado en: {log_filename}")
print(f"✓ Archivo CSV generado: {output_path}")
print(f"✓ Datos enviados a base de datos PostgreSQL")