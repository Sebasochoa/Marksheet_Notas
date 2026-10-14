"""Detección de la plantilla completa. Es el único módulo que conoce a pdfplumber."""
from __future__ import annotations

import io
from typing import Sequence

import pdfplumber
from pdfplumber.page import Page

from ..errores import FormatoNoSoportado, PlantillaNoReconocida
from ..modelos import Alumno, FilaPlantilla, Plantilla, Ubicacion
from .geometria import Borde, Palabra
from .grilla import Grilla, buscar_encabezado, construir_grilla
from .renglones import (RenglonAlumno, agrupar_en_renglones, leer_renglon_alumno,
                        separar_apellidos_y_nombres)

HOLGURA_FRANJA_ALUMNOS = 4.0    # pt sobre y bajo las filas al buscar valores ya escritos


def detectar_plantilla(pdf_bytes: bytes) -> Plantilla:
    filas: list[FilaPlantilla] = []
    ya_tiene_valores = False
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:   # pdfminer descifra con clave vacía
        for indice, pagina in enumerate(pdf.pages):
            filas_pagina, con_valores = _detectar_pagina(pagina, indice)
            filas.extend(filas_pagina)
            ya_tiene_valores = ya_tiene_valores or con_valores
    if not filas:
        raise PlantillaNoReconocida(
            "No se encontró la grilla IC/DM/PR/LA/TOTAL/FR con filas de alumnos.")
    return Plantilla(tuple(filas), ya_tiene_valores)


def _detectar_pagina(pagina: Page, indice: int) -> tuple[list[FilaPlantilla], bool]:
    renglones = agrupar_en_renglones(_palabras(pagina))
    encabezado = buscar_encabezado(renglones)
    if encabezado is None:
        return [], False
    if pagina.rotation:
        raise FormatoNoSoportado(f"La página {indice + 1} está rotada.")
    grilla = construir_grilla(encabezado, _bordes(pagina), pagina.height)
    alumnos = _renglones_de_alumnos(renglones, grilla)
    if not alumnos:
        return [], False
    return _armar_filas(alumnos, grilla, indice), _franja_tiene_valores(renglones, alumnos, grilla)


def _renglones_de_alumnos(renglones: Sequence[Sequence[Palabra]],
                          grilla: Grilla) -> list[RenglonAlumno]:
    """Renglones bajo el encabezado, leyendo solo lo que está a la izquierda de la grilla
    (así un PDF ya llenado no mezcla sus notas con los nombres)."""
    alumnos = []
    for renglon in renglones:
        izquierda = [p for p in renglon if p.x1 <= grilla.borde_izquierdo]
        if izquierda and grilla.fin_encabezado < izquierda[0].top < grilla.bottom:
            alumno = leer_renglon_alumno(izquierda)
            if alumno:
                alumnos.append(alumno)
    return alumnos


def _armar_filas(renglones: Sequence[RenglonAlumno], grilla: Grilla,
                 pagina: int) -> list[FilaPlantilla]:
    divisiones = separar_apellidos_y_nombres(renglones)
    centros = grilla.centros_de_filas(renglones)
    return [
        FilaPlantilla(
            Alumno(r.numero, r.marca, r.codigo, apellidos, nombres),
            Ubicacion(pagina, y_centro, grilla.x_por_columna),
        )
        for r, (apellidos, nombres), y_centro in zip(renglones, divisiones, centros)
    ]


def _franja_tiene_valores(renglones: Sequence[Sequence[Palabra]],
                          alumnos: Sequence[RenglonAlumno], grilla: Grilla) -> bool:
    """¿Hay texto dentro de la grilla a la altura de los alumnos? Solo se revisa esa franja
    porque debajo están la leyenda y las firmas."""
    desde = min(a.top for a in alumnos) - HOLGURA_FRANJA_ALUMNOS
    hasta = max(a.bottom for a in alumnos) + HOLGURA_FRANJA_ALUMNOS
    return any(p.x0 >= grilla.borde_izquierdo and p.top >= desde and p.bottom <= hasta
               for renglon in renglones for p in renglon)


def _palabras(pagina: Page) -> list[Palabra]:
    return [Palabra(p["text"], p["x0"], p["x1"], p["top"], p["bottom"])
            for p in pagina.extract_words()]


def _bordes(pagina: Page) -> list[Borde]:
    return [Borde(b["orientation"] == "v", b["x0"], b["x1"], b["top"], b["bottom"])
            for b in pagina.edges]
