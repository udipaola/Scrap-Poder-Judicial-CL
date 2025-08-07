# 📊 Ejemplos de Registros en BD por Competencia

## 🔍 Campos que Necesitan Depuración

### ⚠️ **PROBLEMAS IDENTIFICADOS:**

1. **Campo DOCUMENTO:** Algunos registros tienen RUTs inválidos o vacíos
2. **Campo NOMBRE:** Algunos nombres tienen caracteres especiales o están mal formateados
3. **Campo CARGO:** Abreviaciones inconsistentes (DDO., AB.DTE, AP.DTE, etc.)
4. **Datos duplicados:** En observaciones hay información repetida
5. **Fechas:** Múltiples formatos de fecha
6. **Campos vacíos:** Algunos campos críticos están vacíos

---

## 📋 **COMPETENCIA CIVIL**

### Registro Original (CSV):
```
NOMBRE: CAYETANO EMILIO PIZARRO ARAYA
DOCUMENTO: 7769127-8
CARGO: DDO.
INSTITUCION: 3º Juzgado de Letras de Calama
OBSERVACIONES: Rol: C-2414-2021 | Fecha: 30/09/2021 | Caratulado: PROMOTORA CMR FALABELLA S.A./PIZARRO | Tribunal: 3º Juzgado de Letras de Calama
```

### Registro en BD (Después del Parsing):
```sql
INSERT INTO chile.causas_judiciales VALUES (
    cargo = 'DDO.',                                    -- ⚠️ DEPURAR: Expandir abreviaciones
    denominacion = 'CAYETANO EMILIO PIZARRO ARAYA',    -- ✅ OK
    observaciones = 'Rol: C-2414-2021 | Fecha: 30/09/2021 | Caratulado: PROMOTORA CMR FALABELLA S.A./PIZARRO | Tribunal: 3º Juzgado de Letras de Calama',
    causa = NULL,
    expediente = NULL,
    id_tributaria = 7769127,                           -- ✅ Extraído del RUT
    verificador = '8',                                 -- ✅ Extraído del RUT
    codigo = [AUTO_INCREMENT],
    fecha_novedad = '2024-01-15',                      -- Fecha de procesamiento
    fuente = 'scraping_poder_judicial',
    rit = NULL,                                        -- ⚠️ Civil no usa RIT
    ruc = NULL,                                        -- ⚠️ Civil no usa RUC
    tribunal = '3º Juzgado de Letras de Calama',       -- ✅ Parseado de observaciones
    caratulado = 'PROMOTORA CMR FALABELLA S.A./PIZARRO', -- ✅ Parseado
    rol = 'C-2414-2021',                              -- ✅ Parseado
    fecha_ingreso = '2021-09-30',                     -- ✅ Parseado y normalizado
    estado_causa = NULL,                              -- ⚠️ Civil no incluye estado
    fecha_ubicacion = NULL,
    ubicacion = NULL,
    competencia = 'civil',                            -- ✅ Detectado automáticamente
    nombre = 'CAYETANO EMILIO PIZARRO ARAYA',         -- ✅ OK
    documento = '7769127-8',                          -- ✅ OK
    institucion = '3º Juzgado de Letras de Calama',   -- ✅ OK
    rol_causa = 'C-2414-2021',                        -- ✅ Duplicado de rol
    
    -- NUEVOS CAMPOS:
    fuente_competencia = 'civil',                     -- ✅ NUEVO
    etapa = NULL,                                     -- Civil no incluye etapa
    forma_inicio = NULL,                              -- Civil no incluye forma_inicio
    procedimiento = NULL,                             -- Civil no incluye procedimiento
    recurso = NULL                                    -- Civil no incluye recurso
);
```

---

## ⚖️ **COMPETENCIA COBRANZA**

### Registro Original (CSV):
```
NOMBRE: SOCIEDAD ADMINISTRADORA DE FONDOS DE CESANTIA DE CHILE II S.A.
DOCUMENTO: 76237243-6
CARGO: DTE.
INSTITUCION: 1º Juzgado de Letras de los Andes
OBSERVACIONES: RIT: P-296-2021 | Tribunal: 1º Juzgado de Letras de los Andes | Caratulado: ADM. DE FONDOS DE CESANTIA CHILE II S.A. CON M Y INGEN | Fecha Ingreso: 21/12/2021 | Estado Procesal: Concluido | RIT: P-296-2021 | Fecha Ing.: 21/12/2021 | RUC: 21- 3-0262173-7 | Est. Adm.: Sin archivar | Proc.: Ejecutivo Previsional | Forma Inicio.: Demanda | Estado Proc.: Concluido | Etapa: Terminada | Titulo Ejec.:  | Juez Asignado: FERNANDO MARCOS ALVARADO PEÑA | Tribunal: 1º Juzgado de Letras de los Andes
```

