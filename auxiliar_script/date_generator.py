import datetime

# --- Parámetros de Fechas ---
# Establece la fecha de inicio en formato AAAA, MM, DD
fecha_inicio = datetime.date(2025, 1, 1)

# Establece la fecha de fin en formato AAAA, MM, DD
fecha_fin = datetime.date(2025, 6, 30)
# -----------------------------

# Nombre del archivo de salida
nombre_archivo = "listado_fechas.txt"

try:
    # Abrimos el archivo en modo escritura ('w')
    with open(nombre_archivo, "w") as archivo:
        fecha_actual = fecha_inicio
        
        # Iteramos desde la fecha de inicio hasta la fecha de fin (inclusive)
        while fecha_actual <= fecha_fin:
            # Formateamos la fecha al formato DD/MM/YYYY
            fecha_formateada = fecha_actual.strftime("%d/%m/%Y")
            
            # Creamos la línea con el formato "DD/MM/YYYY;DD/MM/YYYY"
            linea = f"{fecha_formateada};{fecha_formateada}\n"
            
            # Escribimos la línea en el archivo
            archivo.write(linea)
            
            # Incrementamos la fecha en 1 día para la siguiente iteración
            fecha_actual += datetime.timedelta(days=1)
            
    print(f"✅ ¡Éxito! El archivo '{nombre_archivo}' ha sido generado correctamente.")

except IOError as e:
    print(f"❌ Error: No se pudo escribir en el archivo '{nombre_archivo}'.")
    print(f"Detalle: {e}")