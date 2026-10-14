"""Widgets y estado de la fila de un alumno en la tabla."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..config import COLUMNAS_GRILLA, CRITERIOS
from ..modelos import FilaPlantilla
from ..notas import calificar, es_nota_valida, formatear

ENCABEZADOS_DATOS = ("N°", "", "Código", "Apellidos y nombres")
ENCABEZADOS = ENCABEZADOS_DATOS + COLUMNAS_GRILLA
ALINEACION_DATOS = ("e", "", "", "w")
PRIMERA_COLUMNA_NOTAS = len(ENCABEZADOS_DATOS)
COLUMNA_TOTAL = PRIMERA_COLUMNA_NOTAS + len(CRITERIOS)
COLUMNA_FINAL = COLUMNA_TOTAL + 1

COLOR_CAMPO = "white"
COLOR_ERROR = "#f6c6c6"
COLOR_APROBADO = "#1b7a1b"
COLOR_DESAPROBADO = "#c62828"
ANCHO_CAMPO = 5
ANCHO_RESULTADO = 6
MARGEN_DATOS = 4
MARGEN_CAMPO = 2
MARGEN_VERTICAL = 1


class FilaNotas:
    """Datos del alumno, un campo por criterio y TOTAL/FR recalculados al escribir."""

    def __init__(self, contenedor: tk.Misc, numero_fila: int, fila: FilaPlantilla,
                 al_cambiar: Callable[[], None]):
        self.fila = fila
        self._al_cambiar = al_cambiar
        self._variables = [tk.StringVar(contenedor) for _ in CRITERIOS]
        self._crear_datos(contenedor, numero_fila)
        self.entradas = self._crear_entradas(contenedor, numero_fila)
        self._total = self._crear_resultado(contenedor, numero_fila, COLUMNA_TOTAL)
        self._final = self._crear_resultado(contenedor, numero_fila, COLUMNA_FINAL)
        for variable in self._variables:
            variable.trace_add("write", lambda *_: self._actualizar())

    def textos(self) -> list[str]:
        return [variable.get().strip() for variable in self._variables]

    def esta_completa(self) -> bool:
        return all(es_nota_valida(texto) for texto in self.textos())

    def resaltar_campos_vacios(self) -> None:
        for entrada, texto in zip(self.entradas, self.textos()):
            if not texto:
                entrada.configure(bg=COLOR_ERROR)

    def _crear_datos(self, contenedor: tk.Misc, numero_fila: int) -> None:
        alumno = self.fila.alumno
        valores = (alumno.numero, alumno.marca, alumno.codigo, alumno.nombre_completo)
        for columna, (valor, alineacion) in enumerate(zip(valores, ALINEACION_DATOS)):
            ttk.Label(contenedor, text=valor).grid(row=numero_fila, column=columna,
                                                   padx=MARGEN_DATOS, sticky=alineacion)

    def _crear_entradas(self, contenedor: tk.Misc, numero_fila: int) -> list[tk.Entry]:
        entradas = []
        for desplazamiento, variable in enumerate(self._variables):
            entrada = tk.Entry(contenedor, textvariable=variable, width=ANCHO_CAMPO,
                               justify="center", bg=COLOR_CAMPO)
            entrada.grid(row=numero_fila, column=PRIMERA_COLUMNA_NOTAS + desplazamiento,
                         padx=MARGEN_CAMPO, pady=MARGEN_VERTICAL)
            entradas.append(entrada)
        return entradas

    @staticmethod
    def _crear_resultado(contenedor: tk.Misc, numero_fila: int, columna: int) -> tk.Label:
        etiqueta = tk.Label(contenedor, width=ANCHO_RESULTADO)
        etiqueta.grid(row=numero_fila, column=columna)
        return etiqueta

    def _actualizar(self) -> None:
        self._resaltar_invalidas()
        self._mostrar_resultado()
        self._al_cambiar()

    def _resaltar_invalidas(self) -> None:
        for entrada, texto in zip(self.entradas, self.textos()):
            invalida = bool(texto) and not es_nota_valida(texto)
            entrada.configure(bg=COLOR_ERROR if invalida else COLOR_CAMPO)

    def _mostrar_resultado(self) -> None:
        if not self.esta_completa():
            self._total.configure(text="")
            self._final.configure(text="")
            return
        calificacion = calificar(self.textos())
        color = COLOR_APROBADO if calificacion.aprobada else COLOR_DESAPROBADO
        self._total.configure(text=formatear(calificacion.total))
        self._final.configure(text=formatear(calificacion.final), fg=color)
