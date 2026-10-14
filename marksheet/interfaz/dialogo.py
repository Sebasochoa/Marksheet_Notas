"""Diálogos modales con el estilo de la interfaz (reemplazan a messagebox)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import tema

ETIQUETAS = {"error": "Error", "aviso": "Aviso", "pregunta": "Confirmar", "ok": "Listo"}
COLORES = {"error": tema.MAGENTA_700, "aviso": tema.MAGENTA_700,
           "pregunta": tema.ACENTO_700, "ok": tema.ACENTO_700}
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
        self.configure(bg=tema.SUPERFICIE)
        px, f = tema.px, tema.fuentes

        cuerpo = tk.Frame(self, bg=tema.SUPERFICIE, padx=px(26), pady=px(22))
        cuerpo.pack(fill="both", expand=True)
        tk.Label(cuerpo, text=ETIQUETAS[tipo].upper(), font=f.mini_fuerte, fg=COLORES[tipo],
                 bg=tema.SUPERFICIE).pack(anchor="w")
        tk.Label(cuerpo, text=titulo, font=f.dialogo, fg=tema.TEXTO,
                 bg=tema.SUPERFICIE).pack(anchor="w", pady=(px(2), px(10)))
        tk.Label(cuerpo, text=texto, font=f.cuerpo, fg=tema.NEUTRO_800, bg=tema.SUPERFICIE,
                 justify="left", wraplength=px(ANCHO_TEXTO)).pack(anchor="w")

        acciones = tk.Frame(cuerpo, bg=tema.SUPERFICIE)
        acciones.pack(fill="x", pady=(px(22), 0))
        principal = None
        for texto_boton, valor, es_principal in reversed(botones):
            boton = ttk.Button(acciones, text=texto_boton,
                               style="Primario.TButton" if es_principal else "Secundario.TButton",
                               command=lambda v=valor: self._cerrar(v))
            boton.pack(side="right", padx=(px(10), 0))
            if es_principal:
                principal = (boton, valor)

        self.protocol("WM_DELETE_WINDOW", lambda: self._cerrar(valor_escape))
        self.bind("<Escape>", lambda _e: self._cerrar(valor_escape))
        if principal:
            self.bind("<Return>", lambda _e: self._cerrar(principal[1]))
        self._centrar(padre)
        self.deiconify()
        self.grab_set()
        (principal[0] if principal else self).focus_set()
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
