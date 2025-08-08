-- Script de Depuración de Datos para chile.causas_judiciales
-- Ejecutar DESPUÉS de insertar los datos con el script mejorado

-- =====================================================
-- 1. DEPURACIÓN DE CAMPO CARGO - Expandir Abreviaciones
-- =====================================================

UPDATE chile.causas_judiciales SET cargo = 
    CASE 
        -- Demandantes y Demandados
        WHEN UPPER(cargo) IN ('DDO.', 'DDO', 'DEMANDADO.') THEN 'DEMANDADO'
        WHEN UPPER(cargo) IN ('DTE.', 'DTE', 'DEMANDANTE.') THEN 'DEMANDANTE'
        
        -- Abogados
        WHEN UPPER(cargo) IN ('AB.DTE', 'ABOG.DTE', 'AB.DEMANDANTE') THEN 'ABOGADO DEMANDANTE'
        WHEN UPPER(cargo) IN ('AB.DDO', 'ABOG.DDO', 'AB.DEMANDADO') THEN 'ABOGADO DEMANDADO'
        WHEN UPPER(cargo) IN ('AB.', 'ABOG.', 'ABOGADO.') THEN 'ABOGADO'
        
        -- Apoderados
        WHEN UPPER(cargo) IN ('AP.DTE', 'APOD.DTE', 'AP.DEMANDANTE') THEN 'APODERADO DEMANDANTE'
        WHEN UPPER(cargo) IN ('AP.DDO', 'APOD.DDO', 'AP.DEMANDADO') THEN 'APODERADO DEMANDADO'
        WHEN UPPER(cargo) IN ('AP.', 'APOD.', 'APODERADO.') THEN 'APODERADO'
        
        -- Roles Penales
        WHEN UPPER(cargo) IN ('DENUNCIADO.', 'DENUNCIADO', 'DEN.') THEN 'DENUNCIADO'
        WHEN UPPER(cargo) IN ('DENUNCIANTE.', 'DENUNCIANTE', 'DNTE.') THEN 'DENUNCIANTE'
        WHEN UPPER(cargo) IN ('FISCAL.', 'FISCAL', 'FISC.') THEN 'FISCAL'
        WHEN UPPER(cargo) IN ('COLABORADOR.', 'COLABORADOR', 'COLAB.') THEN 'COLABORADOR'
        WHEN UPPER(cargo) IN ('IMPUTADO.', 'IMPUTADO', 'IMP.') THEN 'IMPUTADO'
        WHEN UPPER(cargo) IN ('QUERELLANTE.', 'QUERELLANTE', 'QUER.') THEN 'QUERELLANTE'
        WHEN UPPER(cargo) IN ('DEFENSOR.', 'DEFENSOR', 'DEF.') THEN 'DEFENSOR'
        
        -- Roles Laborales
        WHEN UPPER(cargo) IN ('TRABAJADOR.', 'TRABAJADOR', 'TRAB.') THEN 'TRABAJADOR'
        WHEN UPPER(cargo) IN ('EMPLEADOR.', 'EMPLEADOR', 'EMP.') THEN 'EMPLEADOR'
        
        -- Otros
        WHEN UPPER(cargo) IN ('TESTIGO.', 'TESTIGO', 'TEST.') THEN 'TESTIGO'
        WHEN UPPER(cargo) IN ('PERITO.', 'PERITO', 'PER.') THEN 'PERITO'
        WHEN UPPER(cargo) IN ('TERCERO.', 'TERCERO', 'TERC.') THEN 'TERCERO'
        
        -- Si no coincide con ninguno, mantener original pero limpiar
        ELSE UPPER(TRIM(REPLACE(cargo, '.', '')))
    END
WHERE cargo IS NOT NULL;

-- =====================================================
-- 2. DEPURACIÓN DE CAMPO RUC - Limpiar Formato
-- =====================================================

-- Limpiar espacios extra y guiones dobles en RUC
UPDATE chile.causas_judiciales SET ruc = 
    TRIM(REPLACE(REPLACE(REPLACE(ruc, '  ', ' '), ' -', '-'), '- ', '-'))
WHERE ruc IS NOT NULL AND ruc != '';

