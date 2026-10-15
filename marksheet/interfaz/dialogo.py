"""Diálogos modales con el estilo de la interfaz (reemplazan a messagebox)."""
from __future__ import annotations

import tkinter as tk

from . import tema
from .neu import Boton, chip

TIPOS = {
    "error": ("error", tema.MAGENTA, tema.MAGENTA_FONDO),
    "aviso": ("aviso", tema.MAGENTA, tema.MAGENTA_FONDO),
    "pregunta": ("pregunta", tema.AMARILLO, tema.AMARILLO_FONDO),
    "ok": ("ok", tema.CIAN, tema.CIAN_FONDO),
}
ANCHO_TEXTO = 400


class Dialogo(tk.Toplevel):
    def __init__(self, padre: tk.Misc, tipo: str, titulo: str, texto: str,
                 botones: list[tuple[str, object, bool]], valor_escape: object = None):
        super().__init__(padre)
        self.resultado = valor_escape
        self.withdraw()
        self.title(titulo)
        self.transient(padre.winfo_toplevel())
        self.resizable(False, False)
        self.configure(bg=tema.FONDO)
        px, f = tema.px, tema.fuentes
        icono, color, fondo = TIPOS[tipo]

        cuerpo = tk.Frame(self, bg=tema.FONDO, padx=px(22), pady=px(18))
        cuerpo.pack(fill="both", expand=True)
        cabeza = tk.Frame(cuerpo, bg=tema.FONDO)
        cabeza.pack(anchor="w", fill="x")
        chip(cabeza, icono, color, fondo, tamano=40, tamano_icono=16).pack(side="left")
        tk.Label(cabeza, text=titulo, font=f.dialogo, fg=tema.TEXTO,
                 bg=tema.FONDO).pack(side="left", padx=(px(10), 0))
        tk.Label(cuerpo, text=texto, font=f.cuerpo, fg="#c3c7cf", bg=tema.FONDO,
                 justify="left", wraplength=px(ANCHO_TEXTO)).pack(anchor="w",
                                                                  pady=(px(10), 0),
                                                                  padx=(px(4), 0))

        acciones = tk.Frame(cuerpo, bg=tema.FONDO)
        acciones.pack(fill="x", pady=(px(14), 0))
        principal = None
        for texto_boton, valor, es_principal in reversed(botones):
            boton = Boton(acciones, texto_boton, variante="primario" if es_principal else "secundario",
                          comando=lambda v=valor: self._cerrar(v))
            boton.pack(side="right")
            if es_principal:
                principal = (boton, valor)

        self.protocol("WM_DELETE_WINDOW", lambda: self._cerrar(valor_escape))
        self.bind("<Escape>", lambda _e: self._cerrar(valor_escape))
        if principal:
            self.bind("<Return>", lambda _e: self._cerrar(principal[1]))
        self._centrar(padre)
        self.deiconify()
        self.grab_set()
        self.focus_set()
        self.wait_window()

    def _centrar(self, padre: tk.Misc) -> None:
        self.update_idletasks()
        raiz = padre.winfo_toplevel()
        x = raiz.winfo_rootx() + (raiz.winfo_width() - self.winfo_reqwidth()) // 2
        y = raiz.winfo_rooty() + (raiz.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _cerrar(self, valor: object) -> None:
        self.resultado = valor
        self.grab_release()
        self.destroy()


def informar(padre: tk.Misc, tipo: str, titulo: str, texto: str, boton: str = "Entendido") -> None:
    Dialogo(padre, tipo, titulo, texto, [(boton, True, True)])


def preguntar(padre: tk.Misc, tipo: str, titulo: str, texto: str,
              si: str = "Sí, continuar", no: str = "No") -> bool:
    return bool(Dialogo(padre, tipo, titulo, texto, [(no, False, False), (si, True, True)],
                        valor_escape=False).resultado)
