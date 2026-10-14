"""Capa transparente con los textos, del mismo tamaño que la página original."""
from __future__ import annotations

import io
from typing import Sequence

from pypdf import PageObject, PdfReader
from reportlab.pdfgen.canvas import Canvas

from ..config import COLOR_TEXTO_RGB, FUENTE, TAMANO_FUENTE
from ..modelos import Anotacion

MITAD_ALTURA_DIGITO = 0.35     # fracción del tamaño de fuente


def crear_capa(ancho: float, alto: float, anotaciones: Sequence[Anotacion]) -> PageObject:
    buffer = io.BytesIO()
    lienzo = Canvas(buffer, pagesize=(ancho, alto))
    lienzo.setFont(FUENTE, TAMANO_FUENTE)
    lienzo.setFillColorRGB(*COLOR_TEXTO_RGB)
    for anotacion in anotaciones:
        _dibujar(lienzo, alto, anotacion)
    lienzo.save()
    return PdfReader(io.BytesIO(buffer.getvalue())).pages[0]


def _dibujar(lienzo: Canvas, alto_pagina: float, anotacion: Anotacion) -> None:
    """pdfplumber mide 'y' desde arriba y reportlab desde abajo; la línea base baja media altura
    de dígito para que el número quede centrado en su celda."""
    ubicacion = anotacion.ubicacion
    linea_base = alto_pagina - ubicacion.y_centro - MITAD_ALTURA_DIGITO * TAMANO_FUENTE
    for columna, texto in anotacion.textos.items():
        lienzo.drawCentredString(ubicacion.x_por_columna[columna], linea_base, texto)
