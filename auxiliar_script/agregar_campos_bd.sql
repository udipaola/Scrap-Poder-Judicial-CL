-- Script para agregar campos faltantes a la tabla chile.causas_judiciales
-- Ejecutar ANTES de usar el script mejorado ejecutar_envio.py

-- 1. Agregar campo fuente_competencia (CRÍTICO)
-- Este campo identifica de qué competencia específica viene cada registro
ALTER TABLE chile.causas_judiciales 
ADD COLUMN IF NOT EXISTS fuente_competencia TEXT;

-- 2. Agregar campo etapa
-- Almacena la etapa procesal extraída de observaciones
ALTER TABLE chile.causas_judiciales 
ADD COLUMN IF NOT EXISTS etapa TEXT;

-- 3. Agregar campo forma_inicio
-- Almacena cómo se inició el proceso (especialmente para cobranza, penal, laboral)
ALTER TABLE chile.causas_judiciales 
ADD COLUMN IF NOT EXISTS forma_inicio TEXT;

-- 4. Agregar campo procedimiento
-- Almacena el tipo de procedimiento (especialmente para cobranza y laboral)
ALTER TABLE chile.causas_judiciales 
ADD COLUMN IF NOT EXISTS procedimiento TEXT;

-- 5. Agregar campo recurso
-- Almacena el tipo de recurso (especialmente para corte suprema)
ALTER TABLE chile.causas_judiciales 
ADD COLUMN IF NOT EXISTS recurso TEXT;

-- Verificar que los campos se agregaron correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'chile' 
AND table_name = 'causas_judiciales' 
AND column_name IN ('fuente_competencia', 'etapa', 'forma_inicio', 'procedimiento', 'recurso')
ORDER BY column_name;

-- Comentarios sobre los campos:
/*
fuente_competencia: Identifica la competencia específica (apelaciones, civil, cobranza, suprema, penal, laboral)
etapa: Etapa procesal del caso
forma_inicio: Forma en que se inició el proceso judicial
procedimiento: Tipo de procedimiento aplicado
recurso: Tipo de recurso presentado (principalmente para suprema)

Todos los campos son de tipo TEXT y permiten NULL porque:
- No todos los registros tendrán todos los campos
- Depende de la competencia específica
- Algunos campos son específicos de ciertas competencias
*/