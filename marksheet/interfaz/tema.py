"""Colores, tipografía, iconos y escala de la interfaz (tema oscuro neumórfico)."""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk

FONDO = "#1f2229"
LUZ = "#2b2f38"            # sombra clara (arriba-izquierda)
SOMBRA = "#14161a"         # sombra oscura (abajo-derecha)
HOVER = "#23262e"
LINEA = "#262930"
TEXTO = "#e8e6e3"
TEXTO_SUAVE = "#a3a8b2"
TEXTO_TENUE = "#6e7480"
CIAN = "#2cc4ef"
CIAN_CLARO = "#7fdcf7"
CIAN_OSCURO = "#0a8fb8"
CIAN_FONDO = "#1d3640"
CIAN_RESPLANDOR = "#163a48"
TINTA_SOBRE_CIAN = "#06212b"
MAGENTA = "#ff4d94"
MAGENTA_CLARO = "#ff8fbb"
MAGENTA_FONDO = "#3a2230"
AMARILLO = "#f5c84b"
AMARILLO_CLARO = "#f9da85"
AMARILLO_FONDO = "#3a3424"
ESQ_OSCURO = "#292d35"
ESQ_CLARO = "#363b46"
ESQ_TRAZO = "#3a3f4a"

FAMILIAS_SERIF = ("Source Serif 4", "Source Serif Pro", "Georgia", "Cambria", "Times New Roman")
FAMILIA_SEMINEGRITA = "Source Serif 4 Semibold"
FAMILIAS_ICONOS = ("Segoe Fluent Icons", "Segoe MDL2 Assets")
CARPETA_FUENTES = Path(__file__).with_name("fuentes")
FR_PRIVATE = 0x10

# nombre: (glifo Segoe Fluent/MDL2, respaldo Unicode si no hay fuente de iconos)
ICONOS = {
    "abrir": ("\uE8E5", "⇪"), "guardar": ("\uE74E", "⤓"), "pdf": ("\uEA90", "▤"),
    "documento": ("\uE8A5", "▤"), "subir": ("\uE898", "⇪"), "alumnos": ("\uE716", "☰"),
    "completas": ("\uE930", "✓"), "revisar": ("\uE783", "!"), "teclado": ("\uE765", "⌨"),
    "info": ("\uE946", "i"), "error": ("\uE783", "!"), "aviso": ("\uE7BA", "!"),
    "pregunta": ("\uE9CE", "?"), "ok": ("\uE930", "✓"), "externo": ("\uE8A7", "↗"),
    "cerrar": ("\uE711", "✕"), "hecho": ("\uE73E", "✓"), "actual": ("\uE72A", "→"),
    "pendiente": ("\uEA3A", "○"), "carga": ("\uE895", "↻"), "paginas": ("\uE8A4", "▤"),
}

ESCALA = 1.0
fuentes: "Fuentes" = None  # type: ignore[assignment]


def px(valor: float) -> int:
    """Píxeles de diseño (a 96 ppp) convertidos a píxeles reales de la pantalla."""
    return max(1, round(valor * ESCALA))


def mezclar(color_a: str, color_b: str, t: float) -> str:
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def glifo(nombre: str) -> str:
    fluent, respaldo = ICONOS[nombre]
    return fluent if fuentes.familia_iconos else respaldo


def fuente_icono(tamano: int) -> tkfont.Font:
    return fuentes.icono(tamano)


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
        self._raiz = raiz
        disponibles = set(tkfont.families(raiz))
        self.base = next((f for f in FAMILIAS_SERIF if f in disponibles), "Times")
        self._semi = FAMILIA_SEMINEGRITA if FAMILIA_SEMINEGRITA in disponibles else None
        self.familia_iconos = next((f for f in FAMILIAS_ICONOS if f in disponibles), None)
        self._iconos: dict[int, tkfont.Font] = {}
        f = self._fuente
        self.marca = f(14, fuerte=True)
        self.marca_italica = f(10, italica=True)
        self.h1 = f(30, fuerte=True)
        self.h1_italica = f(30, italica=True)
        self.h2 = f(19, fuerte=True)
        self.cifra = f(17, fuerte=True)
        self.zona = f(14, fuerte=True)
        self.dialogo = f(14, fuerte=True)
        self.cuerpo_grande = f(12)
        self.cuerpo = f(11)
        self.celda = f(11)
        self.celda_fuerte = f(11, fuerte=True)
        self.pequena = f(10)
        self.boton = f(10, fuerte=True)
        self.mini = f(8)
        self.mini_fuerte = f(8, fuerte=True)
        for nombre in ("TkDefaultFont", "TkTextFont"):
            tkfont.nametofont(nombre).configure(family=self.base, size=10)

    def _fuente(self, tamano: int, fuerte: bool = False, italica: bool = False) -> tkfont.Font:
        familia, peso = self.base, "bold" if fuerte else "normal"
        if fuerte and self._semi:
            familia, peso = self._semi, "normal"
        return tkfont.Font(root=self._raiz, family=familia, size=tamano, weight=peso,
                           slant="italic" if italica else "roman")

    def icono(self, tamano: int) -> tkfont.Font:
        if tamano not in self._iconos:
            familia = self.familia_iconos or self.base
            self._iconos[tamano] = tkfont.Font(root=self._raiz, family=familia, size=tamano)
        return self._iconos[tamano]


def configurar(raiz) -> None:
    global ESCALA, fuentes
    ESCALA = raiz.winfo_fpixels("1i") / 96
    fuentes = Fuentes(raiz)
    raiz.configure(bg=FONDO)
    raiz.option_add("*Background", FONDO)
    raiz.option_add("*Foreground", TEXTO)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure("Vertical.TScrollbar", background="#2f333c", troughcolor=FONDO,
                     bordercolor=FONDO, lightcolor="#2f333c", darkcolor="#2f333c",
                     arrowcolor=TEXTO_SUAVE, gripcount=0, arrowsize=px(12))
    estilo.map("Vertical.TScrollbar", background=[("active", "#3b404b")],
               lightcolor=[("active", "#3b404b")], darkcolor=[("active", "#3b404b")])
