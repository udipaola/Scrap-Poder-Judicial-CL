# tests/run_all_tests.py
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
from datetime import datetime

def run_module_test(module_name):
    """Ejecuta las pruebas para un módulo específico"""
    print(f"\n[TEST] Ejecutando pruebas para {module_name}...")
    print("=" * 60)
    
    try:
        # Verificar si existe el archivo de prueba
        test_file = f"test_{module_name}.py"
        if not os.path.exists(test_file):
            print(f"[WARNING] Archivo de prueba {test_file} no encontrado")
            return False
            
        # Ejecutar las pruebas
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=300)  # 5 minutos timeout
        
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Timeout ejecutando pruebas para {module_name}")
        return False
    except Exception as e:
        print(f"[ERROR] Error ejecutando pruebas para {module_name}: {str(e)}")
        return False

def test_debug_functionality_all_modules():
    """Prueba rápida de funcionalidad --debug en todos los módulos"""
    print("\n[DEBUG_TEST] Prueba rapida de --debug en todos los modulos")
    print("=" * 60)
    
    modules = [
        ("tribunales_civil", "main_civil.py"),
        ("tribunales_cobranza", "main_cobranza.py"),
        ("tribunales_laboral", "main_laboral.py"),
        ("tribunales_penal", "main_penal.py"),
        ("Corte_apelaciones", "main_apelaciones.py"),
        ("Corte_suprema", "main_suprema.py")
    ]
    
    results = {}
    
    for module_dir, main_file in modules:
        print(f"\n[MODULE] Probando {module_dir}...")
        
        try:
            # Verificar que el archivo main existe
            main_path = os.path.join("..", module_dir, main_file)
            if not os.path.exists(main_path):
                print(f"[FAIL] {main_path} no encontrado")
                results[module_dir] = False
                continue
            
            # Probar --help para verificar que --debug está disponible
            result = subprocess.run([
                sys.executable, main_file, "--help"
            ], capture_output=True, text=True, timeout=30, cwd=f"../{module_dir}")
            
            if "--debug" in result.stdout:
                print(f"[PASS] {module_dir}: argumento --debug disponible")
                results[module_dir] = True
            else:
                print(f"[FAIL] {module_dir}: argumento --debug NO disponible")
                results[module_dir] = False
                
        except Exception as e:
            print(f"[ERROR] {module_dir}: Error - {str(e)}")
            results[module_dir] = False
    
    return results

def generate_test_report(results):
    """Genera un reporte de las pruebas ejecutadas"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# Reporte de Pruebas - {timestamp}

## Resumen de Resultados

"""
    
    total_modules = len(results)
    passed_modules = sum(1 for result in results.values() if result)
    
    report += f"- **Total de módulos probados**: {total_modules}\n"
    report += f"- **Módulos que pasaron**: {passed_modules}\n"
    report += f"- **Módulos que fallaron**: {total_modules - passed_modules}\n"
    report += f"- **Tasa de éxito**: {(passed_modules/total_modules)*100:.1f}%\n\n"
    
    report += "## Resultados Detallados\n\n"
    
    for module, result in results.items():
        status = "PASO" if result else "FALLO"
        report += f"- **{module}**: {status}\n"
    
    # Guardar reporte
    with open("test_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n[REPORT] Reporte guardado en test_report.md")
    return report

if __name__ == "__main__":
    print("[START] Ejecutando suite completa de pruebas")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cambiar al directorio de tests
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Ejecutar prueba rápida de --debug en todos los módulos
    debug_results = test_debug_functionality_all_modules()
    
    # Ejecutar pruebas específicas disponibles
    available_tests = ["civil"]  # Solo civil por ahora
    test_results = {}
    
    for module in available_tests:
        test_results[f"tribunales_{module}"] = run_module_test(module)
    
    # Combinar resultados
    all_results = {**debug_results, **test_results}
    
    # Generar reporte
    print("\n[SUMMARY] RESUMEN FINAL")
    print("=" * 60)
    
    generate_test_report(debug_results)
    
    total_passed = sum(1 for result in debug_results.values() if result)
    total_modules = len(debug_results)
    
    print(f"\n[RESULT] Resultado final: {total_passed}/{total_modules} modulos pasaron las pruebas")
    
    if total_passed == total_modules:
        print("[SUCCESS] Todas las pruebas pasaron!")
        sys.exit(0)
    else:
        print("[WARNING] Algunas pruebas fallaron. Revisar detalles arriba.")
        sys.exit(1)