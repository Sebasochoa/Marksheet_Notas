"""Widgets y estado de la fila de un alumno en la tabla, y la grilla que comparten."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ..config import COLUMNAS_GRILLA, CRITERIOS
from ..modelos import FilaPlantilla
from ..notas import calificar, es_nota_valida, formatear
from . import tema
from .neu import Campo, Pastilla

ENCABEZADOS_DATOS = ("N°", "", "Código", "Apellidos y nombres")
ENCABEZADOS = ENCABEZADOS_DATOS + COLUMNAS_GRILLA
ALINEACION_DATOS = ("e", "w", "w", "w")
ALINEACION_ENCABEZADO = ALINEACION_DATOS + ("",) * len(COLUMNAS_GRILLA)
PRIMERA_COLUMNA_NOTAS = len(ENCABEZADOS_DATOS)
COLUMNA_TOTAL = PRIMERA_COLUMNA_NOTAS + len(CRITERIOS)
COLUMNA_FINAL = COLUMNA_TOTAL + 1
COLUMNA_NOMBRE = 3
ANCHOS_COLUMNA = (30, 20, 112, 220, 64, 64, 64, 64, 64, 64)   # px de diseño (mínimos)
ANCHO_RESULTADO = 6


def configurar_columnas(contenedor: tk.Misc) -> None:
    for columna, ancho in enumerate(ANCHOS_COLUMNA):
        contenedor.grid_columnconfigure(columna, minsize=tema.px(ancho),
                                        weight=1 if columna == COLUMNA_NOMBRE else 0)


def crear_encabezado(contenedor: tk.Misc, rotulos_criterios: tuple[str, ...] = CRITERIOS) -> None:
    """Encabezado de la grilla con los criterios tal como los imprime el PDF (LA o GV)."""
    textos = ENCABEZADOS_DATOS + tuple(rotulos_criterios) + COLUMNAS_GRILLA[len(CRITERIOS):]
    for columna, (texto, alineacion) in enumerate(zip(textos, ALINEACION_ENCABEZADO)):
        tk.Label(contenedor, text=texto.upper(), font=tema.fuentes.mini, fg=tema.TEXTO_TENUE,
                 bg=tema.FONDO).grid(row=0, column=columna, sticky=alineacion,
                                     padx=tema.px(4), pady=(tema.px(2), tema.px(8)))
    crear_linea(contenedor, 1, "#2e323b")


def crear_linea(contenedor: tk.Misc, fila: int, color: str = tema.LINEA) -> None:
    tk.Frame(contenedor, height=1, bg=color).grid(row=fila, column=0,
                                                  columnspan=len(ENCABEZADOS), sticky="ew")


class FilaNotas:
    """Datos del alumno, un campo por criterio y TOTAL/FR recalculados al escribir."""

    def __init__(self, contenedor: tk.Misc, numero_fila: int, fila: FilaPlantilla,
                 al_cambiar: Callable[[], None]):
        self.fila = fila
        self._al_cambiar = al_cambiar
        self._variables = [tk.StringVar(contenedor) for _ in CRITERIOS]
        self._crear_datos(contenedor, numero_fila)
        self._campos = self._crear_campos(contenedor, numero_fila)
        self.entradas = [campo.entrada for campo in self._campos]
        self._total = tk.Label(contenedor, width=ANCHO_RESULTADO, font=tema.fuentes.celda,
                               fg=tema.TEXTO_SUAVE, bg=tema.FONDO)
        self._total.grid(row=numero_fila, column=COLUMNA_TOTAL)
        self._final = Pastilla(contenedor)
        self._final.grid(row=numero_fila, column=COLUMNA_FINAL)
        for variable in self._variables:
            variable.trace_add("write", lambda *_: self._actualizar())

    def textos(self) -> list[str]:
        return [variable.get().strip() for variable in self._variables]

    def esta_completa(self) -> bool:
        return all(es_nota_valida(texto) for texto in self.textos())

    def resaltar_campos_vacios(self) -> None:
        for campo, texto in zip(self._campos, self.textos()):
            if not texto:
                campo.marcar_error(True)

    def _crear_datos(self, contenedor: tk.Misc, numero_fila: int) -> None:
        alumno = self.fila.alumno
        f = tema.fuentes
        valores = (
            (alumno.numero, f.celda, tema.TEXTO_TENUE),
            (alumno.marca, f.pequena, tema.MAGENTA_CLARO),
            (alumno.codigo, f.pequena, tema.TEXTO_SUAVE),
            (alumno.nombre_completo, f.celda, tema.TEXTO),
        )
        for columna, ((valor, fuente, color), alineacion) in enumerate(zip(valores, ALINEACION_DATOS)):
            tk.Label(contenedor, text=valor, font=fuente, fg=color, bg=tema.FONDO,
                     anchor=alineacion).grid(row=numero_fila, column=columna, padx=tema.px(4),
                                             sticky=alineacion)

    def _crear_campos(self, contenedor: tk.Misc, numero_fila: int) -> list[Campo]:
        campos = []
        for desplazamiento, variable in enumerate(self._variables):
            campo = Campo(contenedor, variable)
            campo.grid(row=numero_fila, column=PRIMERA_COLUMNA_NOTAS + desplazamiento,
                       padx=tema.px(4), pady=tema.px(7))
            campos.append(campo)
        return campos

    def _actualizar(self) -> None:
        for campo, texto in zip(self._campos, self.textos()):
            campo.marcar_error(bool(texto) and not es_nota_valida(texto))
        self._mostrar_resultado()
        self._al_cambiar()

    def _mostrar_resultado(self) -> None:
        if not self.esta_completa():
            self._total.configure(text="")
            self._final.mostrar("", None)
            return
        calificacion = calificar(self.textos())
        self._total.configure(text=formatear(calificacion.total))
        self._final.mostrar(formatear(calificacion.final),
                            "cian" if calificacion.aprobada else "magenta")
