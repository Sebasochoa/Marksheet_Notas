"""Punto de entrada, también para PyInstaller. Uso: python main.py [archivo.pdf]"""
import sys

from marksheet.interfaz import iniciar

if __name__ == "__main__":
    iniciar(sys.argv[1] if len(sys.argv) > 1 else None)
