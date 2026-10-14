"""Zona para abrir el PDF: clic para elegirlo o arrastrar y soltar (si hay tkinterdnd2)."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from . import tema

ANCHO = 720
ALTO = 112


class ZonaArchivo(tk.Canvas):
    def __init__(self, padre: tk.Misc, al_elegir: Callable[[], None],
                 al_soltar: Callable[[str], None]):
        super().__init__(padre, width=tema.px(ANCHO), height=tema.px(ALTO), bg=tema.FONDO,
                         highlightthickness=0, bd=0, cursor="hand2")
        self._activa = False
        self._con_arrastre = habilitar_arrastre(self, al_soltar, self._resaltar)
        self.bind("<Configure>", lambda _e: self._dibujar())
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
        ancho = max(self.winfo_width(), 2) if self.winfo_width() > 1 else px(ANCHO)
        alto = max(self.winfo_height(), 2) if self.winfo_height() > 1 else px(ALTO)
        fondo = tema.ACENTO_100 if self._activa else tema.SUPERFICIE
        borde = tema.ACENTO if self._activa else tema.NEUTRO_400
        grosor = max(1, round(1.5 * tema.ESCALA))
        self.create_rectangle(grosor, grosor, ancho - grosor, alto - grosor, fill=fondo,
                              outline=borde, dash=(4, 3), width=grosor)
        x, y = px(30), (alto - px(46)) // 2
        self.create_rectangle(x, y, x + px(36), y + px(46), outline=tema.ACENTO, width=grosor,
                              fill=fondo)
        self.create_text(x + px(18), y + px(30), text="PDF", fill=tema.ACENTO_700,
                         font=f.mini_fuerte)
        if self._con_arrastre:
            titulo, detalle = "Arrastra el PDF aquí", "o haz clic para elegirlo en tu equipo"
        else:
            titulo, detalle = "Elige el PDF de la Mark Sheet", "Haz clic aquí para buscarlo en tu equipo"
        texto_x = x + px(56)
        self.create_text(texto_x, alto / 2 - px(11), text=titulo, anchor="w", font=f.zona,
                         fill=tema.TEXTO)
        self.create_text(texto_x, alto / 2 + px(13), text=detalle, anchor="w", font=f.cuerpo,
                         fill=tema.NEUTRO_700)


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
