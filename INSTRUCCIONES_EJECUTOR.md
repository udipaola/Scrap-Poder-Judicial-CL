# 🚀 Ejecutor Centralizado - Scraper Poder Judicial Chile

Este proyecto incluye dos ejecutores centralizados que facilitan la ejecución de todos los módulos de scraping con una interfaz amigable.

## 📁 Archivos Disponibles

### 1. `ejecutar_scraping.bat` (Windows)
- **Tipo**: Script de lotes para Windows
- **Ventajas**: Ejecución directa, no requiere Python instalado
- **Desventajas**: Interfaz básica, solo Windows

### 2. `ejecutar_scraping.py` (Multiplataforma)
- **Tipo**: Script Python avanzado
- **Ventajas**: Interfaz mejorada, validaciones robustas, multiplataforma
- **Requisitos**: Python 3.6+

## 🎯 Módulos Disponibles

| Módulo | Descripción | Directorio |
|--------|-------------|------------|
| **Corte Suprema** | Scraping de la Corte Suprema de Chile | `Corte_suprema/` |
| **Corte de Apelaciones** | Scraping de las Cortes de Apelaciones | `Corte_apelaciones/` |
| **Tribunales Civil** | Scraping de tribunales civiles | `tribunales_civil/` |
| **Tribunales Cobranza** | Scraping de tribunales de cobranza | `tribunales_cobranza/` |
| **Tribunales Laboral** | Scraping de tribunales laborales | `tribunales_laboral/` |
| **Tribunales Penal** | Scraping de tribunales penales | `tribunales_penal/` |

## 🚀 Cómo Usar

### Opción 1: Script BAT (Windows)

1. **Ejecutar el archivo**:
   ```cmd
   ejecutar_scraping.bat
   ```

2. **Seguir el menú interactivo**:
   - Seleccionar módulo (1-6)
   - Configurar modo (histórico/diario)
   - Establecer parámetros
   - Confirmar ejecución

### Opción 2: Script Python (Recomendado)

1. **Ejecutar el script**:
   ```bash
   python ejecutar_scraping.py
   ```

2. **Navegar por la interfaz mejorada**:
   - Menú principal con descripciones
   - Validación automática de fechas
   - Configuración guiada de parámetros
   - Confirmación detallada

## ⚙️ Parámetros Configurables

### 📅 Modo de Ejecución
- **Histórico**: Permite especificar un rango de fechas personalizado
- **Diario**: Usa la fecha actual

### 🔧 Parámetros Técnicos

| Parámetro | Descripción | Valor Recomendado | Rango |
|-----------|-------------|-------------------|-------|
| **Procesos** | Número de procesos concurrentes | 2-4 | 1-10 |
| **Tamaño Tanda** | Procesos que inician simultáneamente | 2 | 1-procesos |
| **Delay Tanda** | Segundos entre inicio de tandas | 90 | 10-300 |
| **Modo Headless** | Ejecutar sin ventana del navegador | Sí | Sí/No |

### 📅 Formato de Fechas
- **Formato requerido**: `YYYY-MM-DD`
- **Ejemplos válidos**: 
  - `2024-01-01`
  - `2024-12-31`
  - `2023-06-15`

## 🎮 Ejemplo de Uso Completo

### Escenario: Scraping histórico de Tribunales Civil

1. **Ejecutar**: `python ejecutar_scraping.py`
2. **Seleccionar**: `3` (Tribunales Civil)
3. **Modo**: `1` (Histórico)
4. **Fecha desde**: `2024-01-01`
5. **Fecha hasta**: `2024-01-31`
6. **Procesos**: `3`
7. **Tamaño tanda**: `2`
8. **Delay tanda**: `90`
9. **Headless**: `S`
10. **Confirmar**: `S`

## 🛠️ Características Avanzadas (Script Python)

### ✅ Validaciones Automáticas
- Formato de fechas correcto
- Rango de fechas lógico (hasta >= desde)
- Valores numéricos en rangos válidos
- Existencia de archivos de módulos

### 🎨 Interfaz Mejorada
- Emojis para mejor visualización
- Colores y separadores claros
- Mensajes de error descriptivos
- Confirmación detallada antes de ejecutar

### 🔄 Manejo de Errores
- Captura de interrupciones (Ctrl+C)
- Manejo de errores de ejecución
- Verificación de módulos existentes
- Códigos de retorno informativos

## 📊 Resultados

Todos los resultados se guardan en:
```
Resultados_Globales/
├── resultados_[modulo]_[fecha].csv
├── checkpoint_[modulo].json
└── error_screenshot_[id].png (si hay errores)
```

## 🚨 Solución de Problemas

### Error: "Módulo no encontrado"
- Verificar que el directorio del módulo existe
- Confirmar que el archivo Python principal está presente

### Error: "Python no reconocido"
- Instalar Python 3.6 o superior
- Agregar Python al PATH del sistema

### Error: "Formato de fecha inválido"
- Usar formato `YYYY-MM-DD`
- Verificar que la fecha sea válida (ej: no 2024-02-30)

### Ejecución Lenta
- Reducir número de procesos concurrentes
- Aumentar delay entre tandas
- Verificar conexión a internet

## 💡 Consejos de Uso

1. **Empezar con pocos procesos**: Usar 2-3 procesos inicialmente
2. **Modo headless recomendado**: Mejora el rendimiento
3. **Monitorear recursos**: Vigilar uso de CPU y memoria
4. **Rangos de fechas pequeños**: Para pruebas iniciales
5. **Backup de resultados**: Los archivos CSV son valiosos

## 🔧 Personalización

Para agregar nuevos módulos, editar el diccionario `modulos` en `ejecutar_scraping.py`:

```python
'7': {
    'nombre': 'Nuevo Módulo',
    'directorio': 'nuevo_modulo',
    'archivo': 'main_nuevo.py',
    'descripcion': 'Descripción del nuevo módulo'
}
```

---

**¡Disfruta del scraping centralizado! 🎉**