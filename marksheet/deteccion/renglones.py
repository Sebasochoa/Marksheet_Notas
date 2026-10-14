"""Lectura de las filas de texto de la plantilla: N°, marca, código y nombre."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .geometria import Palabra

TOLERANCIA_RENGLON = 2.0              # pt de diferencia en 'top' dentro de un mismo renglón
PATRON_NUMERO = re.compile(r"^\d{1,3}$")
PATRON_CODIGO = re.compile(r"^\d{4,}$")
MINIMO_FILAS_ALINEADAS = 2
PROPORCION_FILAS_ALINEADAS = 0.6      # filas que deben coincidir en el inicio de FIRST NAME
HOLGURA_INICIO_COLUMNA = 1.0          # pt, por el redondeo de las x


@dataclass(frozen=True)
class RenglonAlumno:
    numero: str
    marca: str
    codigo: str
    palabras_nombre: tuple[Palabra, ...]
    top: float
    bottom: float

    @property
    def centro_y(self) -> float:
        return (self.top + self.bottom) / 2


def agrupar_en_renglones(palabras: Sequence[Palabra]) -> list[list[Palabra]]:
    renglones: list[list[Palabra]] = []
    for palabra in sorted(palabras, key=lambda p: (p.top, p.x0)):
        if renglones and abs(palabra.top - renglones[-1][0].top) <= TOLERANCIA_RENGLON:
            renglones[-1].append(palabra)
        else:
            renglones.append([palabra])
    return [sorted(renglon, key=lambda p: p.x0) for renglon in renglones]


def leer_renglon_alumno(palabras: Sequence[Palabra]) -> RenglonAlumno | None:
    """Interpreta 'N° [marca] CÓDIGO APELLIDOS NOMBRES'; None si no es el renglón de un alumno."""
    if not palabras or not PATRON_NUMERO.match(palabras[0].texto):
        return None
    posicion_codigo = _posicion_del_codigo(palabras)
    if posicion_codigo is None or posicion_codigo == len(palabras) - 1:
        return None
    primera = palabras[0]
    return RenglonAlumno(
        numero=primera.texto,
        marca=_unir(palabras[1:posicion_codigo]),
        codigo=palabras[posicion_codigo].texto,
        palabras_nombre=tuple(palabras[posicion_codigo + 1:]),
        top=primera.top,
        bottom=primera.bottom,
    )


def separar_apellidos_y_nombres(renglones: Sequence[RenglonAlumno]) -> list[tuple[str, str]]:
    """(apellidos, nombres) de cada renglón según dónde empieza la columna FIRST NAME."""
    inicio_nombres = _inicio_columna_nombres(renglones)
    divisiones = []
    for renglon in renglones:
        palabras = renglon.palabras_nombre
        if inicio_nombres is None:
            corte = _corte_por_mayor_hueco(palabras)
        else:
            corte = _corte_por_columna(palabras, inicio_nombres)
        divisiones.append((_unir(palabras[:corte]), _unir(palabras[corte:])))
    return divisiones


def _posicion_del_codigo(palabras: Sequence[Palabra]) -> int | None:
    return next((i for i in range(1, len(palabras)) if PATRON_CODIGO.match(palabras[i].texto)),
                None)


def _inicio_columna_nombres(renglones: Sequence[RenglonAlumno]) -> float | None:
    """La columna FIRST NAME está alineada a la izquierda: su x0 es la que más se repite entre
    las palabras que no abren el nombre. None si no hay filas suficientes para afirmarlo."""
    conteo = Counter(round(p.x0) for r in renglones for p in r.palabras_nombre[1:])
    if not conteo:
        return None
    x_mas_comun, repeticiones = conteo.most_common(1)[0]
    minimo = max(MINIMO_FILAS_ALINEADAS, PROPORCION_FILAS_ALINEADAS * len(renglones))
    if repeticiones < minimo:
        return None
    return x_mas_comun - HOLGURA_INICIO_COLUMNA


def _corte_por_columna(palabras: Sequence[Palabra], inicio_nombres: float) -> int:
    return next((i for i, p in enumerate(palabras) if p.x0 >= inicio_nombres), len(palabras))


def _corte_por_mayor_hueco(palabras: Sequence[Palabra]) -> int:
    if len(palabras) < 2:
        return len(palabras)
    huecos = [siguiente.x0 - actual.x1 for actual, siguiente in zip(palabras, palabras[1:])]
    return huecos.index(max(huecos)) + 1


def _unir(palabras: Sequence[Palabra]) -> str:
    return " ".join(p.texto for p in palabras)
