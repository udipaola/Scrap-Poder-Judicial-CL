# tests/validacion_manual.py
import subprocess
import sys
import time
from datetime import datetime

def ejecutar_comando(comando, timeout=120):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(
            comando, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            shell=True
        )
        return result
    except subprocess.TimeoutExpired:
        return None

def validar_modulo(modulo, directorio):
    """Valida un módulo específico según el checklist"""
    print(f"\n🧪 Validando módulo: {modulo.upper()}")
    print("=" * 50)
    
    resultados = {
        'modulo': modulo,
        'debug_funciona': False,
        'logs_debug_presentes': False,
        'sin_debug_limpio': False,
        'errores': []
    }
    
    # 1. Probar modo debug
    print("1️⃣ Probando modo debug...")
    comando_debug = f"python ../{directorio}/main_{modulo}.py --debug --modo historico --desde 2024-01-01 --hasta 2024-01-01 --procesos 1"
    
    result_debug = ejecutar_comando(comando_debug, timeout=60)
    
    if result_debug is None:
        print("   ❌ Timeout en modo debug")
        resultados['errores'].append("Timeout en modo debug")
    elif result_debug.returncode != 0:
        print(f"   ❌ Error en modo debug: {result_debug.stderr}")
        resultados['errores'].append(f"Error en modo debug: {result_debug.stderr}")
    else:
        resultados['debug_funciona'] = True
        print("   ✅ Modo debug ejecutado correctamente")
        
        # 2. Verificar logs esperados
        print("2️⃣ Verificando logs de debug...")
        output = result_debug.stdout
        
        logs_esperados = [
            "🚀",  # INICIANDO
            "⚙️",  # PROCESANDO
            "🔍",  # DEBUG
            "DEBUG"
        ]
        
        logs_encontrados = []
        for log in logs_esperados:
            if log in output:
                logs_encontrados.append(log)
                print(f"   ✅ Log encontrado: {log}")
            else:
                print(f"   ❌ Log faltante: {log}")
        
        if len(logs_encontrados) >= 3:  # Al menos 3 de 4 logs
            resultados['logs_debug_presentes'] = True
            print("   ✅ Logs de debug presentes")
        else:
            resultados['errores'].append("Logs de debug insuficientes")
    
    # 3. Probar sin debug
    print("3️⃣ Probando sin modo debug...")
    comando_normal = f"python ../{directorio}/main_{modulo}.py --modo historico --desde 2024-01-01 --hasta 2024-01-01 --procesos 1"
    
    result_normal = ejecutar_comando(comando_normal, timeout=60)
    
    if result_normal is None:
        print("   ❌ Timeout sin modo debug")
        resultados['errores'].append("Timeout sin modo debug")
    elif result_normal.returncode != 0:
        print(f"   ❌ Error sin modo debug: {result_normal.stderr}")
        resultados['errores'].append(f"Error sin modo debug: {result_normal.stderr}")
    else:
        print("   ✅ Modo normal ejecutado correctamente")
        
        # 4. Verificar que NO aparezcan logs DEBUG
        print("4️⃣ Verificando ausencia de logs DEBUG...")
        output_normal = result_normal.stdout
        
        if "🔍" not in output_normal and "DEBUG" not in output_normal:
            resultados['sin_debug_limpio'] = True
            print("   ✅ No se encontraron logs DEBUG en modo normal")
        else:
            print("   ❌ Se encontraron logs DEBUG en modo normal")
            resultados['errores'].append("Logs DEBUG presentes en modo normal")
    
    return resultados

def generar_reporte_validacion(resultados_modulos):
    """Genera un reporte de validación"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    reporte = f"""
# 📋 Reporte de Validación Manual

**Fecha:** {timestamp}

## 📊 Resumen

"""
    
    total_modulos = len(resultados_modulos)
    modulos_exitosos = sum(1 for r in resultados_modulos if len(r['errores']) == 0)
    
    reporte += f"- **Total módulos:** {total_modulos}\n"
    reporte += f"- **Módulos exitosos:** {modulos_exitosos}\n"
    reporte += f"- **Tasa de éxito:** {(modulos_exitosos/total_modulos)*100:.1f}%\n\n"
    
    reporte += "## 🔍 Detalles por Módulo\n\n"
    
    for resultado in resultados_modulos:
        modulo = resultado['modulo']
        reporte += f"### {modulo.upper()}\n\n"
        
        if len(resultado['errores']) == 0:
            reporte += "✅ **Estado:** EXITOSO\n\n"
        else:
            reporte += "❌ **Estado:** CON ERRORES\n\n"
        
        reporte += f"- Debug funciona: {'✅' if resultado['debug_funciona'] else '❌'}\n"
        reporte += f"- Logs debug presentes: {'✅' if resultado['logs_debug_presentes'] else '❌'}\n"
        reporte += f"- Sin debug limpio: {'✅' if resultado['sin_debug_limpio'] else '❌'}\n\n"
        
        if resultado['errores']:
            reporte += "**Errores encontrados:**\n"
            for error in resultado['errores']:
                reporte += f"- {error}\n"
            reporte += "\n"
    
    return reporte

def main():
    """Función principal de validación"""
    print("🧪 VALIDACIÓN MANUAL DE MÓDULOS")
    print("=" * 50)
    print(f"Iniciando validación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    modulos = [
        ('civil', 'tribunales_civil'),
        ('cobranza', 'tribunales_cobranza'),
        ('laboral', 'tribunales_laboral'),
        ('penal', 'tribunales_penal'),
        ('apelaciones', 'Corte_apelaciones'),
        ('suprema', 'Corte_suprema')
    ]
    
    resultados = []
    
    for modulo, directorio in modulos:
        try:
            resultado = validar_modulo(modulo, directorio)
            resultados.append(resultado)
        except Exception as e:
            print(f"❌ Error validando {modulo}: {str(e)}")
            resultados.append({
                'modulo': modulo,
                'debug_funciona': False,
                'logs_debug_presentes': False,
                'sin_debug_limpio': False,
                'errores': [f"Error de validación: {str(e)}"]
            })
    
    # Generar reporte
    reporte = generar_reporte_validacion(resultados)
    
    # Guardar reporte
    with open('reporte_validacion_manual.md', 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print("\n📄 Reporte guardado en: tests/reporte_validacion_manual.md")
    
    # Mostrar resumen
    total = len(resultados)
    exitosos = sum(1 for r in resultados if len(r['errores']) == 0)
    
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   Total módulos: {total}")
    print(f"   Exitosos: {exitosos}")
    print(f"   Con errores: {total - exitosos}")
    print(f"   Tasa de éxito: {(exitosos/total)*100:.1f}%")
    
    if exitosos == total:
        print("\n🎉 ¡Todos los módulos pasaron la validación!")
        return 0
    else:
        print("\n⚠️ Algunos módulos requieren atención")
        return 1

if __name__ == '__main__':
    sys.exit(main())