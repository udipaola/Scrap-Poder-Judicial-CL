#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecutor Centralizado - Scraper Poder Judicial Chile
Interfaz amigable para ejecutar cualquier módulo de scraping
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
import re

class ScrapingExecutor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.modulos = {
            '1': {
                'nombre': 'Corte Suprema',
                'directorio': 'Corte_suprema',
                'archivo': 'main_suprema.py',
                'descripcion': 'Scraping de la Corte Suprema de Chile'
            },
            '2': {
                'nombre': 'Corte de Apelaciones',
                'directorio': 'Corte_apelaciones', 
                'archivo': 'main_apelaciones.py',
                'descripcion': 'Scraping de las Cortes de Apelaciones'
            },
            '3': {
                'nombre': 'Tribunales Civil',
                'directorio': 'tribunales_civil',
                'archivo': 'main_civil.py',
                'descripcion': 'Scraping de tribunales civiles'
            },
            '4': {
                'nombre': 'Tribunales Cobranza',
                'directorio': 'tribunales_cobranza',
                'archivo': 'main_cobranza.py',
                'descripcion': 'Scraping de tribunales de cobranza'
            },
            '5': {
                'nombre': 'Tribunales Laboral',
                'directorio': 'tribunales_laboral',
                'archivo': 'main_laboral.py',
                'descripcion': 'Scraping de tribunales laborales'
            },
            '6': {
                'nombre': 'Tribunales Penal',
                'directorio': 'tribunales_penal',
                'archivo': 'main_penal.py',
                'descripcion': 'Scraping de tribunales penales'
            }
        }
    
    def limpiar_pantalla(self):
        """Limpia la pantalla de la consola"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def mostrar_header(self, titulo="SCRAPER PODER JUDICIAL CHILE"):
        """Muestra el header del programa"""
        print("=" * 60)
        print(f"    {titulo}")
        print("=" * 60)
        print()
    
    def validar_fecha(self, fecha_str):
        """Valida que la fecha tenga el formato correcto YYYY-MM-DD"""
        patron = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(patron, fecha_str):
            return False
        try:
            datetime.strptime(fecha_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def obtener_fecha_actual(self):
        """Obtiene la fecha actual en formato YYYY-MM-DD"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def mostrar_menu_principal(self):
        """Muestra el menú principal y retorna la opción seleccionada"""
        self.limpiar_pantalla()
        self.mostrar_header()
        
        print("Seleccione el módulo a ejecutar:")
        print()
        
        for key, modulo in self.modulos.items():
            print(f"{key}. {modulo['nombre']}")
            print(f"   {modulo['descripcion']}")
            print()
        
        print("7. Salir")
        print()
        
        while True:
            opcion = input("Ingrese su opción (1-7): ").strip()
            if opcion in self.modulos or opcion == '7':
                return opcion
            print("❌ Opción inválida. Intente nuevamente.")
    
    def configurar_parametros(self, modulo_info):
        """Configura los parámetros de ejecución"""
        self.limpiar_pantalla()
        self.mostrar_header("CONFIGURACIÓN DE PARÁMETROS")
        
        print(f"Módulo seleccionado: {modulo_info['nombre']}")
        print(f"Descripción: {modulo_info['descripcion']}")
        print()
        
        # Configurar modo
        print("Seleccione el modo de ejecución:")
        print("1. Histórico (rango de fechas personalizado)")
        print("2. Diario (fecha actual)")
        print()
        
        while True:
            modo_num = input("Ingrese su opción (1-2): ").strip()
            if modo_num == '1':
                modo = 'historico'
                break
            elif modo_num == '2':
                modo = 'diario'
                break
            print("❌ Opción inválida. Intente nuevamente.")
        
        # Configurar fechas
        if modo == 'historico':
            print()
            print("📅 Configuración de fechas (formato: YYYY-MM-DD):")
            
            while True:
                fecha_desde = input("Fecha desde (ej: 2024-01-01): ").strip()
                if self.validar_fecha(fecha_desde):
                    break
                print("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            
            while True:
                fecha_hasta = input("Fecha hasta (ej: 2024-01-31): ").strip()
                if self.validar_fecha(fecha_hasta):
                    # Validar que fecha_hasta >= fecha_desde
                    if fecha_hasta >= fecha_desde:
                        break
                    else:
                        print("❌ La fecha hasta debe ser mayor o igual a la fecha desde")
                else:
                    print("❌ Formato de fecha inválido. Use YYYY-MM-DD")
        else:
            fecha_desde = fecha_hasta = self.obtener_fecha_actual()
            print(f"📅 Fecha seleccionada: {fecha_desde}")
        
        # Configurar procesos
        print()
        while True:
            try:
                procesos_input = input("🔧 Número de procesos concurrentes (recomendado: 2-4, default: 2): ").strip()
                if procesos_input == '':
                    procesos = 2
                    break
                procesos = int(procesos_input)
                if 1 <= procesos <= 20:
                    break
                print("❌ El número de procesos debe estar entre 1 y 10")
            except ValueError:
                print("❌ Ingrese un número válido")
        
        # Configurar tamaño de tanda
        while True:
            try:
                tanda_input = input("📦 Tamaño de tanda (recomendado: 2, default: 2): ").strip()
                if tanda_input == '':
                    tanda_size = 2
                    break
                tanda_size = int(tanda_input)
                if 1 <= tanda_size <= procesos:
                    break
                print(f"❌ El tamaño de tanda debe estar entre 1 y {procesos}")
            except ValueError:
                print("❌ Ingrese un número válido")
        
        # Configurar delay
        while True:
            try:
                delay_input = input("⏱️  Delay entre tandas en segundos (recomendado: 90, default: 90): ").strip()
                if delay_input == '':
                    delay_tanda = 90
                    break
                delay_tanda = int(delay_input)
                if 10 <= delay_tanda <= 300:
                    break
                print("❌ El delay debe estar entre 10 y 300 segundos")
            except ValueError:
                print("❌ Ingrese un número válido")
        
        # Configurar headless
        print()
        while True:
            headless_input = input("🖥️  ¿Ejecutar en modo headless (sin ventana del navegador)? S/N (default: S): ").strip().upper()
            if headless_input == '' or headless_input == 'S':
                headless = True
                break
            elif headless_input == 'N':
                headless = False
                break
            print("❌ Ingrese S para Sí o N para No")
        
        return {
            'modo': modo,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'procesos': procesos,
            'tanda_size': tanda_size,
            'delay_tanda': delay_tanda,
            'headless': headless
        }
    
    def confirmar_ejecucion(self, modulo_info, parametros):
        """Muestra la confirmación antes de ejecutar"""
        self.limpiar_pantalla()
        self.mostrar_header("CONFIRMACIÓN DE EJECUCIÓN")
        
        print(f"📁 Módulo: {modulo_info['nombre']}")
        print(f"📝 Descripción: {modulo_info['descripcion']}")
        print(f"🎯 Modo: {parametros['modo']}")
        
        if parametros['modo'] == 'historico':
            print(f"📅 Fecha desde: {parametros['fecha_desde']}")
            print(f"📅 Fecha hasta: {parametros['fecha_hasta']}")
        else:
            print(f"📅 Fecha: {parametros['fecha_desde']}")
        
        print(f"🔧 Procesos: {parametros['procesos']}")
        print(f"📦 Tamaño tanda: {parametros['tanda_size']}")
        print(f"⏱️  Delay tanda: {parametros['delay_tanda']}s")
        print(f"🖥️  Modo headless: {'SÍ' if parametros['headless'] else 'NO'}")
        print()
        
        while True:
            confirmar = input("¿Confirma la ejecución? S/N: ").strip().upper()
            if confirmar == 'S':
                return True
            elif confirmar == 'N':
                return False
            print("❌ Ingrese S para Sí o N para No")
    
    def ejecutar_scraping(self, modulo_info, parametros):
        """Ejecuta el scraping con los parámetros configurados"""
        self.limpiar_pantalla()
        self.mostrar_header("EJECUTANDO SCRAPING...")
        
        print(f"🚀 Iniciando {modulo_info['nombre']}...")
        print(f"📁 Directorio: {modulo_info['directorio']}")
        print(f"📄 Archivo: {modulo_info['archivo']}")
        print()
        print("⚠️  Presione Ctrl+C para detener la ejecución")
        print("=" * 60)
        print()
        
        # Cambiar al directorio del módulo
        modulo_path = os.path.join(self.base_dir, modulo_info['directorio'])
        
        # Construir comando
        cmd = ['python', modulo_info['archivo']]
        cmd.extend(['--modo', parametros['modo']])
        
        if parametros['modo'] == 'historico':
            cmd.extend(['--desde', parametros['fecha_desde']])
            cmd.extend(['--hasta', parametros['fecha_hasta']])
        
        cmd.extend(['--procesos', str(parametros['procesos'])])
        cmd.extend(['--tanda_size', str(parametros['tanda_size'])])
        cmd.extend(['--delay_tanda', str(parametros['delay_tanda'])])
        
        if parametros['headless']:
            cmd.append('--headless')
        
        try:
            # Ejecutar el comando
            result = subprocess.run(cmd, cwd=modulo_path, check=False)
            
            print()
            print("=" * 60)
            if result.returncode == 0:
                print("✅ EJECUCIÓN COMPLETADA EXITOSAMENTE")
            else:
                print(f"⚠️  EJECUCIÓN TERMINADA CON CÓDIGO: {result.returncode}")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print()
            print("=" * 60)
            print("🛑 EJECUCIÓN INTERRUMPIDA POR EL USUARIO")
            print("=" * 60)
        except Exception as e:
            print()
            print("=" * 60)
            print(f"❌ ERROR DURANTE LA EJECUCIÓN: {e}")
            print("=" * 60)
        
        print()
        input("Presione Enter para volver al menú principal...")
    
    def verificar_modulos(self):
        """Verifica que los módulos existan"""
        modulos_faltantes = []
        for key, modulo in self.modulos.items():
            modulo_path = os.path.join(self.base_dir, modulo['directorio'])
            archivo_path = os.path.join(modulo_path, modulo['archivo'])
            
            if not os.path.exists(archivo_path):
                modulos_faltantes.append(f"{modulo['nombre']} ({archivo_path})")
        
        if modulos_faltantes:
            print("⚠️  ADVERTENCIA: Los siguientes módulos no se encontraron:")
            for modulo in modulos_faltantes:
                print(f"   - {modulo}")
            print()
            input("Presione Enter para continuar...")
    
    def run(self):
        """Ejecuta el programa principal"""
        try:
            self.verificar_modulos()
            
            while True:
                opcion = self.mostrar_menu_principal()
                
                if opcion == '7':
                    self.limpiar_pantalla()
                    print("👋 ¡Gracias por usar el Scraper Poder Judicial Chile!")
                    print()
                    break
                
                modulo_info = self.modulos[opcion]
                parametros = self.configurar_parametros(modulo_info)
                
                if self.confirmar_ejecucion(modulo_info, parametros):
                    self.ejecutar_scraping(modulo_info, parametros)
        
        except KeyboardInterrupt:
            print()
            print("👋 Programa interrumpido por el usuario. ¡Hasta luego!")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            input("Presione Enter para salir...")

if __name__ == "__main__":
    executor = ScrapingExecutor()
    executor.run()