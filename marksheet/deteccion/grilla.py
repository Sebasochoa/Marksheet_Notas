"""Ubicación de la grilla de notas: encabezado, columnas y filas."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from ..config import COLUMNAS_GRILLA, CRITERIOS
from .geometria import (Borde, Intervalo, Palabra, fusionar_cercanos, intervalo_que_contiene,
                        punto_medio)
from .renglones import RenglonAlumno

TOLERANCIA_LINEA = 1.5             # pt: bordes más cercanos que esto son la misma línea
MARGEN_BUSQUEDA_COLUMNAS = 40.0    # pt alrededor de los rótulos donde se buscan verticales
HOLGURA_EXTENSION = 1.0            # pt al comparar horizontales con la altura de la grilla
SEPARACION_SIN_LINEAS = 2.0        # pt entre el primer rótulo y el borde supuesto de la grilla


@dataclass(frozen=True)
class Grilla:
    x_por_columna: Mapping[str, float]     # centro horizontal de cada columna
    borde_izquierdo: float
    fin_encabezado: float
    bottom: float
    cortes_filas: tuple[float, ...]        # 'top' de cada línea horizontal

    def centros_de_filas(self, renglones: Sequence[RenglonAlumno]) -> list[float]:
        """Centro vertical de la celda de cada alumno; si las líneas no le dan a cada alumno su
        propia celda, se usa el centro de su renglón de texto."""
        celdas = [intervalo_que_contiene(self.cortes_filas, r.centro_y) for r in renglones]
        if None in celdas or len(set(celdas)) < len(celdas):
            return [r.centro_y for r in renglones]
        return [punto_medio(celda) for celda in celdas]


def buscar_encabezado(renglones: Sequence[Sequence[Palabra]]) -> dict[str, Palabra] | None:
    """El encabezado es el único renglón con todas las columnas juntas (la leyenda inferior
    repite IC, DM, PR... pero cada sigla en su propio renglón)."""
    for renglon in renglones:
        por_rotulo = {_normalizar_rotulo(p.texto): p for p in renglon}
        if all(columna in por_rotulo for columna in COLUMNAS_GRILLA):
            return {columna: por_rotulo[columna] for columna in COLUMNAS_GRILLA}
    return None


def construir_grilla(encabezado: Mapping[str, Palabra], bordes: Sequence[Borde],
                     alto_pagina: float) -> Grilla:
    verticales = _verticales_que_cruzan(encabezado, bordes)
    if not verticales:
        return _grilla_sin_lineas(encabezado, alto_pagina)
    cortes_x = fusionar_cercanos((b.x0 for b in verticales), TOLERANCIA_LINEA)
    x_por_columna = _centros_de_columnas(encabezado, cortes_x)
    extension = (min(b.top for b in verticales), max(b.bottom for b in verticales))
    return Grilla(
        x_por_columna=MappingProxyType(x_por_columna),
        borde_izquierdo=cortes_x[0],
        fin_encabezado=_fin_encabezado(encabezado),
        bottom=extension[1],
        cortes_filas=_cortes_de_filas(bordes, x_por_columna[CRITERIOS[0]], extension),
    )


def _normalizar_rotulo(texto: str) -> str:
    return texto.strip().upper().rstrip("*")          # "FR*" -> "FR"


def _fin_encabezado(encabezado: Mapping[str, Palabra]) -> float:
    return max(p.bottom for p in encabezado.values())


def _verticales_que_cruzan(encabezado: Mapping[str, Palabra],
                           bordes: Sequence[Borde]) -> list[Borde]:
    rotulos = list(encabezado.values())
    y_rotulos = rotulos[0].centro_y
    x_min = min(p.x0 for p in rotulos) - MARGEN_BUSQUEDA_COLUMNAS
    x_max = max(p.x1 for p in rotulos) + MARGEN_BUSQUEDA_COLUMNAS
    return [b for b in bordes
            if b.vertical and x_min <= b.x0 <= x_max and b.top <= y_rotulos <= b.bottom]


def _centros_de_columnas(encabezado: Mapping[str, Palabra],
                         cortes_x: Sequence[float]) -> dict[str, float]:
    """Centro de la celda de cada rótulo; si las líneas no separan una columna por rótulo,
    se usa el centro del propio rótulo."""
    celdas = {c: intervalo_que_contiene(cortes_x, p.centro_x) for c, p in encabezado.items()}
    if None in celdas.values() or len(set(celdas.values())) < len(celdas):
        return _centros_de_rotulos(encabezado)
    return {columna: punto_medio(celda) for columna, celda in celdas.items()}


def _centros_de_rotulos(encabezado: Mapping[str, Palabra]) -> dict[str, float]:
    return {columna: palabra.centro_x for columna, palabra in encabezado.items()}


def _cortes_de_filas(bordes: Sequence[Borde], x_referencia: float,
                     extension: Intervalo) -> tuple[float, ...]:
    """'top' de las líneas horizontales que cruzan la columna de referencia dentro de la grilla."""
    arriba, abajo = extension
    tops = (b.top for b in bordes
            if not b.vertical and b.x0 <= x_referencia <= b.x1
            and arriba - HOLGURA_EXTENSION <= b.top <= abajo + HOLGURA_EXTENSION)
    return tuple(fusionar_cercanos(tops, TOLERANCIA_LINEA))


def _grilla_sin_lineas(encabezado: Mapping[str, Palabra], alto_pagina: float) -> Grilla:
    """Sin líneas vectoriales: columnas centradas en sus rótulos y filas por renglón de texto."""
    primer_rotulo = min(p.x0 for p in encabezado.values())
    return Grilla(
        x_por_columna=MappingProxyType(_centros_de_rotulos(encabezado)),
        borde_izquierdo=primer_rotulo - SEPARACION_SIN_LINEAS,
        fin_encabezado=_fin_encabezado(encabezado),
        bottom=alto_pagina,
        cortes_filas=(),
    )
