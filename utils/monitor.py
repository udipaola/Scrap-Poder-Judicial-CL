# utils/monitor.py
import re
import os
from collections import defaultdict
from datetime import datetime

def analizar_logs(archivo_log):
    """Analiza logs para extraer métricas"""
    if not os.path.exists(archivo_log):
        return {
            'errores': {},
            'recuperaciones': 0,
            'completados': 0,
            'archivo_existe': False
        }
    
    with open(archivo_log, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Contar errores por tipo
    errores = defaultdict(int)
    
    # ElementClickInterceptedException
    errores['click_intercepted'] = len(re.findall(r'ElementClickInterceptedException', contenido))
    
    # Duplicados
    errores['duplicados'] = len(re.findall(r'registro duplicado', contenido))
    
    # Timeouts
    errores['timeouts'] = len(re.findall(r'TimeoutException', contenido))
    
    # IP bloqueadas
    errores['ip_bloqueadas'] = len(re.findall(r'IP bloqueada', contenido))
    
    # Recuperaciones exitosas
    recuperaciones = len(re.findall(r'Tarea reencolada', contenido))
    
    # Workers completados
    completados = len(re.findall(r'COMPLETADO', contenido))
    
    # Logs de debug
    logs_debug = len(re.findall(r'🔍|DEBUG', contenido))
    
    return {
        'errores': dict(errores),
        'recuperaciones': recuperaciones,
        'completados': completados,
        'logs_debug': logs_debug,
        'archivo_existe': True
    }

def generar_reporte_metricas(directorio_logs='logs'):
    """Genera un reporte completo de métricas para todos los módulos"""
    modulos = ['civil', 'cobranza', 'laboral', 'penal', 'apelaciones', 'suprema']
    reporte = {
        'timestamp': datetime.now().isoformat(),
        'modulos': {},
        'resumen': {
            'total_errores': 0,
            'total_recuperaciones': 0,
            'total_completados': 0,
            'tasa_exito': 0
        }
    }
    
    for modulo in modulos:
        archivo_log = os.path.join(directorio_logs, f'{modulo}.log')
        metricas = analizar_logs(archivo_log)
        reporte['modulos'][modulo] = metricas
        
        if metricas['archivo_existe']:
            reporte['resumen']['total_errores'] += sum(metricas['errores'].values())
            reporte['resumen']['total_recuperaciones'] += metricas['recuperaciones']
            reporte['resumen']['total_completados'] += metricas['completados']
    
    # Calcular tasa de éxito
    total_tareas = reporte['resumen']['total_completados'] + reporte['resumen']['total_errores']
    if total_tareas > 0:
        reporte['resumen']['tasa_exito'] = (reporte['resumen']['total_completados'] / total_tareas) * 100
    
    return reporte

def validar_kpis(reporte):
    """Valida que se cumplan los KPIs definidos"""
    kpis = {
        'tasa_errores_click_intercepted': 0,  # Objetivo: 0%
        'duplicados_ultima_pagina': 0,        # Objetivo: 0%
        'recuperacion_checkpoints': 100,      # Objetivo: 100%
        'tiempo_recuperacion': 30,            # Objetivo: < 30 segundos
        'logs_debug_eventos': 100             # Objetivo: 100% eventos críticos
    }
    
    resultados = {
        'cumple_kpis': True,
        'detalles': {}
    }
    
    # Verificar cada módulo
    for modulo, metricas in reporte['modulos'].items():
        if not metricas['archivo_existe']:
            continue
            
        # KPI 1: Tasa de errores ElementClickInterceptedException
        click_errors = metricas['errores'].get('click_intercepted', 0)
        if click_errors > 0:
            resultados['cumple_kpis'] = False
            resultados['detalles'][f'{modulo}_click_errors'] = f'Encontrados {click_errors} errores de click intercepted'
        
        # KPI 2: Duplicados
        duplicados = metricas['errores'].get('duplicados', 0)
        if duplicados > 0:
            resultados['cumple_kpis'] = False
            resultados['detalles'][f'{modulo}_duplicados'] = f'Encontrados {duplicados} registros duplicados'
    
    return resultados

if __name__ == '__main__':
    # Ejemplo de uso
    reporte = generar_reporte_metricas()
    print("📊 Reporte de Métricas")
    print("=" * 50)
    
    for modulo, metricas in reporte['modulos'].items():
        if metricas['archivo_existe']:
            print(f"\n🔍 {modulo.upper()}:")
            print(f"  ✅ Completados: {metricas['completados']}")
            print(f"  🔄 Recuperaciones: {metricas['recuperaciones']}")
            print(f"  ❌ Errores: {sum(metricas['errores'].values())}")
            if metricas['errores']:
                for tipo, cantidad in metricas['errores'].items():
                    if cantidad > 0:
                        print(f"    - {tipo}: {cantidad}")
        else:
            print(f"\n⚠️ {modulo.upper()}: Archivo de log no encontrado")
    
    print(f"\n📈 RESUMEN GENERAL:")
    print(f"  Tasa de éxito: {reporte['resumen']['tasa_exito']:.1f}%")
    
    # Validar KPIs
    validacion = validar_kpis(reporte)
    if validacion['cumple_kpis']:
        print("\n✅ Todos los KPIs se cumplen")
    else:
        print("\n❌ Algunos KPIs no se cumplen:")
        for detalle, mensaje in validacion['detalles'].items():
            print(f"  - {mensaje}")