"""Esqueleto de carga: filas de bloques que brillan en onda mientras se lee el PDF."""
from __future__ import annotations

import math
import time
import tkinter as tk

from . import tema
from .fila import COLUMNA_FINAL, COLUMNA_TOTAL, PRIMERA_COLUMNA_NOTAS, configurar_columnas, \
    crear_encabezado, crear_linea
from ..config import CRITERIOS

PERIODO_MS = 1400
PASO_MS = 50
DESFASE_FILA = 0.07
DESFASE_COLUMNA = 0.03
ATENUACION_FILA = 0.07          # las filas de abajo se desvanecen hacia el fondo
ANCHOS_NOMBRE = (190, 150, 220, 170, 205, 140, 180, 215, 160, 195)
FILAS_ESQUELETO = 10


class Brillo:
    """Anima bloques (tk.Frame) entre un tono oscuro y uno claro, con desfase por bloque."""

    def __init__(self, dueno: tk.Misc):
        self._dueno = dueno
        self._bloques: list[tuple[tk.Frame, float, str, str]] = []
        self._tarea = None
        self._inicio = 0.0

    def agregar(self, bloque: tk.Frame, desfase: float = 0.0, atenuacion: float = 0.0) -> None:
        oscuro = tema.mezclar(tema.NEUTRO_300, tema.FONDO, atenuacion)
        claro = tema.mezclar(tema.NEUTRO_100, tema.FONDO, atenuacion)
        self._bloques.append((bloque, desfase, oscuro, claro))

    def iniciar(self) -> None:
        if self._tarea is None:
            self._inicio = time.monotonic()
            self._animar()

    def detener(self) -> None:
        if self._tarea is not None:
            self._dueno.after_cancel(self._tarea)
            self._tarea = None

    def _animar(self) -> None:
        ciclos = (time.monotonic() - self._inicio) * 1000 / PERIODO_MS
        for bloque, desfase, oscuro, claro in self._bloques:
            fase = (ciclos - desfase) % 1.0
            luz = 0.5 - 0.5 * math.cos(2 * math.pi * fase)
            bloque.configure(bg=tema.mezclar(oscuro, claro, luz))
        self._tarea = self._dueno.after(PASO_MS, self._animar)


class TablaEsqueleto(tk.Frame):
    """Misma grilla y encabezado que la tabla real, con bloques en lugar de datos."""

    def __init__(self, padre: tk.Misc, filas: int = FILAS_ESQUELETO):
        super().__init__(padre, bg=tema.FONDO)
        self._brillo = Brillo(self)
        configurar_columnas(self)
        crear_encabezado(self)
        px = tema.px
        for k in range(filas):
            fila = 2 + k * 2
            atenuacion = k * ATENUACION_FILA
            self._bloque(fila, 0, 16, k, "e", atenuacion)
            self._bloque(fila, 2, 84, k, "w", atenuacion)
            self._bloque(fila, 3, ANCHOS_NOMBRE[k % len(ANCHOS_NOMBRE)], k, "w", atenuacion)
            campo = tema.mezclar(tema.SUPERFICIE, tema.FONDO, atenuacion)
            for desplazamiento in range(len(CRITERIOS)):
                tk.Frame(self, width=px(50), height=px(30), bg=campo).grid(
                    row=fila, column=PRIMERA_COLUMNA_NOTAS + desplazamiento,
                    padx=px(4), pady=px(6))
            for columna in (COLUMNA_TOTAL, COLUMNA_FINAL):
                tk.Frame(self, width=px(14), height=px(2), bg=tema.NEUTRO_300).grid(
                    row=fila, column=columna)
            crear_linea(self, fila + 1)

    def iniciar(self) -> None:
        self._brillo.iniciar()

    def detener(self) -> None:
        self._brillo.detener()

    def _bloque(self, fila, columna, ancho, k, sticky, atenuacion) -> None:
        bloque = tk.Frame(self, width=tema.px(ancho), height=tema.px(11), bg=tema.NEUTRO_300)
        bloque.grid(row=fila, column=columna, sticky=sticky, padx=tema.px(4))
        self._brillo.agregar(bloque, k * DESFASE_FILA + columna * DESFASE_COLUMNA, atenuacion)
