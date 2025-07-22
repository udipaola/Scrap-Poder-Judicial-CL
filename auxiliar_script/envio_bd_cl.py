import pandas as pd
import sqlalchemy
import sys
import datetime

# Redirigir stdout y stderr a un archivo de log
log_filename = f"envio_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_file = open(log_filename, "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

# Configuración de conexión a Postgres
PG_LDI_Username = 'adminPg'
PG_LDI_Password = 'M#M#%6jEHh3F3HJ%'
PG_LDI_Hostname = 'pgsv-dev-eastus-001.postgres.database.azure.com'
PG_LDI_Database = 'postgres'
engine_postgres = sqlalchemy.create_engine(f'postgresql://{PG_LDI_Username}:{PG_LDI_Password}@{PG_LDI_Hostname}/{PG_LDI_Database}')

# Leer el archivo CSV con separador de punto y coma
def read_and_normalize_csv(input_path):
    df = pd.read_csv(input_path, sep=';')
    df.columns = df.columns.str.lower()
    return df

input_path = 'resultados_filtrados.csv'
df = read_and_normalize_csv(input_path)

# Mapear columnas del DataFrame a los campos requeridos por la tabla (solo los solicitados)
df_final = pd.DataFrame({
    'cargo': df.get('cargo', ''),
    'denominacion': df.get('denominacion', ''),
    'observaciones': df.get('observaciones', ''),
    'fuente': 'Oficina del Poder Judicial',
    'ruc': df.get('documento', ''),
    'tribunal': df.get('institucion', '')
})

# Borra duplicados
df_final = df_final.drop_duplicates()

# Guardar el DataFrame editado en un nuevo archivo CSV con separador ; y codificación UTF-8
output_path = 'resultados_filtrados_editado.csv'
df_final.to_csv(output_path, index=False, sep=';', encoding='utf-8')
print(f"Archivo guardado como {output_path}")

# Enviar el DataFrame a la tabla de Postgres
df_final.to_sql('causas_judiciales', schema='chile', con=engine_postgres, if_exists='append', index=False)
print("Datos enviados a Postgres correctamente.")

# Cerrar el archivo de log y restaurar stdout/stderr
log_file.close()
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
print(f"Log guardado en {log_filename}")
