"""Reglas de calificación: validación de cada criterio, TOTAL, FR y formato."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .config import (COLUMNA_FINAL, COLUMNA_TOTAL, CRITERIOS, DIVISOR_FINAL,
                     FINAL_APROBATORIO, NOTA_MAXIMA, NOTA_MINIMA)
from .errores import CalificacionInvalida

DECIMALES_MAXIMOS = 2


@dataclass(frozen=True)
class Calificacion:
    notas: tuple[float, ...]        # en el orden de CRITERIOS

    @property
    def total(self) -> float:
        return sum(self.notas)

    @property
    def final(self) -> float:
        return self.total / DIVISOR_FINAL

    @property
    def aprobada(self) -> bool:
        return self.final >= FINAL_APROBATORIO

    def textos_por_columna(self) -> dict[str, str]:
        textos = {criterio: formatear(nota) for criterio, nota in zip(CRITERIOS, self.notas)}
        textos[COLUMNA_TOTAL] = formatear(self.total)
        textos[COLUMNA_FINAL] = formatear(self.final)
        return textos


@dataclass(frozen=True)
class Revision:
    """Resultado de revisar todas las filas antes de generar el PDF."""
    calificaciones: Mapping[int, Calificacion]     # índice de fila -> calificación
    invalidas: tuple[int, ...]
    vacias: tuple[int, ...]


def es_nota_valida(texto: str) -> bool:
    return _convertir(texto) is not None


def esta_vacia(textos: Sequence[str]) -> bool:
    return not any(texto.strip() for texto in textos)


def calificar(textos: Sequence[str]) -> Calificacion:
    """Convierte los textos ingresados (uno por criterio) en una calificación."""
    notas = [_convertir(texto) for texto in textos]
    if len(notas) != len(CRITERIOS) or None in notas:
        raise CalificacionInvalida(
            f"Cada criterio debe tener una nota entre {NOTA_MINIMA} y {NOTA_MAXIMA}.")
    return Calificacion(tuple(notas))


def revisar(textos_por_fila: Sequence[Sequence[str]]) -> Revision:
    calificaciones, invalidas, vacias = {}, [], []
    for indice, textos in enumerate(textos_por_fila):
        if esta_vacia(textos):
            vacias.append(indice)
            continue
        try:
            calificaciones[indice] = calificar(textos)
        except CalificacionInvalida:
            invalidas.append(indice)
    return Revision(calificaciones, tuple(invalidas), tuple(vacias))


def formatear(valor: float) -> str:
    """16.0 -> '16', 8.50 -> '8.5'."""
    return f"{valor:.{DECIMALES_MAXIMOS}f}".rstrip("0").rstrip(".")


def _convertir(texto: str) -> float | None:
    """'4', '4.5' o '4,5' -> número; None si no es número o está fuera de rango."""
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        return None
    return valor if NOTA_MINIMA <= valor <= NOTA_MAXIMA else None
