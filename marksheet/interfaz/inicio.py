"""Arranque de la aplicación de escritorio."""
from __future__ import annotations

import ctypes
import sys

from . import tema
from .icono import identificar_aplicacion
from .ventana import VentanaPrincipal

DPI_POR_SISTEMA = 1      # PROCESS_SYSTEM_DPI_AWARE


def iniciar(ruta_inicial: str | None = None) -> None:
    _habilitar_alta_resolucion()
    identificar_aplicacion()
    tema.registrar_fuentes()
    VentanaPrincipal(ruta_inicial).mainloop()


def _habilitar_alta_resolucion() -> None:
    """Evita texto borroso en Windows con escalado de pantalla mayor a 100 %."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(DPI_POR_SISTEMA)
    except (AttributeError, OSError):
        pass        # Windows anterior a 8.1: se mantiene el escalado del sistema