### Registro en BD (Después del Parsing):
```sql
INSERT INTO chile.causas_judiciales VALUES (
    cargo = 'DTE.',                                   -- ⚠️ DEPURAR: Expandir a "DEMANDANTE"
    denominacion = 'SOCIEDAD ADMINISTRADORA DE FONDOS DE CESANTIA DE CHILE II S.A.',
    observaciones = '[OBSERVACIONES COMPLETAS]',
    causa = NULL,
    expediente = NULL,
    id_tributaria = 76237243,
    verificador = '6',
    codigo = [AUTO_INCREMENT],
    fecha_novedad = '2024-01-15',
    fuente = 'scraping_poder_judicial',
    rit = 'P-296-2021',                              -- ✅ Parseado
    ruc = '21-3-0262173-7',                          -- ✅ Parseado y limpiado
    tribunal = '1º Juzgado de Letras de los Andes',  -- ✅ Parseado
    caratulado = 'ADM. DE FONDOS DE CESANTIA CHILE II S.A. CON M Y INGEN', -- ✅ Parseado
    rol = NULL,                                      -- Cobranza usa RIT, no ROL
    fecha_ingreso = '2021-12-21',                    -- ✅ Parseado y normalizado
    estado_causa = 'Concluido',                      -- ✅ Parseado
    fecha_ubicacion = NULL,
    ubicacion = NULL,
    competencia = 'cobranza',
    nombre = 'SOCIEDAD ADMINISTRADORA DE FONDOS DE CESANTIA DE CHILE II S.A.',
    documento = '76237243-6',
    institucion = '1º Juzgado de Letras de los Andes',
    rol_causa = 'P-296-2021',                        -- Usa RIT como rol_causa
    
    -- NUEVOS CAMPOS:
    fuente_competencia = 'cobranza',                 -- ✅ NUEVO
    etapa = 'Terminada',                             -- ✅ Parseado
    forma_inicio = 'Demanda',                        -- ✅ Parseado
    procedimiento = 'Ejecutivo Previsional',         -- ✅ Parseado
    recurso = NULL                                   -- Cobranza no usa recurso
);
```

---

## 🚔 **COMPETENCIA PENAL**

### Registro Original (CSV):
```
NOMBRE: CRISTIAN MARCELO CHÁVEZ PULGAR
CARGO: Denunciado.
INSTITUCION: [VACÍO]
OBSERVACIONES: RIT:  | RUC:  | Tribunal:  | Caratulado:  | Fecha Ingreso:  | Estado Causa:  | Situación: Denunciado. | RIT: Ordinaria-14-2021 | RUC: 2001222728-1 | Fecha Ingreso: 06/01/2021 | Estado Actual: Concluida. | Etapa: Inicio de la acción. | Forma Inicio: Denuncia | Caratulado: MARIETA DEL PILAR MEDINA ZAMBRANO C/ CRISTIAN MARCELO CHÁVEZ PULGAR | Tribunal: Juzgado de Letras y Garantía de Curanilahue | Tribunal Origen: Juzgado de Letras y Garantía de Curanilahue
```

### Registro en BD (Después del Parsing):
```sql
INSERT INTO chile.causas_judiciales VALUES (
    cargo = 'Denunciado',                            -- ⚠️ DEPURAR: Estandarizar cargos penales
    denominacion = 'CRISTIAN MARCELO CHÁVEZ PULGAR',
    observaciones = '[OBSERVACIONES COMPLETAS]',
    causa = NULL,
    expediente = NULL,
    id_tributaria = NULL,                            -- ⚠️ PROBLEMA: No hay documento
    verificador = NULL,
    codigo = [AUTO_INCREMENT],
    fecha_novedad = '2024-01-15',
    fuente = 'scraping_poder_judicial',
    rit = 'Ordinaria-14-2021',                       -- ✅ Parseado (segundo valor)
    ruc = '2001222728-1',                            -- ✅ Parseado (segundo valor)
    tribunal = 'Juzgado de Letras y Garantía de Curanilahue', -- ✅ Parseado
    caratulado = 'MARIETA DEL PILAR MEDINA ZAMBRANO C/ CRISTIAN MARCELO CHÁVEZ PULGAR', -- ✅ Parseado
    rol = NULL,                                      -- Penal usa RIT
    fecha_ingreso = '2021-01-06',                    -- ✅ Parseado y normalizado
    estado_causa = 'Concluida',                      -- ✅ Parseado
    fecha_ubicacion = NULL,
    ubicacion = NULL,
    competencia = 'penal',
    nombre = 'CRISTIAN MARCELO CHÁVEZ PULGAR',
    documento = NULL,                                -- ⚠️ PROBLEMA: Campo vacío
    institucion = 'Juzgado de Letras y Garantía de Curanilahue', -- ✅ Parseado de tribunal
    rol_causa = 'Ordinaria-14-2021',
    
    -- NUEVOS CAMPOS:
    fuente_competencia = 'penal',                    -- ✅ NUEVO
    etapa = 'Inicio de la acción',                   -- ✅ Parseado
    forma_inicio = 'Denuncia',                       -- ✅ Parseado
    procedimiento = NULL,                            -- Penal no especifica procedimiento
    recurso = NULL                                   -- Penal no usa recurso
);
```

