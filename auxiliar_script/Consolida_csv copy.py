#%% [markdown]
# Importar librerías y definir funciones/filtros

import pandas as pd
import glob
import os
import re

# Lista de cargos a considerar
cargo_list = [
    'DENUNCIADO','DDO','RECURRIDO','QUERELLADO','IMPUTAD','QDO','DNDO','APOD',
    'DDOSOL','RECDO','DDO SOL','DDOSO','DDOSOLID','DDOSU','DDO SUB'
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

def limpiar_nombre(texto):
    if pd.isna(texto):
        return ''
    palabras = texto.split()
    palabras_filtradas = [p for p in palabras if p.upper() not in nombre_list1]
    return ' '.join(palabras_filtradas)

#%% [markdown]
# Buscar y cargar archivos resultados_YYYY_MM.csv

# Cambia el path base si es necesario
base_path = r'D:\RepositoriosDataWorldsys\Scrap-Poder-Judicial-CL\csvs'  # o la ruta donde están los archivos
pattern = os.path.join(base_path, '**', 'resultados*.csv')
archivos = glob.glob(pattern, recursive=True)
print(f'Archivos encontrados: {archivos}')

#%% [markdown]
# Leer y concatenar todos los archivos encontrados, mostrando columnas

dfs = []
for archivo in archivos:
    df_temp = pd.read_csv(archivo, sep=';', dtype=str)
    print(f'Archivo: {archivo}')
    print(f'Columnas: {df_temp.columns.tolist()}')
    # Normalizar nombres de columnas
    df_temp.columns = [col.lower().strip() for col in df_temp.columns]
    # Intentar renombrar si existe 'nombre' en vez de 'denominacion'
    if 'denominacion' not in df_temp.columns:
        if 'nombre' in df_temp.columns:
            df_temp = df_temp.rename(columns={'nombre': 'denominacion'})
        else:
            print(f"Advertencia: El archivo {archivo} no tiene columna 'denominacion' ni 'nombre'. Se omite.")
            continue
    dfs.append(df_temp)
if not dfs:
    raise ValueError("No se encontraron archivos válidos con columna 'denominacion' o 'nombre'.")
df = pd.concat(dfs, ignore_index=True)
print(f'Registros totales: {len(df)}')
print(f'Columnas finales: {df.columns.tolist()}')

#%% [markdown]
# Normalizar nombres de columnas (opcional, si hay inconsistencias)

df.columns = [col.lower().strip() for col in df.columns]
# Asegúrate que las columnas relevantes se llamen 'cargo' y 'denominacion'
print(df.columns)

#%% [markdown]
# Aplicar filtros

print(f'Registros totales antes de filtrar: {len(df)}')

# Filtrar por cargos
df_filtrado = df[df['cargo'].str.startswith(tuple(cargo_list), na=False)]
print(f'Registros tras filtro de cargo: {len(df_filtrado)}')

# Eliminar filas por nombres
df_filtrado = df_filtrado[~df_filtrado['denominacion'].str.startswith(tuple(nombre_list), na=False)]
print(f'Registros tras filtro de nombres: {len(df_filtrado)}')

# Eliminar filas con denominacion muy corta
df_filtrado = df_filtrado[df_filtrado['denominacion'].str.len() > 3]
print(f'Registros tras filtro de longitud: {len(df_filtrado)}')

# Limpiar valores de la columna 'denominacion'
df_filtrado['denominacion'] = df_filtrado['denominacion'].apply(limpiar_nombre)

# Eliminar filas vacías o NaN en 'denominacion'
df_filtrado = df_filtrado[df_filtrado['denominacion'].notna() & (df_filtrado['denominacion'] != '')]
print(f'Registros tras limpiar vacíos: {len(df_filtrado)}')

# Eliminar duplicados
df_filtrado = df_filtrado.drop_duplicates()
print(f'Registros tras eliminar duplicados: {len(df_filtrado)}')

# Eliminar registros con RUT = 0-0
df_filtrado = df_filtrado[df_filtrado['documento'] != '0-0']
print(f'Registros tras eliminar RUT 0-0: {len(df_filtrado)}')

# Extraer fecha de ingreso desde 'observaciones'

def extraer_fecha(observaciones):
    if pd.isna(observaciones):
        return None
    match = re.search(r'Ingreso: (\d{2}/\d{2}/\d{4})', observaciones)
    if match:
        return match.group(1)
    return None

# Crear columna 'fecha_ingreso'
df_filtrado['fecha_ingreso'] = df_filtrado['observaciones'].apply(extraer_fecha)

# Mostrar conteo de registros por fecha
distribucion_fechas = df_filtrado['fecha_ingreso'].value_counts().sort_index()
print('Distribución de registros por fecha:')
print(distribucion_fechas)

#%% [markdown]
# Guardar resultado (opcional)

df_filtrado.to_csv('resultados_filtrados.csv', index=False, sep=';')

#%% [markdown]
# Visualizar el DataFrame filtrado con pandagui

try:
    import pandasgui
    pandasgui.show(df_filtrado)
except ImportError:
    print("pandasgui no está instalado. Instálalo con: pip install pandasgui")
# %%
