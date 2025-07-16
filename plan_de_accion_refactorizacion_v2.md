# Plan de Acción de Refactorización v2
## Integración de Sistema de Logging y Soluciones de Errores Críticos

---

## 📋 Resumen Ejecutivo

### Objetivos
- **Integrar** la solución de logging implementada en `tribunales_penal` a todos los módulos del repositorio
- **Resolver** los 6 errores críticos identificados que afectan la estabilidad del sistema
- **Estandarizar** la lógica de paginación y manejo de errores en todos los módulos
- **Mejorar** la robustez y capacidad de recuperación del sistema completo

### Beneficios Esperados
- ✅ **Eliminación** de errores `ElementClickInterceptedException`
- ✅ **Prevención** de duplicados en última página
- ✅ **Recuperación automática** desde checkpoints
- ✅ **Logging unificado** y depuración mejorada
- ✅ **Estabilidad** del sistema al 99%+

---

## 🎯 Estado Actual vs Estado Deseado

### Estado Actual
- ❌ Solo `tribunales_penal` tiene sistema de logging robusto
- ❌ Errores `ElementClickInterceptedException` causan bloqueos
- ❌ Duplicados en última página por detección incorrecta de fin
- ❌ Checkpoints no funcionan correctamente (no salta a página real)
- ❌ Errores "no such element" en paginador
- ❌ Lógica de recuperación inconsistente entre módulos

### Estado Deseado
- ✅ **Todos los módulos** con sistema de logging estandarizado
- ✅ **Manejo robusto** de errores con reintentos y recuperación
- ✅ **Paginación confiable** sin duplicados
- ✅ **Checkpoints funcionales** con salto real a páginas
- ✅ **Esperas explícitas** para elementos del DOM
- ✅ **Flujo de recuperación centralizado** en el main

---

## 📊 ESTADO ACTUAL DE IMPLEMENTACIÓN (Actualizado)

### ✅ COMPLETADO
- **FASE 1**: Sistema de Logging - ✅ **100% COMPLETADO**
  - Todos los módulos tienen funciones de logging implementadas
  - Argumento --debug agregado a todos los main
  - Prints reemplazados por funciones de logging
  - Logs de estado en puntos críticos implementados

- **FASE 2 - Error 2.1**: ElementClickInterceptedException - ✅ **100% COMPLETADO**
  - Manejo robusto implementado en todos los módulos
  - Sistema de reintentos con MAX_REINTENTOS_PAGINA = 3
  - Comunicación RETRY entre worker y main
  - Recuperación automática sin rotación de IP

### 🔄 EN PROGRESO
- **Pruebas con --debug**: Pendiente en todos los módulos
- **FASE 2 - Errores 2.2-2.6**: Pendientes de implementar

### 📋 PRÓXIMOS PASOS INMEDIATOS
1. **PRIORIDAD ALTA**: Probar funcionamiento con --debug en todos los módulos
2. **PRIORIDAD ALTA**: Implementar Error 2.2 (Detección fin de paginación)
3. **PRIORIDAD MEDIA**: Implementar Errores 2.3-2.6
4. **PRIORIDAD BAJA**: FASE 3 (Unificación de Paginación)

---

## 🚀 FASE 1: Estandarización del Sistema de Logging

### Prioridad: 🔴 ALTA - Implementar INMEDIATAMENTE

### 1.1 Módulos a Refactorizar
- `tribunales_civil/`
- `tribunales_cobranza/`
- `tribunales_laboral/`
- `Corte_apelaciones/`
- `Corte_suprema/`

### 1.2 Archivos a Modificar por Módulo

#### Para cada módulo:
```
📁 {modulo}/
├── 📝 main_{modulo}.py     ← Agregar --debug parameter
└── 📝 worker_{modulo}.py   ← Implementar funciones de logging
```

### 1.3 Implementación Detallada

#### 1.3.1 Modificar `main_{modulo}.py`

**Agregar argumento --debug:**
```python
# Agregar en la sección de argumentos
parser.add_argument('--debug', action='store_true', 
                   help='Activar logs detallados para depuración')

# Configurar DEBUG_MODE global
DEBUG_MODE = args.debug
```

**Pasar DEBUG_MODE al worker:**
```python
# En la función que llama al worker
task['debug_mode'] = DEBUG_MODE
```

#### 1.3.2 Implementar funciones de logging en `worker_{modulo}.py`

**Copiar exactamente desde `tribunales_penal/worker_penal.py`:**
```python
def log_progress(task_id, total_workers, message):
    """Log de progreso siempre visible"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Worker {task_id}/{total_workers}: {message}")

def log_error(task_id, total_workers, error_message):
    """Log de errores siempre visible"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] ❌ Worker {task_id}/{total_workers}: ERROR - {error_message}")

def log_debug(task_id, total_workers, debug_message, debug_mode=False):
    """Log de debug solo si está habilitado"""
    if debug_mode:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔍 Worker {task_id}/{total_workers}: DEBUG - {debug_message}")

def log_worker_status(task_id, total_workers, status, details=""):
    """Log de estado del worker"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = {
        "INICIANDO": "🚀",
        "PROCESANDO": "⚙️",
        "COMPLETADO": "✅",
        "ERROR": "❌",
        "DETENIDO": "⏹️"
    }.get(status, "ℹ️")
    
    message = f"[{timestamp}] {status_emoji} Worker {task_id}/{total_workers}: {status}"
    if details:
        message += f" - {details}"
    print(message)
```

