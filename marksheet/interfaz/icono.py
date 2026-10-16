"""Ícono de la aplicación en la ventana, los diálogos y la barra de tareas."""
from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from pathlib import Path

CARPETA_RECURSOS = Path(__file__).with_name("recursos")
ICONO_ICO = CARPETA_RECURSOS / "icono.ico"       # Windows: trae 16-256 px dibujados por tamaño
ICONO_PNG = CARPETA_RECURSOS / "icono.png"       # otros sistemas
ID_APLICACION = "MarkSheet.LlenarNotas"          # AppUserModelID


def identificar_aplicacion() -> None:
    """Da a la aplicación su propio botón en la barra de tareas. Debe llamarse antes de crear
    la ventana.

    Ejecutada con 'python main.py', Windows agrupa la ventana bajo python.exe y muestra el ícono
    de Python. El .exe ya tiene identidad propia: asignarle otra haría que, si lo anclas a la
    barra, la ventana abierta aparezca como un segundo botón aparte del anclado.
    """
    if sys.platform != "win32" or getattr(sys, "frozen", False):
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ID_APLICACION)
    except (AttributeError, OSError):
        pass        # Windows anterior a 7: se mantiene la agrupación por ejecutable


def aplicar_icono(ventana: tk.Tk) -> None:
    """Reemplaza la pluma de Tk. 'default=' hace que cada Toplevel (los diálogos) lo herede."""
    if sys.platform == "win32" and ICONO_ICO.is_file():
        ventana.iconbitmap(default=str(ICONO_ICO))
    elif ICONO_PNG.is_file():
        ventana.icono_png = tk.PhotoImage(master=ventana, file=str(ICONO_PNG))
        ventana.iconphoto(True, ventana.icono_png)
