"""Zona para abrir el PDF: clic para elegirlo o arrastrar y soltar (si hay tkinterdnd2)."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from . import tema
from .neu import superficie

ANCHO = 600
ALTO = 210
LADO_ICONO = 64


class ZonaArchivo(tk.Canvas):
    def __init__(self, padre: tk.Misc, al_elegir: Callable[[], None],
                 al_soltar: Callable[[str], None]):
        self._ancho, self._alto = tema.px(ANCHO), tema.px(ALTO)
        super().__init__(padre, width=self._ancho, height=self._alto, bg=tema.FONDO,
                         highlightthickness=0, bd=0, cursor="hand2")
        self._activa = False
        self._fotos = []
        self._con_arrastre = habilitar_arrastre(self, al_soltar, self._resaltar)
        self.bind("<Enter>", lambda _e: self._resaltar(True))
        self.bind("<Leave>", lambda _e: self._resaltar(False))
        self.bind("<Button-1>", lambda _e: al_elegir())
        self._dibujar()

    def _resaltar(self, activa: bool) -> None:
        if activa != self._activa:
            self._activa = activa
            self._dibujar()

    def _dibujar(self) -> None:
        px, f = tema.px, tema.fuentes
        self.delete("all")
        fondo = superficie(self._ancho, self._alto, px(22), "hundido", distancia=px(4),
                           desenfoque=px(6), anillo=tema.CIAN if self._activa else None)
        d, b = px(3), px(5)
        m = d + 2 * b
        lado = px(LADO_ICONO)
        icono = superficie(lado + 2 * m, lado + 2 * m, px(20), "elevado", margen=m,
                           distancia=d, desenfoque=b, relleno=tema.CIAN_FONDO)
        self._fotos = [fondo, icono]
        cx = self._ancho // 2
        self.create_image(0, 0, anchor="nw", image=fondo)
        self.create_image(cx, px(24) + lado // 2, image=icono)
        self.create_text(cx, px(24) + lado // 2, text=tema.glifo("subir"),
                         fill=tema.CIAN_CLARO if self._activa else tema.CIAN,
                         font=tema.fuente_icono(24))
        if self._con_arrastre:
            titulo, detalle = "Arrastra el PDF aquí", "o haz clic para elegirlo en tu equipo"
        else:
            titulo, detalle = "Elige el PDF de la Mark Sheet", "Haz clic aquí para buscarlo en tu equipo"
        self.create_text(cx, px(126), text=titulo, font=f.zona, fill=tema.TEXTO)
        self.create_text(cx, px(154), text=detalle, font=f.cuerpo, fill=tema.TEXTO_SUAVE)


def habilitar_arrastre(widget: tk.Widget, al_soltar: Callable[[str], None],
                       al_resaltar: Callable[[bool], None]) -> bool:
    """Registra el widget como destino de archivos con tkdnd. False si no está instalado."""
    try:
        from tkinterdnd2 import TkinterDnD
        TkinterDnD._require(widget.winfo_toplevel())
    except Exception:
        return False

    def entrar(*_):
        al_resaltar(True)
        return "copy"

    def salir(*_):
        al_resaltar(False)
        return ""

    def soltar(datos):
        al_resaltar(False)
        pdfs = [r for r in widget.tk.splitlist(datos) if r.lower().endswith(".pdf")]
        if pdfs:
            widget.after_idle(al_soltar, pdfs[0])
        return "copy"

    try:
        widget.tk.call("tkdnd::drop_target", "register", widget._w, "DND_Files")
        for evento, funcion, sufijo in (("<<DropEnter>>", entrar, ""),
                                        ("<<DropLeave>>", salir, ""),
                                        ("<<Drop:DND_Files>>", soltar, " %D")):
            widget.tk.call("bind", widget._w, evento, widget.register(funcion) + sufijo)
    except tk.TclError:
        return False
    return True