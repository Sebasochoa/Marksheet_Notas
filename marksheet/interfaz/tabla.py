"""Tabla desplazable con una FilaNotas por alumno y navegación por teclado."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, Sequence

from ..config import CRITERIOS
from ..modelos import FilaPlantilla
from . import tema
from .fila import ENCABEZADOS, FilaNotas, configurar_columnas, crear_encabezado, crear_linea

PASOS_POR_GIRO = 1


class TablaNotas(tk.Frame):
    def __init__(self, padre: tk.Misc, al_cambiar: Callable[[], None]):
        super().__init__(padre, bg=tema.FONDO)
        self._al_cambiar = al_cambiar
        self._lienzo, self._interior = self._crear_area_desplazable()
        configurar_columnas(self._interior)
        self.filas: list[FilaNotas] = []
        self._entradas: list[tk.Entry] = []

    def mostrar(self, filas_plantilla: Sequence[FilaPlantilla]) -> None:
        self._limpiar()
        crear_encabezado(self._interior)
        separar_paginas = len({f.ubicacion.pagina for f in filas_plantilla}) > 1
        numero_fila, pagina_actual = 2, None
        for fila_plantilla in filas_plantilla:
            if separar_paginas and fila_plantilla.ubicacion.pagina != pagina_actual:
                pagina_actual = fila_plantilla.ubicacion.pagina
                self._crear_separador_de_pagina(numero_fila, pagina_actual)
                numero_fila += 1
            self._agregar_fila(numero_fila, fila_plantilla)
            crear_linea(self._interior, numero_fila + 1)
            numero_fila += 2
        self._lienzo.yview_moveto(0)
        self.enfocar(0)

    def textos_por_fila(self) -> list[list[str]]:
        return [fila.textos() for fila in self.filas]

    def cantidad_completas(self) -> int:
        return sum(fila.esta_completa() for fila in self.filas)

    def resaltar_vacios(self, indices: Iterable[int]) -> None:
        for indice in indices:
            self.filas[indice].resaltar_campos_vacios()

    def enfocar(self, posicion: int) -> str:
        """Enfoca el campo en 'posicion' (orden de lectura); 'break' anula el manejo por defecto."""
        if 0 <= posicion < len(self._entradas):
            entrada = self._entradas[posicion]
            entrada.focus_set()
            entrada.select_range(0, "end")
        return "break"

    def _crear_area_desplazable(self) -> tuple[tk.Canvas, tk.Frame]:
        lienzo = tk.Canvas(self, highlightthickness=0, bd=0, bg=tema.FONDO)
        barra = ttk.Scrollbar(self, orient="vertical", command=lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y", padx=(tema.px(8), 0))
        lienzo.pack(side="left", fill="both", expand=True)
        interior = tk.Frame(lienzo, bg=tema.FONDO)
        ventana = lienzo.create_window((0, 0), window=interior, anchor="nw")
        interior.bind("<Configure>",
                      lambda _evento: lienzo.configure(scrollregion=lienzo.bbox("all")))
        lienzo.bind("<Configure>", lambda e: lienzo.itemconfigure(ventana, width=e.width))
        lienzo.bind_all("<MouseWheel>", self._desplazar_con_rueda, add="+")
        return lienzo, interior

    def _limpiar(self) -> None:
        for widget in self._interior.winfo_children():
            widget.destroy()
        self.filas, self._entradas = [], []

    def _crear_separador_de_pagina(self, numero_fila: int, pagina: int) -> None:
        caja = tk.Frame(self._interior, bg=tema.FONDO)
        caja.grid(row=numero_fila, column=0, columnspan=len(ENCABEZADOS), sticky="w",
                  padx=tema.px(4), pady=(tema.px(16), tema.px(4)))
        tk.Label(caja, text=tema.glifo("paginas"), font=tema.fuente_icono(11),
                 fg=tema.AMARILLO, bg=tema.FONDO).pack(side="left")
        tk.Label(caja, text=f"PÁGINA {pagina + 1}", font=tema.fuentes.mini_fuerte,
                 fg=tema.AMARILLO, bg=tema.FONDO).pack(side="left", padx=(tema.px(6), 0))

    def _agregar_fila(self, numero_fila: int, fila_plantilla: FilaPlantilla) -> None:
        fila = FilaNotas(self._interior, numero_fila, fila_plantilla, self._al_cambiar)
        for entrada in fila.entradas:
            self._conectar_navegacion(entrada, posicion=len(self._entradas))
            self._entradas.append(entrada)
        self.filas.append(fila)

    def _conectar_navegacion(self, entrada: tk.Entry, posicion: int) -> None:
        """Enter avanza al siguiente campo; las flechas cambian de fila en la misma columna."""
        salto_de_fila = len(CRITERIOS)
        entrada.bind("<Return>", lambda _evento: self.enfocar(posicion + 1))
        entrada.bind("<Down>", lambda _evento: self.enfocar(posicion + salto_de_fila))
        entrada.bind("<Up>", lambda _evento: self.enfocar(posicion - salto_de_fila))
        entrada.bind("<FocusIn>", lambda _evento: self._hacer_visible(entrada.master), add="+")

    def _hacer_visible(self, widget: tk.Widget) -> None:
        """Desplaza la tabla para que el campo con foco quede a la vista."""
        self.update_idletasks()
        alto_tabla = max(self._interior.winfo_height(), 1)
        alto_vista = self._lienzo.winfo_height()
        arriba = widget.winfo_y()
        abajo = arriba + widget.winfo_height()
        inicio_vista = self._lienzo.canvasy(0)
        if arriba < inicio_vista:
            self._lienzo.yview_moveto(arriba / alto_tabla)
        elif abajo > inicio_vista + alto_vista:
            self._lienzo.yview_moveto((abajo - alto_vista) / alto_tabla)

    def _desplazar_con_rueda(self, evento: tk.Event) -> None:
        if not self.winfo_ismapped():
            return
        direccion = -1 if evento.delta > 0 else 1
        self._lienzo.yview_scroll(direccion * PASOS_POR_GIRO, "units")