---

## 🏛️ **COMPETENCIA SUPREMA**

### Registro Original (CSV):
```
OBSERVACIONES: Rol: 12345-2023 | Recurso: Casación | Ingreso: 15/07/2023 | Estado: En tramitación
```

### Registro en BD (Después del Parsing):
```sql
INSERT INTO chile.causas_judiciales VALUES (
    -- [campos básicos...]
    rit = NULL,                                      -- Suprema no usa RIT
    ruc = NULL,                                      -- Suprema no usa RUC
    tribunal = 'Corte Suprema',                      -- ✅ Inferido
    caratulado = NULL,                               -- ⚠️ Suprema a veces no incluye caratulado
    rol = '12345-2023',                              -- ✅ Parseado
    fecha_ingreso = '2023-07-15',                    -- ✅ Parseado y normalizado
    estado_causa = 'En tramitación',                 -- ✅ Parseado
    competencia = 'suprema',
    
    -- NUEVOS CAMPOS:
    fuente_competencia = 'suprema',                  -- ✅ NUEVO
    etapa = NULL,                                    -- Suprema no especifica etapa
    forma_inicio = NULL,                             -- Suprema no especifica forma_inicio
    procedimiento = NULL,                            -- Suprema no especifica procedimiento
    recurso = 'Casación'                             -- ✅ Parseado - CAMPO ESPECÍFICO DE SUPREMA
);
```

---

## 🛠️ **CAMPOS QUE NECESITAN DEPURACIÓN**

### 1. **Campo CARGO - Expandir Abreviaciones:**
```sql
-- Crear tabla de mapeo de cargos
UPDATE chile.causas_judiciales SET cargo = 
    CASE 
        WHEN cargo = 'DDO.' THEN 'DEMANDADO'
        WHEN cargo = 'DTE.' THEN 'DEMANDANTE'
        WHEN cargo = 'AB.DTE' THEN 'ABOGADO DEMANDANTE'
        WHEN cargo = 'AP.DTE' THEN 'APODERADO DEMANDANTE'
        WHEN cargo = 'AB.DDO' THEN 'ABOGADO DEMANDADO'
        WHEN cargo = 'AP.DDO' THEN 'APODERADO DEMANDADO'
        WHEN cargo = 'Denunciado.' THEN 'DENUNCIADO'
        WHEN cargo = 'Denunciante.' THEN 'DENUNCIANTE'
        WHEN cargo = 'Fiscal.' THEN 'FISCAL'
        WHEN cargo = 'Colaborador.' THEN 'COLABORADOR'
        ELSE cargo
    END;
```

### 2. **Campo RUC - Limpiar Formato:**
```sql
-- Limpiar espacios y guiones inconsistentes en RUC
UPDATE chile.causas_judiciales SET ruc = 
    REPLACE(REPLACE(ruc, ' ', ''), '--', '-')
WHERE ruc IS NOT NULL;
```

### 3. **Campo DOCUMENTO - Validar RUTs:**
```sql
-- Identificar RUTs inválidos para revisión manual
SELECT documento, COUNT(*) 
FROM chile.causas_judiciales 
WHERE documento IS NOT NULL 
AND (LENGTH(documento) < 8 OR LENGTH(documento) > 12)
GROUP BY documento;
```

### 4. **Campo NOMBRE - Limpiar Caracteres Especiales:**
```sql
-- Limpiar nombres con caracteres especiales
UPDATE chile.causas_judiciales SET nombre = 
    UPPER(TRIM(REGEXP_REPLACE(nombre, '[^A-Za-z0-9\s\.]', '', 'g')))
WHERE nombre IS NOT NULL;
```

---

## 📈 **Estadísticas Esperadas por Competencia**

| Competencia | Campos Más Poblados | Campos Específicos | Calidad Esperada |
|-------------|--------------------|--------------------|------------------|
| **Civil** | rol, tribunal, caratulado, fecha_ingreso | ninguno específico | 85% |
| **Cobranza** | rit, ruc, tribunal, estado_causa, etapa | procedimiento, forma_inicio | 90% |
| **Penal** | rit, ruc, tribunal, estado_causa, etapa | forma_inicio | 80% |
| **Laboral** | rit, tribunal, caratulado, estado_causa | procedimiento, forma_inicio | 85% |
| **Suprema** | rol, estado_causa, recurso | recurso | 75% |
| **Apelaciones** | rol, tribunal, caratulado, ubicacion | fecha_ubicacion | 80% |

---

## ⚠️ **RECOMENDACIONES DE DEPURACIÓN**

1. **Ejecutar script SQL de campos faltantes PRIMERO**
2. **Ejecutar script de depuración de cargos**
3. **Validar RUTs y documentos**
4. **Limpiar nombres y caracteres especiales**
5. **Verificar fechas en formato correcto**
6. **Revisar registros con campos críticos vacíos**