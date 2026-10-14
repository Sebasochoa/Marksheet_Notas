"""Ventana principal: abrir la plantilla, ingresar las notas y generar el PDF."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Iterable

from ..config import NOTA_MAXIMA, NOTA_MINIMA
from ..deteccion import detectar_plantilla
from ..errores import ErrorMarkSheet
from ..escritura import escribir_anotaciones
from ..modelos import Anotacion, Plantilla
from ..notas import Revision, revisar
from .tabla import TablaNotas

TITULO = "Mark Sheet - Speaking Test"
GEOMETRIA_INICIAL = "980x680"
TAMANO_MINIMO = (760, 400)
RETARDO_CARGA_INICIAL_MS = 50      # deja que la ventana se dibuje antes de leer el PDF
SUFIJO_SALIDA = "_notas"
TIPOS_PDF = [("PDF", "*.pdf")]
MARGEN = 6


class VentanaPrincipal(tk.Tk):
    def __init__(self, ruta_inicial: str | None = None):
        super().__init__()
        self.title(TITULO)
        self.geometry(GEOMETRIA_INICIAL)
        self.minsize(*TAMANO_MINIMO)
        self._ruta_pdf = ""
        self._pdf_bytes = b""
        self._plantilla: Plantilla | None = None
        self._crear_barra()
        self._tabla = TablaNotas(self, al_cambiar=self._actualizar_estado)
        self._tabla.pack(fill="both", expand=True, padx=MARGEN)
        self._estado = ttk.Label(self, padding=MARGEN, text="Abre el PDF de la Mark Sheet.")
        self._estado.pack(fill="x")
        if ruta_inicial:
            self.after(RETARDO_CARGA_INICIAL_MS, lambda: self.cargar(ruta_inicial))

    def report_callback_exception(self, tipo, valor, traza) -> None:
        """Muestra cualquier error no previsto en vez de perderlo: el .exe no tiene consola."""
        messagebox.showerror("Error inesperado", f"{tipo.__name__}: {valor}")

    def abrir(self) -> None:
        ruta = filedialog.askopenfilename(title="Abrir Mark Sheet", filetypes=TIPOS_PDF) or ""
        if ruta:
            self.cargar(ruta)

    def cargar(self, ruta: str) -> None:
        with open(ruta, "rb") as archivo:
            pdf_bytes = archivo.read()      # en memoria: guardar no depende del archivo abierto
        try:
            plantilla = detectar_plantilla(pdf_bytes)
        except ErrorMarkSheet as error:
            messagebox.showerror("Plantilla no reconocida", str(error))
            return
        self._ruta_pdf, self._pdf_bytes, self._plantilla = ruta, pdf_bytes, plantilla
        self._advertir_si_ya_tiene_valores(plantilla)
        self._archivo.configure(text=os.path.basename(ruta))
        self._tabla.mostrar(plantilla.filas)
        self._boton_generar.configure(state="normal")
        self._actualizar_estado()

    def generar(self) -> None:
        revision = revisar(self._tabla.textos_por_fila())
        if not self._confirmar_revision(revision):
            return
        ruta = self._pedir_ruta_salida()
        if ruta:
            self._escribir(self._anotaciones(revision), ruta)

    def _crear_barra(self) -> None:
        barra = ttk.Frame(self, padding=MARGEN)
        barra.pack(fill="x")
        ttk.Button(barra, text="Abrir PDF...", command=self.abrir).pack(side="left")
        self._boton_generar = ttk.Button(barra, text="Generar PDF...", command=self.generar,
                                         state="disabled")
        self._boton_generar.pack(side="left", padx=MARGEN)
        self._archivo = ttk.Label(barra, text="Sin archivo")
        self._archivo.pack(side="left", padx=MARGEN)

    def _advertir_si_ya_tiene_valores(self, plantilla: Plantilla) -> None:
        if plantilla.ya_tiene_valores:
            messagebox.showwarning("PDF ya llenado",
                                   "La grilla ya tiene valores: las notas nuevas se superpondrían. "
                                   "Usa el PDF original.")

    def _actualizar_estado(self) -> None:
        self._estado.configure(text=f"{len(self._tabla.filas)} alumnos detectados  |  "
                                    f"{self._tabla.cantidad_completas()} con notas completas")

    def _confirmar_revision(self, revision: Revision) -> bool:
        if revision.invalidas:
            self._tabla.resaltar_vacios(revision.invalidas)
            messagebox.showerror("Notas incompletas o inválidas",
                                 f"Revisa N° {self._describir(revision.invalidas)}.\n"
                                 f"Cada criterio debe estar entre {NOTA_MINIMA} y {NOTA_MAXIMA}.")
            return False
        if not revision.calificaciones:
            messagebox.showwarning("Sin notas", "No hay ninguna fila con notas.")
            return False
        if revision.vacias:
            return messagebox.askyesno("Filas vacías", f"{len(revision.vacias)} alumno(s) sin "
                                                       "notas quedarán en blanco. ¿Continuar?")
        return True

    def _describir(self, indices: Iterable[int]) -> str:
        alumnos = (self._plantilla.filas[indice].alumno for indice in indices)
        return ", ".join(f"{alumno.numero} ({alumno.codigo})" for alumno in alumnos)

    def _pedir_ruta_salida(self) -> str:
        carpeta, nombre = os.path.split(self._ruta_pdf)
        ruta = filedialog.asksaveasfilename(
            title="Guardar PDF con notas", defaultextension=".pdf", filetypes=TIPOS_PDF,
            initialdir=carpeta, initialfile=os.path.splitext(nombre)[0] + SUFIJO_SALIDA + ".pdf",
        ) or ""
        if ruta and _es_la_misma_ruta(ruta, self._ruta_pdf):
            messagebox.showerror("Nombre inválido", "Guarda con otro nombre para conservar el original.")
            return ""
        return ruta

    def _anotaciones(self, revision: Revision) -> list[Anotacion]:
        filas = self._plantilla.filas
        return [Anotacion(filas[indice].ubicacion, calificacion.textos_por_columna())
                for indice, calificacion in revision.calificaciones.items()]

    def _escribir(self, anotaciones: list[Anotacion], ruta: str) -> None:
        try:
            escribir_anotaciones(self._pdf_bytes, anotaciones, ruta)
        except PermissionError:
            messagebox.showerror("No se pudo guardar", "El archivo está abierto en otro programa. "
                                                       "Ciérralo e inténtalo de nuevo.")
            return
        except ErrorMarkSheet as error:
            messagebox.showerror("No se pudo generar", str(error))
            return
        self._estado.configure(text=f"Generado: {ruta}")
        _ofrecer_abrir(ruta)


def _es_la_misma_ruta(una: str, otra: str) -> bool:
    return os.path.normcase(os.path.abspath(una)) == os.path.normcase(os.path.abspath(otra))


def _ofrecer_abrir(ruta: str) -> None:
    if hasattr(os, "startfile") and messagebox.askyesno("Listo", f"PDF generado:\n{ruta}\n\n¿Abrirlo?"):
        os.startfile(ruta)
