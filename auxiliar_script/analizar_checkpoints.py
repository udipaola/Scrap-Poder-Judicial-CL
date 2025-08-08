#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar checkpoints de cada competencia y calcular días restantes de procesamiento
Analiza el progreso desde 2021-01-01 hasta 2025-07-30
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import re

def generar_fechas_rango(fecha_inicio, fecha_fin):
    """Genera todas las fechas en el rango especificado"""
    fechas = []
    fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_final = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    while fecha_actual <= fecha_final:
        fechas.append(fecha_actual.strftime('%Y-%m-%d'))
        fecha_actual += timedelta(days=1)
    
    return fechas

def analizar_checkpoint_suprema(checkpoint_path):
    """Analiza checkpoint de Suprema (formato: fecha -> status)"""
    print(f"\n=== ANÁLISIS SUPREMA ===")
    print(f"Archivo: {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        print("❌ Archivo no encontrado")
        return
    
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Generar todas las fechas del rango
    todas_las_fechas = generar_fechas_rango('2021-01-01', '2025-07-30')
    fechas_completadas = set()
    
    # Identificar fechas completadas
    for fecha, info in data.items():
        if info.get('status') == 'completed':
            fechas_completadas.add(fecha)
    
    fechas_pendientes = [f for f in todas_las_fechas if f not in fechas_completadas]
    
    print(f"📊 Total de fechas en rango: {len(todas_las_fechas)}")
    print(f"✅ Fechas completadas: {len(fechas_completadas)}")
    print(f"⏳ Fechas pendientes: {len(fechas_pendientes)}")
    print(f"📈 Progreso: {len(fechas_completadas)/len(todas_las_fechas)*100:.2f}%")
    
    if fechas_pendientes:
        print(f"🔍 Primeras 10 fechas pendientes: {fechas_pendientes[:10]}")
        print(f"🔍 Últimas 10 fechas pendientes: {fechas_pendientes[-10:]}")
    
    return len(fechas_pendientes)

def analizar_checkpoint_apelaciones(checkpoint_path):
    """Analiza checkpoint de Apelaciones (formato: fecha_tribunal -> status)"""
    print(f"\n=== ANÁLISIS APELACIONES ===")
    print(f"Archivo: {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        print("❌ Archivo no encontrado")
        return
    
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extraer fechas y tribunales únicos
    fechas_por_tribunal = defaultdict(set)
    tribunales = set()
    
    for key, info in data.items():
        if info.get('status') == 'completed':
            # Formato: "2021-01-01_10"
            parts = key.split('_')
            if len(parts) >= 2:
                fecha = parts[0]
                tribunal = parts[1]
                fechas_por_tribunal[tribunal].add(fecha)
                tribunales.add(tribunal)
    
    # Generar todas las fechas del rango
    todas_las_fechas = generar_fechas_rango('2021-01-01', '2025-07-30')
    
    print(f"📊 Total de tribunales encontrados: {len(tribunales)}")
    print(f"📊 Total de fechas en rango: {len(todas_las_fechas)}")
    
    # Calcular pendientes por tribunal
    total_pendientes = 0
    tribunales_con_pendientes = 0
    
    for tribunal in sorted(tribunales):
        fechas_completadas = fechas_por_tribunal[tribunal]
        fechas_pendientes = [f for f in todas_las_fechas if f not in fechas_completadas]
        pendientes_tribunal = len(fechas_pendientes)
        total_pendientes += pendientes_tribunal
        
        if pendientes_tribunal > 0:
            tribunales_con_pendientes += 1
        
        print(f"  Tribunal {tribunal}: {len(fechas_completadas)} completadas, {pendientes_tribunal} pendientes")
    
    print(f"✅ Total combinaciones completadas: {sum(len(fechas) for fechas in fechas_por_tribunal.values())}")
    print(f"⏳ Total combinaciones pendientes: {total_pendientes}")
    print(f"🏛️ Tribunales con fechas pendientes: {tribunales_con_pendientes}/{len(tribunales)}")
    
    return total_pendientes

def analizar_checkpoint_tribunales(checkpoint_path, competencia):
    """Analiza checkpoints de tribunales (civil, penal, cobranza, laboral)"""
    print(f"\n=== ANÁLISIS {competencia.upper()} ===")
    print(f"Archivo: {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        print("❌ Archivo no encontrado")
        return
    
    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extraer fechas y tribunales únicos
    fechas_por_tribunal = defaultdict(set)
    tribunales = set()
    
    for key, info in data.items():
        if info.get('status') == 'completed':
            # Formato: "civil_2021-01-01_to_2021-01-07_10" o "tribunales_cobranza_2021-01-01_6"
            if '_to_' in key:
                # Formato con rango de fechas
                parts = key.split('_')
                if len(parts) >= 4:
                    fecha_inicio = parts[1]
                    tribunal = parts[-1]
                    fechas_por_tribunal[tribunal].add(fecha_inicio)
                    tribunales.add(tribunal)
            else:
                # Formato con fecha única
                parts = key.split('_')
                if len(parts) >= 3:
                    fecha = parts[-2]  # Penúltimo elemento es la fecha
                    tribunal = parts[-1]  # Último elemento es el tribunal
                    fechas_por_tribunal[tribunal].add(fecha)
                    tribunales.add(tribunal)
    
    # Generar todas las fechas del rango (por semanas para competencias con rangos)
    if competencia in ['civil', 'penal', 'laboral']:
        # Para estas competencias, se procesan por semanas
        todas_las_fechas = []
        fecha_actual = datetime.strptime('2021-01-01', '%Y-%m-%d')
        fecha_final = datetime.strptime('2025-07-30', '%Y-%m-%d')
        
        while fecha_actual <= fecha_final:
            todas_las_fechas.append(fecha_actual.strftime('%Y-%m-%d'))
            fecha_actual += timedelta(days=7)  # Incrementar por semanas
    else:
        # Para cobranza, se procesan por días
        todas_las_fechas = generar_fechas_rango('2021-01-01', '2025-07-30')
    
    print(f"📊 Total de tribunales encontrados: {len(tribunales)}")
    print(f"📊 Total de fechas/períodos en rango: {len(todas_las_fechas)}")
    
    # Calcular pendientes por tribunal
    total_pendientes = 0
    tribunales_con_pendientes = 0
    
    for tribunal in sorted(tribunales):
        fechas_completadas = fechas_por_tribunal[tribunal]
        fechas_pendientes = [f for f in todas_las_fechas if f not in fechas_completadas]
        pendientes_tribunal = len(fechas_pendientes)
        total_pendientes += pendientes_tribunal
        
        if pendientes_tribunal > 0:
            tribunales_con_pendientes += 1
        
        if len(tribunales) <= 20:  # Solo mostrar detalle si hay pocos tribunales
            print(f"  Tribunal {tribunal}: {len(fechas_completadas)} completadas, {pendientes_tribunal} pendientes")
    
    if len(tribunales) > 20:
        print(f"  (Detalle omitido - demasiados tribunales)")
    
    print(f"✅ Total combinaciones completadas: {sum(len(fechas) for fechas in fechas_por_tribunal.values())}")
    print(f"⏳ Total combinaciones pendientes: {total_pendientes}")
    print(f"🏛️ Tribunales con fechas pendientes: {tribunales_con_pendientes}/{len(tribunales)}")
    
    return total_pendientes

def main():
    """Función principal"""
    print("🔍 ANÁLISIS DE CHECKPOINTS - PROGRESO DE SCRAPING")
    print("=" * 60)
    print(f"📅 Rango de análisis: 2021-01-01 a 2025-07-30")
    
    base_path = r"C:\Worldsys\Scrap-Poder-Judicial-CL\Resultados_Globales"
    
    # Definir rutas de checkpoints
    checkpoints = {
        'suprema': os.path.join(base_path, 'Resultados_suprema', 'checkpoint_suprema.json'),
        'apelaciones': os.path.join(base_path, 'Resultados_apelaciones', 'checkpoint_apelaciones.json'),
        'civil': os.path.join(base_path, 'Resultados_civil', 'checkpoint_tribunales_civil.json'),
        'penal': os.path.join(base_path, 'Resultados_penal', 'checkpoint_tribunales_penal.json'),
        'cobranza': os.path.join(base_path, 'Resultados_cobranza', 'checkpoint_tribunales_cobranza.json'),
        'laboral': os.path.join(base_path, 'Resultados_laboral', 'checkpoint.json')
    }
    
    total_pendientes_global = 0
    
    # Analizar cada competencia
    for competencia, checkpoint_path in checkpoints.items():
        try:
            if competencia == 'suprema':
                pendientes = analizar_checkpoint_suprema(checkpoint_path)
            elif competencia == 'apelaciones':
                pendientes = analizar_checkpoint_apelaciones(checkpoint_path)
            else:
                pendientes = analizar_checkpoint_tribunales(checkpoint_path, competencia)
            
            if pendientes is not None:
                total_pendientes_global += pendientes
                
        except Exception as e:
            print(f"❌ Error analizando {competencia}: {str(e)}")
    
    # Resumen final
    print(f"\n" + "=" * 60)
    print(f"📊 RESUMEN GLOBAL")
    print(f"=" * 60)
    print(f"⏳ Total de días/combinaciones pendientes: {total_pendientes_global:,}")
    print(f"📅 Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Estimación de tiempo
    if total_pendientes_global > 0:
        print(f"\n💡 ESTIMACIONES:")
        print(f"   • A 1,000 registros/día: {total_pendientes_global/1000:.1f} días")
        print(f"   • A 5,000 registros/día: {total_pendientes_global/5000:.1f} días")
        print(f"   • A 10,000 registros/día: {total_pendientes_global/10000:.1f} días")

if __name__ == "__main__":
    main()