-- Limpiar RUCs que son solo espacios o guiones
UPDATE chile.causas_judiciales SET ruc = NULL 
WHERE ruc IS NOT NULL AND TRIM(REPLACE(REPLACE(ruc, '-', ''), ' ', '')) = '';

-- =====================================================
-- 3. DEPURACIÓN DE CAMPO DOCUMENTO - Validar RUTs
-- =====================================================

-- Limpiar documentos con formato inconsistente
UPDATE chile.causas_judiciales SET documento = 
    TRIM(REPLACE(documento, ' ', ''))
WHERE documento IS NOT NULL;

-- Marcar documentos sospechosos (muy cortos o muy largos)
-- Crear una columna temporal para marcar documentos a revisar
ALTER TABLE chile.causas_judiciales ADD COLUMN IF NOT EXISTS documento_revisar BOOLEAN DEFAULT FALSE;

UPDATE chile.causas_judiciales SET documento_revisar = TRUE 
WHERE documento IS NOT NULL 
AND (LENGTH(documento) < 8 OR LENGTH(documento) > 12 OR documento = '0' OR documento = 'S/I');

-- =====================================================
-- 4. DEPURACIÓN DE CAMPO NOMBRE - Limpiar Caracteres
-- =====================================================

-- Limpiar nombres: mayúsculas, quitar caracteres especiales, espacios extra
UPDATE chile.causas_judiciales SET nombre = 
    TRIM(REGEXP_REPLACE(
        UPPER(nombre), 
        '[^A-Z0-9\s\.\-]', 
        '', 
        'g'
    ))
WHERE nombre IS NOT NULL;

-- Limpiar espacios múltiples
UPDATE chile.causas_judiciales SET nombre = 
    REGEXP_REPLACE(nombre, '\s+', ' ', 'g')
WHERE nombre IS NOT NULL;

-- =====================================================
-- 5. DEPURACIÓN DE FECHAS - Validar Formatos
-- =====================================================

-- Corregir fechas con años mal interpretados (0023 -> 2023, etc.)
UPDATE chile.causas_judiciales 
SET fecha_ingreso = CASE 
    WHEN EXTRACT(YEAR FROM fecha_ingreso) BETWEEN 20 AND 99 THEN 
        (fecha_ingreso + INTERVAL '2000 years')::DATE
    WHEN EXTRACT(YEAR FROM fecha_ingreso) BETWEEN 0 AND 19 THEN 
        (fecha_ingreso + INTERVAL '2000 years')::DATE
    ELSE fecha_ingreso
END
WHERE fecha_ingreso IS NOT NULL 
  AND EXTRACT(YEAR FROM fecha_ingreso) < 100;

-- Marcar fechas sospechosas (futuras o muy antiguas)
ALTER TABLE chile.causas_judiciales ADD COLUMN IF NOT EXISTS fecha_revisar BOOLEAN DEFAULT FALSE;

UPDATE chile.causas_judiciales SET fecha_revisar = TRUE 
WHERE fecha_ingreso IS NOT NULL 
AND (fecha_ingreso > CURRENT_DATE OR fecha_ingreso < '1990-01-01');

-- =====================================================
-- 6. DEPURACIÓN DE TRIBUNALES - Estandarizar Nombres
-- =====================================================

-- Limpiar nombres de tribunales
UPDATE chile.causas_judiciales SET tribunal = 
    TRIM(REGEXP_REPLACE(tribunal, '\s+', ' ', 'g'))
WHERE tribunal IS NOT NULL;

-- Estandarizar nombres comunes de tribunales
UPDATE chile.causas_judiciales SET tribunal = 
    CASE 
        WHEN tribunal ILIKE '%juzgado de letras y garantía%' THEN 
            REGEXP_REPLACE(tribunal, 'Juzgado de Letras y Garantía', 'Juzgado de Letras y Garantía', 'i')
        WHEN tribunal ILIKE '%juzgado de letras%' THEN 
            REGEXP_REPLACE(tribunal, 'Juzgado de Letras', 'Juzgado de Letras', 'i')
        WHEN tribunal ILIKE '%corte de apelaciones%' THEN 
            REGEXP_REPLACE(tribunal, 'Corte de Apelaciones', 'Corte de Apelaciones', 'i')
        WHEN tribunal ILIKE '%corte suprema%' THEN 'Corte Suprema'
        ELSE tribunal
    END
