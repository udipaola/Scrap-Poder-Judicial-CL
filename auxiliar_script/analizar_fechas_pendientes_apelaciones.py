#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar el checkpoint de apelaciones y determinar los rangos de fechas
ideales para dividir el scraping en 3 PCs.
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict

def cargar_checkpoint():
    """Carga el checkpoint de apelaciones"""
    checkpoint_path = r"D:\RepositoriosDataWorldsys\Scrap-Poder-Judicial-CL\Resultados_Globales\Resultados_apelaciones\checkpoint_apelaciones.json"
    
    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error al cargar checkpoint: {e}")
        return {}

def generar_fechas_rango():
    """Genera todas las fechas del rango 2021-01-01 a 2025-07-30"""
    fecha_inicio = datetime(2021, 1, 1)
    fecha_fin = datetime(2025, 7, 30)
    
    fechas = []
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        fechas.append(fecha_actual.strftime('%Y-%m-%d'))
        fecha_actual += timedelta(days=1)
    
    return fechas

def analizar_fechas_pendientes(checkpoint):
    """Analiza qué fechas están pendientes por tribunal"""
    tribunales = ['10', '11', '15', '20', '25', '30', '35', '40', '45', '46', '50', '55', '56', '60', '61', '90', '91']
    todas_las_fechas = generar_fechas_rango()
    
    fechas_pendientes_por_tribunal = defaultdict(list)
    fechas_completadas_por_tribunal = defaultdict(list)
    
    print(f"📊 Analizando {len(todas_las_fechas)} fechas para {len(tribunales)} tribunales...")
    
    for tribunal in tribunales:
        for fecha in todas_las_fechas:
            clave = f"{fecha}_{tribunal}"
            
            if clave in checkpoint and checkpoint[clave].get('status') == 'completed':
                fechas_completadas_por_tribunal[tribunal].append(fecha)
            else:
                fechas_pendientes_por_tribunal[tribunal].append(fecha)
    
    return fechas_pendientes_por_tribunal, fechas_completadas_por_tribunal

def encontrar_fechas_comunes_pendientes(fechas_pendientes_por_tribunal):
    """Encuentra las fechas que están pendientes en todos los tribunales"""
    tribunales = list(fechas_pendientes_por_tribunal.keys())
    
    if not tribunales:
        return []
    
    # Comenzar con las fechas del primer tribunal
    fechas_comunes = set(fechas_pendientes_por_tribunal[tribunales[0]])
    
    # Intersección con las fechas de los demás tribunales
    for tribunal in tribunales[1:]:
        fechas_comunes = fechas_comunes.intersection(set(fechas_pendientes_por_tribunal[tribunal]))
    
    return sorted(list(fechas_comunes))

def dividir_fechas_en_rangos(fechas_pendientes, num_pcs=3):
    """Divide las fechas pendientes en rangos para múltiples PCs"""
    total_fechas = len(fechas_pendientes)
    fechas_por_pc = total_fechas // num_pcs
    resto = total_fechas % num_pcs
    
    rangos = []
    inicio = 0
    
    for i in range(num_pcs):
        # Distribuir el resto entre los primeros PCs
        fin = inicio + fechas_por_pc + (1 if i < resto else 0)
        
        if inicio < total_fechas:
            fecha_inicio = fechas_pendientes[inicio]
            fecha_fin = fechas_pendientes[min(fin - 1, total_fechas - 1)]
            
            rangos.append({
                'pc': i + 1,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'total_fechas': fin - inicio,
                'indices': (inicio, fin - 1)
            })
        
        inicio = fin
    
    return rangos

def main():
    print("🔍 ANÁLISIS DE FECHAS PENDIENTES - CORTE DE APELACIONES")
    print("=" * 60)
    
    # Cargar checkpoint
    checkpoint = cargar_checkpoint()
    if not checkpoint:
        return
    
    # Analizar fechas pendientes
    fechas_pendientes_por_tribunal, fechas_completadas_por_tribunal = analizar_fechas_pendientes(checkpoint)
    
    # Estadísticas por tribunal
    print("\n📊 ESTADÍSTICAS POR TRIBUNAL:")
    print("-" * 50)
    
    tribunales = ['10', '11', '15', '20', '25', '30', '35', '40', '45', '46', '50', '55', '56', '60', '61', '90', '91']
    
    for tribunal in tribunales:
        completadas = len(fechas_completadas_por_tribunal[tribunal])
        pendientes = len(fechas_pendientes_por_tribunal[tribunal])
        total = completadas + pendientes
        porcentaje = (completadas / total * 100) if total > 0 else 0
        
        print(f"Tribunal {tribunal}: {completadas:4d} completadas, {pendientes:4d} pendientes ({porcentaje:.1f}% completo)")
    
    # Encontrar fechas comunes pendientes
    fechas_comunes_pendientes = encontrar_fechas_comunes_pendientes(fechas_pendientes_por_tribunal)
    
    print(f"\n🎯 FECHAS COMUNES PENDIENTES EN TODOS LOS TRIBUNALES:")
    print(f"Total de fechas pendientes comunes: {len(fechas_comunes_pendientes)}")
    
    if fechas_comunes_pendientes:
        print(f"Primera fecha pendiente: {fechas_comunes_pendientes[0]}")
        print(f"Última fecha pendiente: {fechas_comunes_pendientes[-1]}")
        
        # Dividir en 3 rangos
        rangos = dividir_fechas_en_rangos(fechas_comunes_pendientes, 3)
        
        print(f"\n🚀 DIVISIÓN RECOMENDADA PARA 3 PCs:")
        print("=" * 60)
        
        total_combinaciones = 0
        
        for rango in rangos:
            combinaciones = rango['total_fechas'] * 17  # 17 tribunales (excluyendo tribunal 1)
            total_combinaciones += combinaciones
            
            print(f"\n💻 PC {rango['pc']}:")
            print(f"   📅 Rango de fechas: {rango['fecha_inicio']} a {rango['fecha_fin']}")
            print(f"   📊 Total fechas: {rango['total_fechas']}")
            print(f"   🏛️ Tribunales: 17 (excluyendo tribunal 1)")
            print(f"   🔢 Combinaciones: {combinaciones:,}")
            print(f"   ⏱️ Tiempo estimado: ~{combinaciones//100:.0f} días (a 100 registros/día)")
        
        print(f"\n📈 RESUMEN TOTAL:")
        print(f"   🔢 Total combinaciones: {total_combinaciones:,}")
        print(f"   ⏱️ Tiempo total estimado: ~{total_combinaciones//300:.0f} días (3 PCs a 100 reg/día cada uno)")
        print(f"   📅 Fechas por PC: ~{len(fechas_comunes_pendientes)//3} fechas promedio")
        
        # Mostrar comandos de ejecución
        print(f"\n🔧 COMANDOS DE EJECUCIÓN SUGERIDOS:")
        print("=" * 60)
        
        for rango in rangos:
            print(f"\n# PC {rango['pc']} - Ejecutar desde {rango['fecha_inicio']} hasta {rango['fecha_fin']}")
            print(f"python main_apelaciones.py --fecha_inicio {rango['fecha_inicio']} --fecha_fin {rango['fecha_fin']}")

if __name__ == "__main__":
    main()