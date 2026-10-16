"""Estructuras que comparten la detección, la escritura y la interfaz."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Alumno:
    numero: str
    marca: str          # columna sin título entre N° y CODE (p. ej. "F")
    codigo: str
    apellidos: str
    nombres: str

    @property
    def nombre_completo(self) -> str:
        if not self.nombres:
            return self.apellidos
        return f"{self.apellidos}, {self.nombres}"


@dataclass(frozen=True)
class Ubicacion:
    """Dónde escribir los valores de un alumno, en puntos PDF con 'y' medida desde arriba."""
    pagina: int
    y_centro: float
    x_por_columna: Mapping[str, float]


@dataclass(frozen=True)
class FilaPlantilla:
    alumno: Alumno
    ubicacion: Ubicacion


@dataclass(frozen=True)
class Plantilla:
    filas: tuple[FilaPlantilla, ...]
    ya_tiene_valores: bool      # la grilla ya trae texto, p. ej. un PDF generado antes
    rotulos_criterios: tuple[str, ...]      # como los imprime el PDF, p. ej. (..., "GV")


@dataclass(frozen=True)
class Anotacion:
    """Textos a escribir en la fila de un alumno, por columna de la grilla."""
    ubicacion: Ubicacion
    textos: Mapping[str, str]
