
-- 2. Agregar columnas faltantes de forma idempotente
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='competencia') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN competencia TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='fecha_novedad') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN fecha_novedad DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='fuente') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN fuente TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='rol') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN rol TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='rit') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN rit TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='ruc') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN ruc TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='caratulado') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN caratulado TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='fecha_ingreso') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN fecha_ingreso DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='estado_causa') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN estado_causa TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='fecha_ubicacion') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN fecha_ubicacion DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='ubicacion') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN ubicacion TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='nombre') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN nombre TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='documento') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN documento TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='institucion') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN institucion TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='rol_causa') THEN
        ALTER TABLE chile.causas_judiciales ADD COLUMN rol_causa TEXT;
    END IF;
END$$;

-- 3. Eliminar columnas obsoletas de forma segura (ajustar nombres según necesidad)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='fuente_anterior') THEN
        ALTER TABLE chile.causas_judiciales DROP COLUMN fuente_anterior;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chile' AND table_name='causas_judiciales' AND column_name='estado') THEN
        ALTER TABLE chile.causas_judiciales DROP COLUMN estado;
    END IF;
END$$;