WHERE tribunal IS NOT NULL;

-- =====================================================
-- 7. LIMPIAR CAMPOS VACÍOS - Convertir a NULL
-- =====================================================

-- Convertir strings vacíos a NULL para mejor manejo
UPDATE chile.causas_judiciales SET 
    rit = CASE WHEN TRIM(rit) = '' THEN NULL ELSE rit END,
    ruc = CASE WHEN TRIM(ruc) = '' THEN NULL ELSE ruc END,
    rol = CASE WHEN TRIM(rol) = '' THEN NULL ELSE rol END,
    caratulado = CASE WHEN TRIM(caratulado) = '' THEN NULL ELSE caratulado END,
    estado_causa = CASE WHEN TRIM(estado_causa) = '' THEN NULL ELSE estado_causa END,
    etapa = CASE WHEN TRIM(etapa) = '' THEN NULL ELSE etapa END,
    forma_inicio = CASE WHEN TRIM(forma_inicio) = '' THEN NULL ELSE forma_inicio END,
    procedimiento = CASE WHEN TRIM(procedimiento) = '' THEN NULL ELSE procedimiento END,
    recurso = CASE WHEN TRIM(recurso) = '' THEN NULL ELSE recurso END,
    ubicacion = CASE WHEN TRIM(ubicacion) = '' THEN NULL ELSE ubicacion END;

-- =====================================================
-- 8. ESTADÍSTICAS POST-DEPURACIÓN
-- =====================================================

-- Ver estadísticas de calidad de datos por competencia
SELECT 
    fuente_competencia,
    COUNT(*) as total_registros,
    COUNT(documento) as con_documento,
    COUNT(rit) as con_rit,
    COUNT(ruc) as con_ruc,
    COUNT(rol) as con_rol,
    COUNT(tribunal) as con_tribunal,
    COUNT(caratulado) as con_caratulado,
    COUNT(fecha_ingreso) as con_fecha_ingreso,
    COUNT(estado_causa) as con_estado_causa,
    SUM(CASE WHEN documento_revisar = TRUE THEN 1 ELSE 0 END) as documentos_revisar,
    SUM(CASE WHEN fecha_revisar = TRUE THEN 1 ELSE 0 END) as fechas_revisar
FROM chile.causas_judiciales 
WHERE fuente_competencia IS NOT NULL
GROUP BY fuente_competencia
ORDER BY fuente_competencia;

-- Ver registros que necesitan revisión manual
SELECT 
    'Documentos a revisar' as tipo,
    COUNT(*) as cantidad
FROM chile.causas_judiciales 
WHERE documento_revisar = TRUE

UNION ALL

SELECT 
    'Fechas a revisar' as tipo,
    COUNT(*) as cantidad
FROM chile.causas_judiciales 
WHERE fecha_revisar = TRUE;

-- =====================================================
-- 9. ÍNDICES PARA MEJORAR RENDIMIENTO
-- =====================================================

-- Crear índices en campos más consultados
CREATE INDEX IF NOT EXISTS idx_causas_fuente_competencia ON chile.causas_judiciales(fuente_competencia);
CREATE INDEX IF NOT EXISTS idx_causas_competencia ON chile.causas_judiciales(competencia);
CREATE INDEX IF NOT EXISTS idx_causas_documento ON chile.causas_judiciales(documento);
CREATE INDEX IF NOT EXISTS idx_causas_rit ON chile.causas_judiciales(rit);
CREATE INDEX IF NOT EXISTS idx_causas_ruc ON chile.causas_judiciales(ruc);
CREATE INDEX IF NOT EXISTS idx_causas_rol ON chile.causas_judiciales(rol);
CREATE INDEX IF NOT EXISTS idx_causas_fecha_ingreso ON chile.causas_judiciales(fecha_ingreso);
CREATE INDEX IF NOT EXISTS idx_causas_tribunal ON chile.causas_judiciales(tribunal);

-- =====================================================
-- 10. LIMPIEZA FINAL
-- =====================================================

-- Eliminar columnas temporales de revisión (opcional)
-- ALTER TABLE chile.causas_judiciales DROP COLUMN IF EXISTS documento_revisar;
-- ALTER TABLE chile.causas_judiciales DROP COLUMN IF EXISTS fecha_revisar;

COMMIT;