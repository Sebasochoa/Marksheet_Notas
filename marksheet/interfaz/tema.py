"""Colores, tipografía, escala y estilos ttk de la interfaz (sistema Broadsheet)."""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk

FONDO = "#f3f2f2"
SUPERFICIE = "#eae9e9"
TEXTO = "#201e1d"
ACENTO = "#0088b0"
ACENTO_100 = "#e9f8ff"
ACENTO_600 = "#1186ac"
ACENTO_700 = "#006786"
MAGENTA = "#d6006c"
MAGENTA_100 = "#fff1f4"
MAGENTA_700 = "#aa0b56"
NEUTRO_100 = "#f8f4f4"
NEUTRO_300 = "#d7d3d3"
NEUTRO_400 = "#bab6b6"
NEUTRO_500 = "#9b9797"
NEUTRO_700 = "#605d5d"
NEUTRO_800 = "#444141"
DIVISOR = "#d1d0cf"            # tinta al 16 % sobre el fondo
LINEA_FILA = "#e2e1e1"         # tinta al 8 %
TINTE_HOVER = "#e1e0e0"        # tinta al 7 %
TINTE_PRESION = "#d3d2d1"      # tinta al 14 %
SELECCION = "#aad2de"          # acento al 30 %
ACENTO_DESHABILITADO = "#86c2d4"   # acento al 45 % de opacidad

FAMILIAS_SERIF = ("Source Serif 4", "Source Serif Pro", "Georgia", "Cambria", "Times New Roman")
FAMILIA_SEMINEGRITA = "Source Serif 4 Semibold"
CARPETA_FUENTES = Path(__file__).with_name("fuentes")
FR_PRIVATE = 0x10

ESCALA = 1.0
fuentes: "Fuentes" = None  # type: ignore[assignment]


def px(valor: float) -> int:
    """Píxeles de diseño (a 96 ppp) convertidos a píxeles reales de la pantalla."""
    return max(1, round(valor * ESCALA))


def mezclar(color_a: str, color_b: str, t: float) -> str:
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def registrar_fuentes() -> None:
    """Carga Source Serif 4 desde interfaz/fuentes/ solo para este proceso (Windows)."""
    if sys.platform != "win32" or not CARPETA_FUENTES.is_dir():
        return
    for archivo in list(CARPETA_FUENTES.glob("*.ttf")) + list(CARPETA_FUENTES.glob("*.otf")):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(str(archivo), FR_PRIVATE, 0)
        except (AttributeError, OSError):
            pass


class Fuentes:
    def __init__(self, raiz):
        disponibles = set(tkfont.families(raiz))
        base = next((f for f in FAMILIAS_SERIF if f in disponibles), "Times")
        semi = FAMILIA_SEMINEGRITA if FAMILIA_SEMINEGRITA in disponibles else None

        def fuente(tamano: int, fuerte: bool = False, italica: bool = False) -> tkfont.Font:
            familia, peso = base, "bold" if fuerte else "normal"
            if fuerte and semi:
                familia, peso = semi, "normal"
            return tkfont.Font(root=raiz, family=familia, size=tamano, weight=peso,
                               slant="italic" if italica else "roman")

        self.marca = fuente(14, fuerte=True)
        self.marca_italica = fuente(14, italica=True)
        self.h1 = fuente(30, fuerte=True)
        self.h1_italica = fuente(30, italica=True)
        self.h2 = fuente(21, fuerte=True)
        self.zona = fuente(14, fuerte=True)
        self.dialogo = fuente(15, fuerte=True)
        self.cuerpo_grande = fuente(13)
        self.cuerpo = fuente(11)
        self.celda = fuente(11)
        self.celda_fuerte = fuente(11, fuerte=True)
        self.pequena = fuente(10)
        self.boton = fuente(10, fuerte=True)
        self.mini = fuente(8)
        self.mini_fuerte = fuente(8, fuerte=True)
        for nombre in ("TkDefaultFont", "TkTextFont"):
            tkfont.nametofont(nombre).configure(family=base, size=10)


def configurar(raiz) -> None:
    global ESCALA, fuentes
    ESCALA = raiz.winfo_fpixels("1i") / 96
    fuentes = Fuentes(raiz)
    raiz.configure(bg=FONDO)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure(".", background=FONDO, foreground=TEXTO, font=fuentes.cuerpo,
                     focuscolor=ACENTO)
    comun = dict(font=fuentes.boton, padding=(px(16), px(9)), borderwidth=1, relief="flat",
                 focusthickness=1)
    _boton(estilo, "Primario.TButton", ACENTO, FONDO, ACENTO, ACENTO_600, ACENTO_700,
           ACENTO_DESHABILITADO, FONDO, comun)
    _boton(estilo, "Secundario.TButton", FONDO, TEXTO, DIVISOR, TINTE_HOVER, TINTE_PRESION,
           FONDO, NEUTRO_500, comun)
    estilo.configure("Vertical.TScrollbar", background=NEUTRO_300, troughcolor=FONDO,
                     bordercolor=FONDO, lightcolor=NEUTRO_300, darkcolor=NEUTRO_300,
                     arrowcolor=NEUTRO_700, gripcount=0, arrowsize=px(12))
    estilo.map("Vertical.TScrollbar", background=[("active", NEUTRO_400)])


def _boton(estilo, nombre, fondo, tinta, borde, hover, presion, fondo_off, tinta_off, comun):
    estilo.configure(nombre, background=fondo, foreground=tinta, bordercolor=borde,
                     lightcolor=fondo, darkcolor=fondo, **comun)
    estados = [("disabled", fondo_off), ("pressed", presion), ("active", hover)]
    estilo.map(nombre, background=estados, lightcolor=estados, darkcolor=estados,
               foreground=[("disabled", tinta_off)],
               bordercolor=[("disabled", borde if borde != fondo else fondo_off),
                            ("pressed", borde if borde != fondo else presion),
                            ("active", borde if borde != fondo else hover)])