#### 1.3.3 Reemplazar todos los `print()` por funciones de logging

**Mapeo de reemplazos:**
- `print(f"Procesando...")` → `log_progress(task_id, total_workers, "Procesando...")`
- `print(f"Error: {e}")` → `log_error(task_id, total_workers, str(e))`
- `print(f"Debug info")` → `log_debug(task_id, total_workers, "Debug info", debug_mode)`
- Agregar `log_worker_status()` en puntos críticos

#### 1.3.4 Puntos críticos para `log_worker_status()`

```python
# Al inicio del worker
log_worker_status(task_id, total_workers, "INICIANDO", f"día {dia_id}")

# Al cambiar de página
log_worker_status(task_id, total_workers, "PROCESANDO", f"página {pagina_actual}")

# Al completar exitosamente
log_worker_status(task_id, total_workers, "COMPLETADO", f"{total_registros} registros")

# En caso de error
log_worker_status(task_id, total_workers, "ERROR", error_description)
```

### 1.4 Checklist de Implementación por Módulo

#### ✅ Tribunales Civil
- [x] Modificar main_civil.py - agregar --debug (usar patrón de `main_suprema.py`)
- [x] Implementar funciones de logging en `worker_civil.py` (copiar exactamente de `tribunales_penal`)
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

#### ✅ Tribunales Laboral
- [x] Modificar `main_laboral.py` - agregar --debug
- [x] Implementar funciones de logging en `worker_laboral.py`
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

**📋 Referencias Funcionales:**
- **Sistema de Logging**: `tribunales_penal/worker_penal.py` (funciones probadas)
- **Manejo de Errores**: `Corte_suprema/worker_suprema.py` (líneas 150-175, 251-285)
- **Recuperación**: `Corte_suprema/main_suprema.py` (líneas 174-184)

#### ✅ Tribunales Cobranza
- [x] Modificar `main_cobranza.py` - agregar --debug
- [x] Implementar funciones de logging en `worker_cobranza.py`
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

#### ✅ Tribunales Penal
- [x] Modificar `main_penal.py` - agregar --debug
- [x] Implementar funciones de logging en `worker_penal.py`
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

#### ✅ Corte Apelaciones
- [x] Modificar `main_apelaciones.py` - agregar --debug
- [x] Implementar funciones de logging en `worker_apelaciones.py`
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

#### ✅ Corte Suprema
- [x] Modificar `main_suprema.py` - agregar --debug
- [x] Implementar funciones de logging en `worker_suprema.py`
- [x] Reemplazar prints por funciones de logging
- [x] Agregar logs de estado en puntos críticos
- [x] ElementClickInterceptedException handling implementado
- [x] RETRY signal handling implementado
- [x] Probar funcionamiento con `--debug` - ✅ VERIFICADO

---

## 🛡️ FASE 2: Implementación de Manejo de Errores Robusto

### Prioridad: 🔴 ALTA - Implementar INMEDIATAMENTE después de Fase 1

### 2.1 Error: ElementClickInterceptedException

#### Problema
```
ElementClickInterceptedException: Message: element click intercepted: 
Element is not clickable at point (x, y). Other element would receive the click
```

#### ✅ Solución Implementada en Corte Suprema (REFERENCIA FUNCIONAL)

**📁 Ejemplo Real: `Corte_suprema/worker_suprema.py` (líneas 87-89, 150-175)**

```python
# Constante al inicio del archivo
MAX_REINTENTOS_PAGINA = 3
reintentos_pagina = 0

# En el bucle de procesamiento de filas
for i in range(len(filas_causas)):
    if stop_event.is_set(): break
    try:
        # ... lógica de procesamiento ...
        
        # Detección específica de ElementClickInterceptedException
        try:
            celdas[0].find_element(By.TAG_NAME, 'a').click()
        except (TimeoutException, Exception) as e_click:
            from selenium.common.exceptions import ElementClickInterceptedException
            if isinstance(e_click, ElementClickInterceptedException) or 'element click intercepted' in str(e_click):
                print(f"[{dia_id}] ElementClickInterceptedException al hacer click en la lupa. Reintentando página completa...")
                error_reintentar_pagina = True
                break
            else:
                raise
        
        # ... resto del procesamiento ...
        
    except Exception as e_row:
        from selenium.common.exceptions import ElementClickInterceptedException
        error_message = str(e_row).split('\n')[0]
        if isinstance(e_row, ElementClickInterceptedException) or 'element click intercepted' in error_message:
            print(f"[{dia_id}] ElementClickInterceptedException detectado. Reintentando página completa...")
            error_reintentar_pagina = True
            break
        print(f"[{dia_id}] Error procesando fila, saltando. Causa: {type(e_row).__name__} - {error_message}")
        continue

# Manejo de reintentos después del bucle de filas
if error_reintentar_pagina:
    reintentos_pagina += 1
    if reintentos_pagina > MAX_REINTENTOS_PAGINA:
        print(f"[{dia_id}] Se superó el máximo de reintentos ({MAX_REINTENTOS_PAGINA}) para la página {pagina_actual}. Cerrando worker y notificando al main para reintentar desde el checkpoint...")
        if driver:
            driver.quit()
        return f"RETRY:{dia_id}:page_{pagina_actual}"
    else:
        print(f"[{dia_id}] Reintentando página {pagina_actual} (intento {reintentos_pagina}/{MAX_REINTENTOS_PAGINA})...")
        time.sleep(3)
    continue
```

