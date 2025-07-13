# tests/test_civil.py
# -*- coding: utf-8 -*-
import subprocess
import time
import os
import sys

def test_logging_debug_mode():
    """Prueba que el modo debug funcione correctamente"""
    print("[TEST] Probando modo debug en tribunales_civil...")
    
    try:
        # Ejecutar con debug
        result = subprocess.run([
            sys.executable, "tribunales_civil/main_civil.py", 
            "--debug", "--modo", "historico", "--desde", "2024-01-01", "--hasta", "2024-01-01", "--procesos", "1"
        ], capture_output=True, text=True, timeout=120, cwd="..")
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout[:500]}...")  # Primeros 500 caracteres
        print(f"STDERR: {result.stderr[:500]}...")  # Primeros 500 caracteres
        
        # Verificar que aparezcan logs de debug
        if "DEBUG" in result.stdout:
            print("[PASS] Logs de debug encontrados")
            return True
        else:
            print("[FAIL] No se encontraron logs de debug")
            return False
            
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] El proceso tomo mas de 2 minutos")
        return False
    except Exception as e:
        print(f"[ERROR] Error ejecutando prueba: {str(e)}")
        return False

def test_normal_mode():
    """Prueba que el modo normal (sin debug) funcione correctamente"""
    print("[TEST] Probando modo normal en tribunales_civil...")
    
    try:
        # Ejecutar sin debug
        result = subprocess.run([
            sys.executable, "tribunales_civil/main_civil.py", 
            "--modo", "historico", "--desde", "2024-01-01", "--hasta", "2024-01-01", "--procesos", "1"
        ], capture_output=True, text=True, timeout=120, cwd="..")
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout[:500]}...")  # Primeros 500 caracteres
        
        # Verificar que NO aparezcan logs de debug
        if "DEBUG" not in result.stdout:
            print("[PASS] Modo normal funcionando (sin logs de debug)")
            return True
        else:
            print("[FAIL] Se encontraron logs de debug en modo normal")
            return False
            
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] El proceso tomo mas de 2 minutos")
        return False
    except Exception as e:
        print(f"[ERROR] Error ejecutando prueba: {str(e)}")
        return False

def test_help_argument():
    """Prueba que el argumento --help funcione"""
    print("[TEST] Probando argumento --help en tribunales_civil...")
    
    try:
        result = subprocess.run([
            sys.executable, "tribunales_civil/main_civil.py", "--help"
        ], capture_output=True, text=True, timeout=30, cwd="..")
        
        if "--debug" in result.stdout:
            print("[PASS] Argumento --debug disponible en help")
            return True
        else:
            print("[FAIL] Argumento --debug no encontrado en help")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error ejecutando prueba: {str(e)}")
        return False

if __name__ == "__main__":
    print("[START] Iniciando pruebas para tribunales_civil")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Ejecutar pruebas
    if test_help_argument():
        tests_passed += 1
    
    if test_normal_mode():
        tests_passed += 1
        
    if test_logging_debug_mode():
        tests_passed += 1
    
    print("=" * 50)
    print(f"[RESULTS] Resultados: {tests_passed}/{total_tests} pruebas pasaron")
    
    if tests_passed == total_tests:
        print("[SUCCESS] Todas las pruebas de tribunales_civil pasaron")
        sys.exit(0)
    else:
        print("[FAILED] Algunas pruebas fallaron")
        sys.exit(1)