"""Mark Sheet sintética con el layout del reporte real y alumnos ficticios."""
from __future__ import annotations

import io
from typing import Sequence

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

ANCHO, ALTO = 595.35, 842.0          # A4 del reporte original
GROSOR_LINEA = 0.5
CORTES_COLUMNAS = (392.70, 420.90, 449.15, 477.40, 505.65, 543.35, 573.90)
LINEAS_ENCABEZADO = (137.48, 147.50, 157.52)
ALTO_FILA = 14.2
BASE_ROTULOS, BASE_MAXIMOS, BASE_PRIMER_ALUMNO = 145.74, 155.76, 170.21
ROTULOS = ("IC", "DM", "PR", "LA", "TOTAL", "FR*")            # Juniors
ROTULOS_ADULTOS = ("IC", "DM", "PR", "GV", "TOTAL", "FR*")    # Grammar and Vocabulary
MAXIMOS = ("5", "5", "5", "5", "20", "10")
X_DATOS = (25.25, 50.30, 70.10, 134.95, 266.65)    # N°, marca, código, apellidos, nombres
PERMISOS_REPORTE = -12                               # imprimir y copiar sí; modificar no

ALUMNOS = (
    ("1", "", "100001", "PEREZ LOPEZ", "ANA MARIA"),
    ("2", "F", "100002", "DE LA CRUZ SOTO", "LUIS"),
    ("3", "", "100003", "QUISPE", "ROSA ELENA"),
)


def crear_pdf(algoritmo: str | None = "RC4-40", contrasena_propietario: str = "",
              paginas: int = 1, rotulos: Sequence[str] = ROTULOS) -> bytes:
    """Mark Sheet de 'paginas' hojas independientes, cifrada como el reporte si hay algoritmo."""
    escritor = PdfWriter()
    for _ in range(paginas):
        escritor.add_page(PdfReader(io.BytesIO(_dibujar_hoja(ALUMNOS, rotulos))).pages[0])
    if algoritmo is not None:
        escritor.encrypt("", contrasena_propietario, permissions_flag=PERMISOS_REPORTE,
                         algorithm=algoritmo)
    salida = io.BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def crear_pdf_sin_plantilla() -> bytes:
    buffer = io.BytesIO()
    lienzo = Canvas(buffer, pagesize=(ANCHO, ALTO))
    lienzo.drawString(72, 720, "Documento sin grilla de notas")
    lienzo.save()
    return buffer.getvalue()


def centros_columnas() -> list[float]:
    centros_lineas = [x + GROSOR_LINEA / 2 for x in CORTES_COLUMNAS]
    return [(a + b) / 2 for a, b in zip(centros_lineas, centros_lineas[1:])]


def centro_fila(indice: int) -> float:
    return _linea_sobre_alumno(indice) + GROSOR_LINEA / 2 + ALTO_FILA / 2


def _linea_sobre_alumno(indice: int) -> float:
    return LINEAS_ENCABEZADO[-1] + ALTO_FILA * indice


def _y(top: float) -> float:
    return ALTO - top


def _dibujar_hoja(alumnos: Sequence[tuple[str, ...]], rotulos: Sequence[str]) -> bytes:
    buffer = io.BytesIO()
    lienzo = Canvas(buffer, pagesize=(ANCHO, ALTO))
    _dibujar_grilla(lienzo, len(alumnos))
    _dibujar_encabezados(lienzo, rotulos)
    _dibujar_alumnos(lienzo, alumnos)
    _dibujar_leyenda(lienzo)
    lienzo.save()
    return buffer.getvalue()


def _dibujar_grilla(lienzo: Canvas, cantidad: int) -> None:
    horizontales = LINEAS_ENCABEZADO + tuple(_linea_sobre_alumno(i + 1) for i in range(cantidad))
    arriba, abajo = horizontales[0], horizontales[-1] + GROSOR_LINEA
    izquierda, derecha = CORTES_COLUMNAS[0], CORTES_COLUMNAS[-1] + GROSOR_LINEA
    for x in CORTES_COLUMNAS:
        lienzo.rect(x, _y(abajo), GROSOR_LINEA, abajo - arriba, stroke=0, fill=1)
    for top in horizontales:
        lienzo.rect(izquierda, _y(top + GROSOR_LINEA), derecha - izquierda, GROSOR_LINEA,
                    stroke=0, fill=1)


def _dibujar_encabezados(lienzo: Canvas, rotulos: Sequence[str]) -> None:
    lienzo.setFont("Helvetica-Bold", 8)
    for rotulo, maximo, centro in zip(rotulos, MAXIMOS, centros_columnas()):
        lienzo.drawCentredString(centro, _y(BASE_ROTULOS), rotulo)
        lienzo.drawCentredString(centro, _y(BASE_MAXIMOS), maximo)
    for texto, x in (("N0", 28.0), ("CODE", 85.57), ("LAST NAME", 172.07), ("FIRST NAME", 302.66)):
        lienzo.drawString(x, _y(BASE_MAXIMOS), texto)


def _dibujar_alumnos(lienzo: Canvas, alumnos: Sequence[tuple[str, ...]]) -> None:
    lienzo.setFont("Helvetica", 8)
    for indice, datos in enumerate(alumnos):
        base = _y(BASE_PRIMER_ALUMNO + ALTO_FILA * indice)
        for texto, x in zip(datos, X_DATOS):
            lienzo.drawString(x, base, texto)


def _dibujar_leyenda(lienzo: Canvas) -> None:
    siglas = (("IC", "Interactive Communication"), ("DM", "Discourse Management"),
              ("PR", "Pronunciation"), ("LA", "Language"), ("FR", "Final Result"))
    for indice, (sigla, significado) in enumerate(siglas):
        base = _y(630 + 12 * indice)
        lienzo.drawString(420, base, sigla)
        lienzo.drawString(445, base, "=")
        lienzo.drawString(460, base, significado)