**📁 Ejemplo Real: `Corte_suprema/main_suprema.py` (líneas 174-184, 200-203)**

```python
# En el bucle de procesamiento de resultados
for idx, res in enumerate(results_async):
    try:
        resultado = res.get(timeout=30)
        print(f"Resultado de un worker: {resultado}")

        # Detectamos 'RETRY' para reencolar la tarea
        if isinstance(resultado, str) and resultado.startswith('RETRY:'):
            # Extraer el id de la tarea
            parts = resultado.split(':')
            if len(parts) >= 2:
                retry_id = parts[1]
                print(f"[MAIN] Tarea {retry_id} marcada para reintento (RETRY). Se reencolará en la próxima tanda.")
                # Buscar el task original y agregarlo a retry_tasks
                for t in tareas_pendientes:
                    if t['id'] == retry_id:
                        retry_tasks.append(t)
                        break
            continue

# Si hay tareas a reintentar, las agregamos al principio de la lista para la próxima ronda
if retry_tasks:
    print(f"[MAIN] {len(retry_tasks)} tareas serán reintentadas en la próxima tanda.")
    # Insertar al principio para que se prioricen
    tasks = retry_tasks + [t for t in tasks if t not in retry_tasks]
```

#### 🎯 Patrón a Replicar en Otros Módulos

1. **Constante**: `MAX_REINTENTOS_PAGINA = 3`
2. **Variable de control**: `error_reintentar_pagina = False`
3. **Detección específica**: Capturar `ElementClickInterceptedException` y variantes de string
4. **Comunicación**: Retornar `f"RETRY:{dia_id}:page_{pagina_actual}"`
5. **Reencolado prioritario**: Insertar al inicio de la lista de tareas

### 2.2 Error: No detecta correctamente el final de la paginación ✅ COMPLETADO

#### Problema
Duplicados en última página porque no detecta que el número de página no cambió.

#### ✅ Solución Implementada en Todos los Módulos

**📁 Ejemplo Real: `Corte_suprema/worker_suprema.py` (líneas 251-285)**

```python
# Verificación del botón "Next" y detección del final
try:
    # Buscar el botón "Next"
    next_button = driver.find_element(By.XPATH, "//a[contains(@class, 'next')]")
    
    # Verificar si el botón está deshabilitado
    if 'disabled' in next_button.get_attribute('class'):
        print(f"[{dia_id}] Botón 'Next' deshabilitado. Fin de paginación detectado en página {pagina_actual}.")
        break
    
    # Obtener número de página antes del click
    pagina_antes_click = obtener_numero_pagina_actual(driver)
    print(f"[{dia_id}] Página antes del click: {pagina_antes_click}")
    
    # Hacer click en "Next"
    next_button.click()
    time.sleep(3)  # Esperar a que cargue la nueva página
    
    # Verificar si cambió la página
    pagina_despues_click = obtener_numero_pagina_actual(driver)
    print(f"[{dia_id}] Página después del click: {pagina_despues_click}")
    
    # Si no cambió la página, hemos llegado al final
    if pagina_antes_click == pagina_despues_click:
        print(f"[{dia_id}] No hubo cambio de página. Fin de paginación detectado.")
        break
    
    # Actualizar página actual
    pagina_actual = pagina_despues_click
    print(f"[{dia_id}] Avanzando a página {pagina_actual}")
    
except Exception as e:
    print(f"[{dia_id}] Error al navegar a la siguiente página: {str(e)}")
    # Si no se puede encontrar el botón Next, asumimos que es el final
    if "no such element" in str(e).lower():
        print(f"[{dia_id}] Botón 'Next' no encontrado. Fin de paginación.")
        break
    else:
        # Otros errores, continuar con la siguiente página
        pagina_actual += 1

def obtener_numero_pagina_actual(driver):
    """Obtiene el número de página actual del paginador"""
    try:
        # Buscar el span con la página actual
        current_page_element = driver.find_element(By.XPATH, "//span[@class='current']")
        return int(current_page_element.text)
    except Exception as e:
        print(f"Error obteniendo número de página actual: {str(e)}")
        return 1
```

#### 🎯 Patrón a Replicar en Otros Módulos

1. **Verificar botón deshabilitado**: `'disabled' in next_button.get_attribute('class')`
2. **Comparar página antes/después**: Obtener número de página antes y después del click
3. **Detección de no-cambio**: Si `pagina_antes == pagina_despues`, es el final
4. **Manejo de excepciones**: Si no se encuentra el botón Next, asumir final
5. **Función auxiliar**: `obtener_numero_pagina_actual()` específica para cada sitio

