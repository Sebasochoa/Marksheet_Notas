"""Primitivas geométricas de la página, independientes de pdfplumber."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

Intervalo = tuple[float, float]


@dataclass(frozen=True)
class Palabra:
    texto: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def centro_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def centro_y(self) -> float:
        return (self.top + self.bottom) / 2


@dataclass(frozen=True)
class Borde:
    vertical: bool
    x0: float
    x1: float
    top: float
    bottom: float


def fusionar_cercanos(valores: Iterable[float], tolerancia: float) -> list[float]:
    """Agrupa valores separados por menos de 'tolerancia' y devuelve el centro de cada grupo.

    Cada línea de la grilla es un rectángulo de 0.5 pt, es decir, dos bordes casi iguales.
    """
    grupos: list[list[float]] = []
    for valor in sorted(valores):
        if grupos and valor - grupos[-1][-1] <= tolerancia:
            grupos[-1].append(valor)
        else:
            grupos.append([valor])
    return [sum(grupo) / len(grupo) for grupo in grupos]


def intervalo_que_contiene(cortes: Sequence[float], valor: float) -> Intervalo | None:
    for inicio, fin in zip(cortes, cortes[1:]):
        if inicio < valor < fin:
            return inicio, fin
    return None


def punto_medio(intervalo: Intervalo) -> float:
    inicio, fin = intervalo
    return (inicio + fin) / 2
