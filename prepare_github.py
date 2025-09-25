#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para preparar JP-LegalBot V2 para subir a GitHub
"""

import os
import subprocess
import sys

def check_git():
    """Verificar si Git está instalado"""
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True)
        print(f"✅ Git encontrado: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Git no está instalado o no está en el PATH")
        print("📥 Instalar Git desde: https://git-scm.com/download/win")
        return False

def init_repository():
    """Inicializar repositorio Git"""
    commands = [
        ['git', 'init'],
        ['git', 'config', 'user.name', 'Miguel Melendez'],
        ['git', 'config', 'user.email', 'melendez_ma@jp.pr.gov'],
        ['git', 'add', '.'],
        ['git', 'commit', '-m', 'Initial commit: JP-LegalBot V2 con autenticación SQLite y mejoras de UI'],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print(f"✅ {' '.join(cmd)}")
            else:
                print(f"❌ Error en {' '.join(cmd)}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error ejecutando {' '.join(cmd)}: {e}")

def add_remote():
    """Agregar repositorio remoto"""
    repo_url = "https://github.com/mmelendezJPPR/JP-LegalBot_V2.git"
    
    commands = [
        ['git', 'remote', 'add', 'origin', repo_url],
        ['git', 'branch', '-M', 'main'],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print(f"✅ {' '.join(cmd)}")
            else:
                print(f"⚠️ {' '.join(cmd)}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error ejecutando {' '.join(cmd)}: {e}")

def push_to_github():
    """Push al repositorio de GitHub"""
    cmd = ['git', 'push', '-u', 'origin', 'main']
    
    try:
        print("📤 Subiendo a GitHub...")
        result = subprocess.run(cmd, cwd='.')
        if result.returncode == 0:
            print("✅ Proyecto subido exitosamente a GitHub!")
            print("🌐 Ver en: https://github.com/mmelendezJPPR/JP-LegalBot_V2")
        else:
            print("❌ Error subiendo a GitHub")
    except Exception as e:
        print(f"❌ Error en push: {e}")

def main():
    """Función principal"""
    print("🚀 PREPARANDO JP-LEGALBOT V2 PARA GITHUB")
    print("=" * 50)
    
    # Verificar Git
    if not check_git():
        return
    
    # Verificar si ya es un repositorio
    if os.path.exists('.git'):
        print("📁 Repositorio Git ya existe")
    else:
        print("📁 Inicializando nuevo repositorio...")
        init_repository()
    
    # Agregar remoto
    print("\n🔗 Configurando repositorio remoto...")
    add_remote()
    
    # Push a GitHub
    print("\n📤 ¿Deseas subir el proyecto a GitHub ahora? (y/n): ", end="")
    choice = input().lower()
    
    if choice in ['y', 'yes', 's', 'si']:
        push_to_github()
    else:
        print("⏸️ Push cancelado. Puedes subirlo manualmente con:")
        print("   git push -u origin main")
    
    print("\n✅ ¡Preparación completada!")

if __name__ == "__main__":
    main()