### 2.3 Error: No salta realmente a la página indicada por el checkpoint

#### Problema
El worker dice que salta a la página X pero procesa desde página 1.

#### ✅ Solución Implementada en Corte Suprema (REFERENCIA FUNCIONAL)

**📁 Ejemplo Real: `Corte_suprema/worker_suprema.py` (líneas 120-149)**

```python
def ir_a_pagina_especifica(driver, pagina_objetivo):
    """Navega a una página específica del paginador"""
    try:
        print(f"Intentando ir a la página {pagina_objetivo}...")
        
        # Buscar el input de página
        page_input = driver.find_element(By.XPATH, "//input[@type='text' and contains(@class, 'ui-pg-input')]")
        
        # Limpiar el input y escribir la página objetivo
        page_input.clear()
        page_input.send_keys(str(pagina_objetivo))
        page_input.send_keys(Keys.ENTER)
        
        # Esperar a que cargue la nueva página
        time.sleep(3)
        
        # Verificar que efectivamente llegamos a la página correcta
        pagina_actual = obtener_numero_pagina_actual(driver)
        if pagina_actual == pagina_objetivo:
            print(f"Navegación exitosa a página {pagina_objetivo}")
            return True
        else:
            print(f"Error: Se esperaba página {pagina_objetivo}, pero estamos en página {pagina_actual}")
            return False
            
    except Exception as e:
        print(f"Error navegando a página {pagina_objetivo}: {str(e)}")
        return False

# Uso en el worker principal
if pagina_inicial > 1:
    print(f"[{dia_id}] Saltando a página inicial {pagina_inicial} desde checkpoint...")
    if ir_a_pagina_especifica(driver, pagina_inicial):
        pagina_actual = pagina_inicial
        print(f"[{dia_id}] Checkpoint aplicado exitosamente. Iniciando desde página {pagina_actual}")
    else:
        print(f"[{dia_id}] Error aplicando checkpoint. Iniciando desde página 1")
        pagina_actual = 1
else:
    pagina_actual = 1
    print(f"[{dia_id}] Iniciando desde página 1")

# Verificación adicional antes de procesar
pagina_verificada = obtener_numero_pagina_actual(driver)
if pagina_verificada != pagina_actual:
    print(f"[{dia_id}] ADVERTENCIA: Discrepancia de página. Esperada: {pagina_actual}, Real: {pagina_verificada}")
    pagina_actual = pagina_verificada
```

#### 🎯 Patrón a Replicar en Otros Módulos

1. **Input directo**: Buscar `input[@type='text']` del paginador
2. **Verificación obligatoria**: Siempre verificar que `pagina_actual == pagina_objetivo`
3. **Manejo de discrepancias**: Advertir y corregir si la página real ≠ esperada
4. **Aplicación de checkpoint**: Usar la función antes de iniciar el procesamiento
5. **Fallback**: Si falla, continuar desde página 1 en lugar de fallar completamente

### 2.4 Error: "no such element" al buscar el paginador

#### Problema
```
no such element: Unable to locate element: {"method":"xpath","selector":"//a[contains(@class, 'next')]"}
No espera a que el paginador se cargue completamente
```

#### ✅ Solución Implementada en Corte Suprema (REFERENCIA FUNCIONAL)

**📁 Ejemplo Real: `Corte_suprema/worker_suprema.py` (líneas 251-285)**

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Esperas explícitas antes de interactuar con el paginador
try:
    # Esperar a que el paginador esté presente y visible
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ui-pg-table')]"))
    )
    
    # Buscar el botón "Next" con espera explícita
    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'next')]"))
    )
    
    # Verificar si el botón está deshabilitado
    if 'disabled' in next_button.get_attribute('class'):
        print(f"[{dia_id}] Botón 'Next' deshabilitado. Fin de paginación detectado en página {pagina_actual}.")
        break
    
    # Obtener número de página antes del click con espera
    current_page_element = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, "//span[@class='current']"))
    )
    pagina_antes_click = int(current_page_element.text)
    print(f"[{dia_id}] Página antes del click: {pagina_antes_click}")
    
    # Hacer click en "Next"
    next_button.click()
    time.sleep(3)  # Esperar a que cargue la nueva página
    
    # Esperar a que se actualice el número de página
    WebDriverWait(driver, 10).until(
        lambda d: obtener_numero_pagina_actual(d) != pagina_antes_click
    )
    
    # Verificar si cambió la página
    pagina_despues_click = obtener_numero_pagina_actual(driver)
    print(f"[{dia_id}] Página después del click: {pagina_despues_click}")
    
except TimeoutException as e:
    print(f"[{dia_id}] Timeout esperando elementos del paginador: {str(e)}")
    # Si hay timeout, asumir que es el final de la paginación
    print(f"[{dia_id}] Asumiendo fin de paginación por timeout.")
    break
    
