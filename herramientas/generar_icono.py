"""Genera el ícono: una hoja con filas (nombre + celdas de nota) y una celda recién llenada.

Un solo color (cian); la hoja va calada, así que se ve bien sobre barras oscuras y claras.
Cada tamaño chico tiene su propio dibujo sobre una grilla entera para que los bordes queden
nítidos: escalar el diseño grande a 16 px lo vuelve una mancha.

Solo hace falta para cambiar el ícono; el .ico ya generado está en marksheet/interfaz/recursos.
Uso: python herramientas/generar_icono.py  (requiere cairosvg, que en Windows necesita la DLL de
Cairo, por ejemplo la que instala GTK).
"""
import io
from pathlib import Path

import cairosvg
from PIL import Image

CIAN = "#2cc4ef"
TAMANOS = (16, 20, 24, 32, 40, 48, 64, 128, 256)
DESTINO = Path(__file__).resolve().parent.parent / "marksheet" / "interfaz" / "recursos"


def rect_redondeado(x, y, ancho, alto, r):
    return (f"M{x + r} {y} H{x + ancho - r} A{r} {r} 0 0 1 {x + ancho} {y + r} V{y + alto - r} "
            f"A{r} {r} 0 0 1 {x + ancho - r} {y + alto} H{x + r} A{r} {r} 0 0 1 {x} {y + alto - r} "
            f"V{y + r} A{r} {r} 0 0 1 {x + r} {y} Z")


def svg(lado, azulejo, hoja, pliegue, elementos, nitido=False):
    modo = ' shape-rendering="crispEdges"' if nitido else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}"{modo}>'
            f'<path fill-rule="evenodd" fill="{CIAN}" shape-rendering="geometricPrecision" '
            f'd="{azulejo} {hoja}"/><path d="{pliegue}" fill="{CIAN}"/>'
            f'<g fill="{CIAN}">{elementos}</g></svg>')


def completo():
    """48-256 px: tres filas con nombre y dos celdas; la del medio a la derecha, llena."""
    elementos = []
    for fila, centro in enumerate((102, 144, 186)):
        elementos.append(f'<rect x="72" y="{centro - 6}" width="38" height="12" rx="6"/>')
        for columna, x in enumerate((124, 162)):
            if fila == 1 and columna == 1:
                elementos.append(f'<rect x="{x}" y="{centro - 17}" width="34" height="34" rx="8"/>')
            else:
                elementos.append(f'<rect x="{x + 3.5}" y="{centro - 13.5}" width="27" height="27" '
                                 f'rx="5" fill="none" stroke="{CIAN}" stroke-width="7"/>')
    return svg(256, rect_redondeado(8, 8, 240, 240, 52),
               "M68 28 H164 L208 72 V216 a12 12 0 0 1 -12 12 H68 a12 12 0 0 1 -12 -12 V40 "
               "a12 12 0 0 1 12 -12 Z",
               "M164 28 V60 a12 12 0 0 0 12 12 H208 Z", "".join(elementos))


def medio():
    """24 px (pantallas al 150 %): una columna de celdas de 3x3, la del medio llena."""
    elementos = []
    for fila, arriba in enumerate((8, 12, 16)):
        elementos.append(f'<rect x="7" y="{arriba + 1}" width="5" height="1"/>')
        if fila == 1:
            elementos.append(f'<rect x="13" y="{arriba}" width="3" height="3"/>')
        else:
            elementos.append(f'<path fill-rule="evenodd" d="M13 {arriba} h3 v3 h-3 Z M14 {arriba + 1} h1 v1 h-1 Z"/>')
    return svg(24, rect_redondeado(0, 0, 24, 24, 5), "M4 2 H15 L19 6 V22 H4 Z",
               "M15 2 V6 H19 Z", "".join(elementos), nitido=True)


def reducido():
    """16-20 px y 32 px (2x exacto): tres líneas y una celda llena."""
    elementos = ('<rect x="5" y="6" width="3" height="1"/><rect x="5" y="9" width="3" height="1"/>'
                 '<rect x="5" y="12" width="3" height="1"/><rect x="9" y="8" width="3" height="3"/>')
    return svg(16, rect_redondeado(0, 0, 16, 16, 3), "M3 1 H10 L13 4 V15 H3 Z",
               "M10 1 V4 H13 Z", elementos, nitido=True)


def diseno_para(lado):
    if lado == 24:
        return medio()
    return reducido() if lado <= 32 else completo()


def rasterizar(fuente, lado):
    png = cairosvg.svg2png(bytestring=fuente.encode(), output_width=lado, output_height=lado)
    return Image.open(io.BytesIO(png)).convert("RGBA")


if __name__ == "__main__":
    DESTINO.mkdir(exist_ok=True)
    (DESTINO / "icono.svg").write_text(completo(), encoding="utf-8")
    imagenes = {lado: rasterizar(diseno_para(lado), lado) for lado in TAMANOS}
    imagenes[256].save(DESTINO / "icono.png")
    imagenes[256].save(DESTINO / "icono.ico", format="ICO", sizes=[(t, t) for t in TAMANOS],
                       append_images=[imagenes[t] for t in TAMANOS if t != 256])
    print(f"Ícono generado en {DESTINO}")
