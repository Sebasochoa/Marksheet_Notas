"""Superpone las anotaciones sobre el PDF original y lo guarda con su mismo cifrado."""
from __future__ import annotations

import io
from collections import defaultdict
from typing import Sequence

from pypdf import PageObject, PdfReader, PdfWriter

from ..errores import FormatoNoSoportado
from ..modelos import Anotacion
from . import cifrado
from .capa import crear_capa

CLAVE_TIPO = "/Type"     # entrada estructural del diccionario Info, no es un metadato


def escribir_anotaciones(pdf_bytes: bytes, anotaciones: Sequence[Anotacion],
                         ruta_salida: str) -> None:
    lector, proteccion = cifrado.abrir_descifrado(pdf_bytes)
    escritor = PdfWriter()
    anotaciones_por_pagina = _agrupar_por_pagina(anotaciones)
    for indice, pagina in enumerate(lector.pages):
        if indice in anotaciones_por_pagina:
            pagina.merge_page(_capa_para(pagina, anotaciones_por_pagina[indice]))
        escritor.add_page(pagina)
    _copiar_metadatos(lector, escritor)
    if proteccion is not None:
        cifrado.aplicar(escritor, proteccion)
    _guardar(escritor, ruta_salida)


def _agrupar_por_pagina(anotaciones: Sequence[Anotacion]) -> dict[int, list[Anotacion]]:
    por_pagina: dict[int, list[Anotacion]] = defaultdict(list)
    for anotacion in anotaciones:
        por_pagina[anotacion.ubicacion.pagina].append(anotacion)
    return por_pagina


def _capa_para(pagina: PageObject, anotaciones: Sequence[Anotacion]) -> PageObject:
    caja = pagina.mediabox
    if float(caja.left) or float(caja.bottom):
        raise FormatoNoSoportado("La página tiene la MediaBox desplazada del origen.")
    return crear_capa(float(caja.width), float(caja.height), anotaciones)


def _copiar_metadatos(lector: PdfReader, escritor: PdfWriter) -> None:
    if lector.metadata:
        escritor.add_metadata({clave: str(valor) for clave, valor in lector.metadata.items()
                               if clave != CLAVE_TIPO})


def _guardar(escritor: PdfWriter, ruta: str) -> None:
    """Arma el PDF en memoria antes de abrir el archivo: si algo falla, no queda a medio escribir."""
    buffer = io.BytesIO()
    escritor.write(buffer)
    with open(ruta, "wb") as archivo:
        archivo.write(buffer.getvalue())