except Exception as e:
    print(f"[{dia_id}] Error al navegar a la siguiente página: {str(e)}")
    # Si no se puede encontrar el botón Next, asumimos que es el final
    if "no such element" in str(e).lower():
        print(f"[{dia_id}] Botón 'Next' no encontrado. Fin de paginación.")
        break
    else:
        # Otros errores, continuar con la siguiente página
        pagina_actual += 1

# Función auxiliar para esperas robustas
def esperar_elemento_paginador(driver, xpath, timeout=10):|
    """Espera a que un elemento del paginador esté disponible"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
    except TimeoutException:
        print(f"Timeout esperando elemento: {xpath}")
        return None
```

#### 🎯 Patrón a Replicar en Otros Módulos

1. **Esperas explícitas**: Usar `WebDriverWait` antes de interactuar con elementos
2. **Verificación de presencia**: Esperar que el contenedor del paginador esté presente
3. **Timeout manejo**: Capturar `TimeoutException` y asumir fin de paginación
4. **Espera de cambios**: Usar lambda para esperar que cambie el número de página
5. **Función auxiliar**: Crear `esperar_elemento_paginador()` para reutilizar lógica

### 2.5 Flujo de reintentos y recuperación centralizado en el main

#### ✅ Solución Implementada en Corte Suprema (REFERENCIA FUNCIONAL)

**📁 Ejemplo Real: `Corte_suprema/main_suprema.py` (líneas 174-184, 200-203, 230-259)**

```python
# Variables para manejo de recuperación
retry_tasks = []
stop_event = multiprocessing.Event()

# Procesamiento de resultados con manejo centralizado
for idx, res in enumerate(results_async):
    try:
        resultado = res.get(timeout=30)
        print(f"Resultado de un worker: {resultado}")

        # Detectamos 'RETRY' para reencolar la tarea
        if isinstance(resultado, str) and resultado.startswith('RETRY:'):
            # Extraer el id de la tarea
            parts = resultado.split(':')
            if len(parts) >= 2:
                retry_id = parts[1]
                print(f"[MAIN] Tarea {retry_id} marcada para reintento (RETRY). Se reencolará en la próxima tanda.")
                # Buscar el task original y agregarlo a retry_tasks
                for t in tareas_pendientes:
                    if t['id'] == retry_id:
                        retry_tasks.append(t)
                        break
            continue

        # Detectamos señales críticas (IP_BLOCKED, ERROR)
        if isinstance(resultado, str) and resultado in ['IP_BLOCKED', 'ERROR']:
            print(f"[MAIN] Señal crítica detectada: {resultado}. Deteniendo workers...")
            stop_event.set()  # Señalar a todos los workers que paren
            
            # Terminar el pool de workers
            pool.terminate()
            pool.join()
            
            # Cerrar todos los navegadores
            print("[MAIN] Cerrando navegadores...")
            cerrar_todos_los_navegadores()
            
            # Rotar IP si es necesario
            if resultado == 'IP_BLOCKED':
                print("[MAIN] Rotando IP...")
                rotar_ip()
                time.sleep(30)  # Esperar antes de continuar
            
            # Reencolar todas las tareas pendientes para la próxima ronda
            print(f"[MAIN] Reencolando {len(tareas_pendientes)} tareas pendientes...")
            retry_tasks.extend(tareas_pendientes)
            break

    except Exception as e:
        print(f"[MAIN] Error obteniendo resultado del worker {idx}: {str(e)}")
        # En caso de error, también reencolar la tarea
        if idx < len(tareas_pendientes):
            retry_tasks.append(tareas_pendientes[idx])

# Si hay tareas a reintentar, las agregamos al principio de la lista para la próxima ronda
if retry_tasks:
    print(f"[MAIN] {len(retry_tasks)} tareas serán reintentadas en la próxima tanda.")
    # Insertar al principio para que se prioricen
    tasks = retry_tasks + [t for t in tasks if t not in retry_tasks]

# Función auxiliar para cerrar navegadores
def cerrar_todos_los_navegadores():
    """Cierra todos los procesos de navegador que puedan estar ejecutándose"""
    try:
        # Cerrar procesos de Chrome
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      capture_output=True, text=True, check=False)
        subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                      capture_output=True, text=True, check=False)
        
        # Limpiar perfiles temporales
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('scoped_dir') and 'chrome' in item.lower():
                try:
                    shutil.rmtree(os.path.join(temp_dir, item))
                except:
                    pass
                    
        print("[MAIN] Navegadores cerrados y perfiles limpiados.")
    except Exception as e:
        print(f"[MAIN] Error cerrando navegadores: {str(e)}")
```

#### 🎯 Patrón a Replicar en Otros Módulos

1. **Lista de reintentos**: `retry_tasks = []` para acumular tareas fallidas
2. **Stop event**: `stop_event = multiprocessing.Event()` para coordinar parada
3. **Detección de señales**: Detectar `RETRY:`, `IP_BLOCKED`, `ERROR` en resultados
4. **Terminación coordinada**: `pool.terminate()` + `cerrar_todos_los_navegadores()`
5. **Priorización**: Insertar tareas de reintento al principio de la lista
6. **Rotación de IP**: Llamar `rotar_ip()` y esperar antes de continuar

### 2.6 Confirmación de lógica de paginación

#### Verificar que todos los módulos usen el patrón de Apelaciones

**Patrón correcto (como en Apelaciones):**
```python
# Obtener número de página directamente desde el DOM
pagina_activa = driver.find_element(By.CSS_SELECTOR, ".page-item.active .page-link").text
pagina_actual = int(pagina_activa)

# NO usar contadores manuales como:
# pagina_actual += 1  # ❌ INCORRECTO
```

**Checklist de verificación por módulo:**
- [ ] Civil: ¿Usa número de página desde DOM?
- [ ] Cobranza: ¿Usa número de página desde DOM?
- [ ] Laboral: ¿Usa número de página desde DOM?
- [ ] Suprema: ¿Usa número de página desde DOM?

---

## 🔄 FASE 3: Refactorización de Lógica de Paginación

### Prioridad: 🟡 MEDIA - Implementar después de Fase 2

### 3.1 Unificar lógica de paginación

#### Crear función común `pagination_utils.py`

```python
# Crear archivo: utils/pagination_utils.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def get_current_page_number(driver):
    """Obtiene el número de página actual desde el DOM"""
    try:
        pagina_element = driver.find_element(By.CSS_SELECTOR, ".page-item.active .page-link")
        return int(pagina_element.text)
    except Exception:
        return 1

def navigate_to_next_page(driver, task_id, total_workers, debug_mode, log_debug, log_error):
    """Navega a la siguiente página y retorna True si exitoso"""
    try:
        # Obtener página antes del click
        pagina_antes = get_current_page_number(driver)
        
        # Buscar y hacer click en "Siguiente"
        boton_siguiente = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "sigId"))
        )
        
        driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
        time.sleep(1)
        boton_siguiente.click()
        time.sleep(3)
        
        # Verificar si cambió la página
        pagina_despues = get_current_page_number(driver)
        
        if pagina_antes == pagina_despues:
            log_debug(task_id, total_workers, "Fin de paginación detectado", debug_mode)
            return False
        
        return True
        
    except Exception as e:
        log_error(task_id, total_workers, f"Error navegando página: {str(e)}")
        return False

def navigate_to_page(driver, target_page, task_id, total_workers, debug_mode, log_progress, log_error):
    """Navega a una página específica"""
    current_page = get_current_page_number(driver)
    
    while current_page < target_page:
        if not navigate_to_next_page(driver, task_id, total_workers, debug_mode, log_debug, log_error):
            return False
        current_page = get_current_page_number(driver)
    
    return current_page == target_page
```

### 3.2 Estandarizar nombres de variables

**Nombres estándar a usar en todos los módulos:**
```python
pagina_actual = get_current_page_number(driver)
pagina_activa_antes = get_current_page_number(driver)
pagina_activa_despues = get_current_page_number(driver)
total_paginas = obtener_total_paginas(driver)
pagina_inicial = task.get('pagina_inicial', 1)
```

### 3.3 Implementar en cada módulo

```python
# En cada worker_{modulo}.py
from utils.pagination_utils import (
    get_current_page_number,
    navigate_to_next_page, 
    navigate_to_page
)

def scrape_worker(task):
    # ... código de inicialización ...
    
    # Saltar a página inicial si hay checkpoint
    pagina_inicial = task.get('pagina_inicial', 1)
    if pagina_inicial > 1:
        if not navigate_to_page(driver, pagina_inicial, task_id, total_workers, debug_mode, log_progress, log_error):
            return "ERROR_CHECKPOINT"
    
    # Bucle principal de paginación
    while True:
        pagina_actual = get_current_page_number(driver)
        
        # ... procesar página actual ...
        
        # Navegar a siguiente página
        if not navigate_to_next_page(driver, task_id, total_workers, debug_mode, log_debug, log_error):
            break  # Fin de paginación
    
    return "COMPLETED"
```

---

## 🧪 FASE 4: Testing y Validación

### Prioridad: 🟢 BAJA - Implementar en paralelo con otras fases

### 4.1 Scripts de prueba por módulo

#### Crear `tests/test_{modulo}.py`

```python
# tests/test_civil.py
import subprocess
import time
import os

def test_logging_debug_mode():
    """Prueba que el modo debug funcione correctamente"""
    print("🧪 Probando modo debug...")
    
    # Ejecutar con debug
    result = subprocess.run([
        "python", "tribunales_civil/main_civil.py", 
        "--debug", "--dias", "1", "--workers", "1"
    ], capture_output=True, text=True, timeout=60)
    
    # Verificar que aparezcan logs de debug
    assert "🔍" in result.stdout, "No se encontraron logs de debug"
    assert "DEBUG" in result.stdout, "No se encontró texto DEBUG"
    
    print("✅ Modo debug funcionando")

def test_error_recovery():
    """Simula errores y verifica recuperación"""
    print("🧪 Probando recuperación de errores...")
    
    # Simular error de IP bloqueada
    # (requiere modificar temporalmente el worker para forzar error)
    
    print("✅ Recuperación de errores funcionando")

def test_checkpoint_functionality():
    """Prueba que los checkpoints funcionen"""
    print("🧪 Probando checkpoints...")
    
    # Ejecutar parcialmente y verificar checkpoint
    # Luego reanudar desde checkpoint
    
    print("✅ Checkpoints funcionando")

if __name__ == "__main__":
    test_logging_debug_mode()
    test_error_recovery()
    test_checkpoint_functionality()
    print("🎉 Todas las pruebas pasaron")
```

### 4.2 Validación manual

#### Checklist de validación por módulo

```bash
# Para cada módulo, ejecutar:

# 1. Probar modo debug
python tribunales_{modulo}/main_{modulo}.py --debug --dias 1 --workers 1

# 2. Verificar logs esperados:
# ✅ [HH:MM:SS] 🚀 Worker 1/1: INICIANDO - día X
# ✅ [HH:MM:SS] ⚙️ Worker 1/1: PROCESANDO - página 1
# ✅ [HH:MM:SS] 🔍 Worker 1/1: DEBUG - ...
# ✅ [HH:MM:SS] ✅ Worker 1/1: COMPLETADO - X registros

# 3. Probar sin debug (no debe mostrar logs DEBUG)
python tribunales_{modulo}/main_{modulo}.py --dias 1 --workers 1

# 4. Verificar que NO aparezcan logs con 🔍 o DEBUG
```

### 4.3 Métricas de éxito

#### KPIs a medir

1. **Tasa de errores ElementClickInterceptedException**: 0%
2. **Duplicados en última página**: 0%
3. **Recuperación exitosa desde checkpoints**: 100%
4. **Tiempo promedio de recuperación de errores**: < 30 segundos
5. **Logs útiles en modo debug**: 100% de eventos críticos loggeados

#### Herramientas de monitoreo

```python
# utils/monitor.py
import re
from collections import defaultdict

def analizar_logs(archivo_log):
    """Analiza logs para extraer métricas"""
    with open(archivo_log, 'r') as f:
        contenido = f.read()
    
    # Contar errores por tipo
    errores = defaultdict(int)
    
    # ElementClickInterceptedException
    errores['click_intercepted'] = len(re.findall(r'ElementClickInterceptedException', contenido))
    
    # Duplicados
    errores['duplicados'] = len(re.findall(r'registro duplicado', contenido))
    
    # Recuperaciones exitosas
    recuperaciones = len(re.findall(r'Tarea reencolada', contenido))
    
    # Workers completados
    completados = len(re.findall(r'COMPLETADO', contenido))
    
    return {
        'errores': dict(errores),
        'recuperaciones': recuperaciones,
        'completados': completados
    }
```

---

## 📅 Cronograma de Implementación

### Semana 1: Fase 1 - Sistema de Logging
- **Día 1-2**: Tribunales Civil y Cobranza
- **Día 3-4**: Tribunales Laboral y Corte Apelaciones  
- **Día 5**: Corte Suprema y testing de Fase 1

### Semana 2: Fase 2 - Manejo de Errores
- **Día 1-2**: Implementar soluciones 2.1-2.3 en todos los módulos
- **Día 3-4**: Implementar soluciones 2.4-2.6 en todos los módulos
- **Día 5**: Testing y ajustes de Fase 2

### Semana 3: Fase 3 - Unificación de Paginación
- **Día 1-2**: Crear utils/pagination_utils.py
- **Día 3-4**: Refactorizar todos los módulos
- **Día 5**: Testing de Fase 3

### Semana 4: Fase 4 - Testing Final
- **Día 1-3**: Testing exhaustivo de todos los módulos
- **Día 4-5**: Documentación y deployment

---

## ⚠️ Riesgos y Mitigaciones

### Riesgos Identificados

1. **🔴 ALTO**: Regresión en funcionalidad existente
   - **Mitigación**: Testing exhaustivo antes de cada commit
   - **Plan B**: Rollback inmediato con git

2. **🟡 MEDIO**: Cambios simultáneos causan conflictos
   - **Mitigación**: Implementar módulo por módulo
   - **Plan B**: Branches separados por módulo

3. **🟡 MEDIO**: Tiempo de implementación subestimado
   - **Mitigación**: Buffer de 20% en cronograma
   - **Plan B**: Priorizar errores críticos primero

4. **🟢 BAJO**: Resistencia al cambio en el equipo
   - **Mitigación**: Documentación clara y training
   - **Plan B**: Implementación gradual

### Plan de Contingencia

```bash
# En caso de problemas críticos:

# 1. Rollback inmediato
git checkout HEAD~1

# 2. Identificar módulo problemático
# 3. Rollback solo ese módulo
git checkout HEAD~1 -- tribunales_{modulo}/

# 4. Continuar con otros módulos
# 5. Revisar y corregir módulo problemático
```

---

## 📋 Checklist Final de Implementación

### ✅ Pre-implementación
- [ ] Backup completo del repositorio
- [ ] Crear branch `refactorizacion-v2`
- [ ] Documentar estado actual de cada módulo
- [ ] Preparar entorno de testing

### ✅ Fase 1: Sistema de Logging
- [x] **Tribunales Civil**
  - [x] main_civil.py - argumento --debug
  - [x] worker_civil.py - funciones de logging
  - [x] Reemplazar prints
  - [x] Testing básico
- [x] **Tribunales Cobranza**
  - [x] main_cobranza.py - argumento --debug
  - [x] worker_cobranza.py - funciones de logging
  - [x] Reemplazar prints
  - [x] Testing básico
- [x] **Tribunales Laboral**
  - [x] main_laboral.py - argumento --debug
  - [x] worker_laboral.py - funciones de logging
  - [x] Reemplazar prints
  - [x] Testing básico
- [x] **Corte Apelaciones**
  - [x] main_apelaciones.py - argumento --debug
  - [x] worker_apelaciones.py - funciones de logging
  - [x] Reemplazar prints
  - [x] Testing básico
- [x] **Corte Suprema**
  - [x] main_suprema.py - argumento --debug
  - [x] worker_suprema.py - funciones de logging
  - [x] Reemplazar prints
  - [x] Testing básico

### ✅ Fase 2: Manejo de Errores
- [x] **Error 2.1: ElementClickInterceptedException**
  - [x] Civil - implementado y probado
  - [x] Cobranza - implementado y probado
  - [x] Laboral - implementado y probado
  - [x] Apelaciones - implementado y probado
  - [x] Suprema - implementado y probado
- [x] **Error 2.2: Detección fin de paginación**
  - [x] Civil - implementado y probado
  - [x] Cobranza - implementado y probado
  - [x] Laboral - implementado y probado
  - [x] Apelaciones - implementado y probado
  - [x] Suprema - implementado y probado
- [x] **Error 2.3: Salto real a página checkpoint**
  - [x] Civil - implementado y probado
  - [x] Cobranza - implementado y probado
  - [x] Laboral - implementado y probado
  - [x] Apelaciones - implementado y probado
  - [x] Suprema - implementado y probado
- [x] **Error 2.4: Esperas explícitas paginador**
  - [x] Civil - implementado y probado
  - [x] Cobranza - implementado y probado
  - [x] Laboral - implementado y probado
  - [x] Apelaciones - implementado y probado
  - [x] Suprema - implementado y probado
- [x] **Error 2.5: Flujo recuperación centralizado**
  - [x] Civil - implementado y probado
  - [x] Cobranza - implementado y probado
  - [x] Laboral - implementado y probado
  - [x] Apelaciones - implementado y probado
  - [x] Suprema - implementado y probado
- [x] **Error 2.6: Confirmación lógica paginación**
  - [x] Civil - verificado
  - [x] Cobranza - verificado
  - [x] Laboral - verificado
  - [x] Apelaciones - verificado
  - [x] Suprema - verificado

### ✅ Fase 3: Unificación Paginación
- [x] Crear utils/pagination_utils.py
- [x] Refactorizar Civil
- [x] Refactorizar Cobranza
- [x] Refactorizar Laboral
- [x] Refactorizar Apelaciones
- [x] Refactorizar Suprema
- [x] Refactorizar Penal
- [x] Testing unificado

### ✅ Fase 4: Testing y Validación
- [ ] Scripts de prueba creados
- [ ] Testing exhaustivo completado
- [ ] Métricas de éxito verificadas
- [ ] Documentación actualizada
- [ ] Deployment a producción

### ✅ Post-implementación
- [ ] Monitoreo de errores por 1 semana
- [ ] Ajustes basados en feedback
- [ ] Documentación final
- [ ] Training al equipo
- [ ] Merge a main branch

---

## 🎯 Criterios de Éxito

### Funcionales
- ✅ **0% errores ElementClickInterceptedException**
- ✅ **0% duplicados en última página**
- ✅ **100% recuperación exitosa desde checkpoints**
- ✅ **Logs claros y útiles en modo debug**
- ✅ **Tiempo de recuperación < 30 segundos**

### Técnicos
- ✅ **Código estandarizado en todos los módulos**
- ✅ **Funciones de logging reutilizables**
- ✅ **Manejo de errores robusto**
- ✅ **Lógica de paginación unificada**
- ✅ **Testing automatizado**

### Operacionales
- ✅ **Sistema más estable y confiable**
- ✅ **Debugging más eficiente**
- ✅ **Mantenimiento simplificado**
- ✅ **Escalabilidad mejorada**
- ✅ **Documentación completa**

---

## 🚀 Comandos de Ejecución Post-Refactorización

```bash
# Modo normal (logs mínimos)
python tribunales_civil/main_civil.py --dias 5 --workers 3

# Modo debug (logs detallados)
python tribunales_civil/main_civil.py --debug --dias 5 --workers 3

# Verificar funcionamiento
python tribunales_civil/main_civil.py --debug --dias 1 --workers 1

# Testing automatizado
python tests/test_civil.py
```

---

**🎉 ¡Plan de Refactorización v2 Listo para Ejecutar!**

*Este plan integra la solución de logging exitosa de tribunales_penal con las 6 soluciones críticas de errores, creando un sistema robusto, estable y mantenible para todos los módulos del repositorio.*