"""Ventana principal: abrir la plantilla, ingresar las notas y generar el PDF."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Iterable

from ..config import FINAL_APROBATORIO, NOTA_MAXIMA, NOTA_MINIMA
from ..deteccion import detectar_plantilla
from ..errores import ErrorMarkSheet
from ..escritura import escribir_anotaciones
from ..modelos import Anotacion, Plantilla
from ..notas import Revision, revisar
from . import neu, tema
from .dialogo import informar, preguntar
from .esqueleto import TablaEsqueleto
from .icono import aplicar_icono
from .tabla import TablaNotas
from .zona import ZonaArchivo

TITULO = "Mark Sheet - Speaking Test"
GEOMETRIA_INICIAL = "1200x780"
TAMANO_MINIMO = (940, 580)
ANCHO_MAXIMO = 1160                # px de diseño: el contenido se centra hasta este ancho
MARGEN = 28
RETARDO_CARGA_INICIAL_MS = 50
CARGA_MINIMA_S = 0.6               # el esqueleto no parpadea con PDF pequeños
SONDEO_MS = 40
SUFIJO_SALIDA = "_notas"
TIPOS_PDF = [("PDF", "*.pdf")]
LARGO_NOMBRE_BARRA = 40
PASOS = ("Leyendo el PDF", "Detectando la grilla", "Leyendo alumnos")
INTRODUCCION = ("Escribe los cuatro criterios sobre el PDF que genera BI Publisher. TOTAL y FR se "
                "calculan solos, y el resultado se guarda como copia: el original no cambia.")
TARJETAS = (
    ("alumnos", "alumnos", tema.AMARILLO, tema.AMARILLO_FONDO, "Alumnos"),
    ("completas", "completas", tema.CIAN, tema.CIAN_FONDO, "Completas"),
    ("revisar", "revisar", tema.MAGENTA, tema.MAGENTA_FONDO, "Por revisar"),
)
TARJETA_ESTILO = dict(radio=16, relleno=10, distancia=5, desenfoque=8)
TABLA_ESTILO = dict(radio=22, relleno=18, distancia=7, desenfoque=11)


def centrar(contenedor: tk.Misc, hijo: tk.Widget) -> None:
    """Mantiene 'hijo' (ya empaquetado) centrado con un ancho máximo dentro de 'contenedor'."""
    def ajustar(evento: tk.Event) -> None:
        relleno = max(tema.px(MARGEN), (evento.width - tema.px(ANCHO_MAXIMO)) // 2)
        hijo.pack_configure(padx=relleno)
    contenedor.bind("<Configure>", ajustar, add="+")


class VentanaPrincipal(tk.Tk):
    def __init__(self, ruta_inicial: str | None = None):
        super().__init__()
        aplicar_icono(self)          # antes de que la ventana se dibuje: sin destello de la pluma
        self.title(TITULO)
        self.geometry(GEOMETRIA_INICIAL)
        self.minsize(*TAMANO_MINIMO)
        tema.configurar(self)
        self._ruta_pdf = ""
        self._pdf_bytes = b""
        self._plantilla: Plantilla | None = None
        self._cola: queue.Queue = queue.Queue()
        self._cargando = False
        self._generado = ""
        self._crear_barra()
        self._crear_pie()
        self._cuerpo = tk.Frame(self, bg=tema.FONDO)
        self._cuerpo.pack(fill="both", expand=True)
        self._columna = tk.Frame(self._cuerpo, bg=tema.FONDO)
        self._columna.pack(fill="both", expand=True)
        centrar(self._cuerpo, self._columna)
        self._vista_inicio = self._crear_inicio(self._columna)
        self._vista_trabajo = self._crear_trabajo(self._columna)
        self._aviso = self._crear_aviso()
        self._mostrar_vista(self._vista_inicio)
        self._actualizar_estado()
        if ruta_inicial:
            self.after(RETARDO_CARGA_INICIAL_MS, lambda: self.cargar(ruta_inicial))

    def report_callback_exception(self, tipo, valor, traza) -> None:
        """Muestra cualquier error no previsto en vez de perderlo: el .exe no tiene consola."""
        messagebox.showerror("Error inesperado", f"{tipo.__name__}: {valor}")

    # — flujo —

    def abrir(self) -> None:
        if self._cargando:
            return
        ruta = filedialog.askopenfilename(title="Abrir Mark Sheet", filetypes=TIPOS_PDF) or ""
        if ruta:
            self.cargar(ruta)

    def cargar(self, ruta: str) -> None:
        """Lee y detecta la plantilla en un hilo; mientras tanto se ve el esqueleto."""
        if self._cargando:
            return
        self._cargando = True
        self._ocultar_aviso()
        self._mostrar_cargando(os.path.basename(ruta))
        threading.Thread(target=self._leer_en_segundo_plano, args=(ruta,), daemon=True).start()
        self.after(SONDEO_MS, self._sondear)

    def generar(self) -> None:
        revision = revisar(self._tabla.textos_por_fila())
        if not self._confirmar_revision(revision):
            return
        ruta = self._pedir_ruta_salida()
        if ruta:
            self._escribir(self._anotaciones(revision), ruta)

    # — carga en segundo plano —

    def _leer_en_segundo_plano(self, ruta: str) -> None:
        inicio = time.monotonic()
        try:
            with open(ruta, "rb") as archivo:
                pdf_bytes = archivo.read()  # en memoria: guardar no depende del archivo abierto
            self._cola.put(("paso", 1))
            plantilla = detectar_plantilla(pdf_bytes)
        except ErrorMarkSheet as error:
            self._cola.put(("error", "Plantilla no reconocida", str(error)))
            return
        except OSError as error:
            self._cola.put(("error", "No se pudo abrir", error.strerror or str(error)))
            return
        except Exception as error:  # noqa: BLE001 — el .exe no tiene consola
            self._cola.put(("error", "Error inesperado", f"{type(error).__name__}: {error}"))
            return
        espera = CARGA_MINIMA_S - (time.monotonic() - inicio)
        if espera > 0:
            time.sleep(espera)
        self._cola.put(("listo", ruta, pdf_bytes, plantilla))

    def _sondear(self) -> None:
        try:
            while True:
                mensaje = self._cola.get_nowait()
                if mensaje[0] == "paso":
                    self._marcar_paso(mensaje[1])
                elif mensaje[0] == "error":
                    self._fallo_carga(*mensaje[1:])
                    return
                elif mensaje[0] == "listo":
                    self._marcar_paso(2)
                    self.after(SONDEO_MS, lambda m=mensaje: self._terminar_carga(*m[1:]))
                    return
        except queue.Empty:
            pass
        self.after(SONDEO_MS, self._sondear)

    def _terminar_carga(self, ruta: str, pdf_bytes: bytes, plantilla: Plantilla) -> None:
        self._ruta_pdf, self._pdf_bytes, self._plantilla = ruta, pdf_bytes, plantilla
        self._cargando = False
        self._generado = ""
        self._tabla.mostrar(plantilla.filas, plantilla.rotulos_criterios)
        self._mostrar_listo()
        self._advertir_si_ya_tiene_valores(plantilla)

    def _fallo_carga(self, titulo: str, texto: str) -> None:
        self._cargando = False
        if self._plantilla:     # se conserva lo que ya estaba abierto, con sus notas
            self._mostrar_listo()
        else:
            self._detener_esqueleto()
            self._archivo.configure(text="Sin archivo")
            self._boton_abrir.configurar(estado="normal")
            self._mostrar_vista(self._vista_inicio)
            self._actualizar_estado()
        informar(self, "error", titulo, texto)

    # — construcción —

    def _crear_barra(self) -> None:
        px, f = tema.px, tema.fuentes
        exterior = tk.Frame(self, bg=tema.FONDO)
        exterior.pack(fill="x")
        barra = tk.Frame(exterior, bg=tema.FONDO)
        barra.pack(fill="x", pady=(px(10), 0))
        centrar(exterior, barra)
        neu.chip(barra, "documento", "#10161c", tamano=42, radio=13, tamano_icono=17,
                 degradado=(tema.CIAN, tema.MAGENTA)).pack(side="left")
        marca = tk.Frame(barra, bg=tema.FONDO)
        marca.pack(side="left", padx=(px(4), 0))
        tk.Label(marca, text="Mark Sheet", font=f.marca, fg=tema.TEXTO,
                 bg=tema.FONDO).pack(anchor="w")
        tk.Label(marca, text="Speaking Test", font=f.marca_italica, fg=tema.TEXTO_SUAVE,
                 bg=tema.FONDO).pack(anchor="w")

        self._boton_generar = neu.Boton(barra, "Generar PDF…", "guardar", self.generar,variante="primario", estado="disabled")
        self._boton_generar.pack(side="right")
        self._boton_abrir = neu.Boton(barra, "Abrir PDF…", "abrir", self.abrir)
        self._boton_abrir.pack(side="right")
        pastilla = neu.Panel(barra, modo="hundido", radio=12, relleno=9, ajustar="ambos")
        pastilla.pack(side="right", padx=(0, px(12)))
        tk.Label(pastilla.interior, text=tema.glifo("pdf"), font=tema.fuente_icono(13),
                 fg=tema.MAGENTA, bg=tema.FONDO).pack(side="left", padx=(px(4), 0))
        self._archivo = tk.Label(pastilla.interior, text="Sin archivo", font=f.pequena,
                                 fg=tema.TEXTO_SUAVE, bg=tema.FONDO)
        self._archivo.pack(side="left", padx=(px(8), px(4)))

    def _crear_pie(self) -> None:
        px, f = tema.px, tema.fuentes
        exterior = tk.Frame(self, bg=tema.FONDO)
        exterior.pack(side="bottom", fill="x")
        pie = tk.Frame(exterior, bg=tema.FONDO)
        pie.pack(fill="x", pady=(px(4), px(14)))
        centrar(exterior, pie)
        self._estado_icono = tk.Label(pie, font=tema.fuente_icono(12), fg=tema.CIAN,
                                      bg=tema.FONDO)
        self._estado_icono.pack(side="left")
        self._estado = tk.Label(pie, font=f.pequena, fg=tema.TEXTO_SUAVE, bg=tema.FONDO)
        self._estado.pack(side="left", padx=(px(8), 0))
        self._progreso = neu.Barra(pie)
        self._etiqueta_completas = tk.Label(pie, text="Completas", font=f.pequena,
                                            fg=tema.TEXTO_SUAVE, bg=tema.FONDO)

    def _crear_inicio(self, padre: tk.Misc) -> tk.Frame:
        px, f = tema.px, tema.fuentes
        vista = tk.Frame(padre, bg=tema.FONDO)
        centro = tk.Frame(vista, bg=tema.FONDO)
        centro.place(relx=0.5, rely=0.46, anchor="center")
        tk.Label(centro, text="Abre la Mark Sheet", font=f.h1, fg=tema.TEXTO,
                 bg=tema.FONDO).pack()
        tk.Label(centro, text="para ingresar las notas.", font=f.h1_italica,
                 fg=tema.CIAN_CLARO, bg=tema.FONDO).pack()
        tk.Label(centro, text=INTRODUCCION, font=f.cuerpo_grande, fg=tema.TEXTO_SUAVE,
                 bg=tema.FONDO, justify="center", wraplength=px(560)).pack(
            pady=(px(14), px(26)))
        ZonaArchivo(centro, al_elegir=self.abrir, al_soltar=self.cargar).pack()
        return vista

    def _crear_trabajo(self, padre: tk.Misc) -> tk.Frame:
        px, f = tema.px, tema.fuentes
        vista = tk.Frame(padre, bg=tema.FONDO)
        margen_tabla = neu.margen_elevado(TABLA_ESTILO["distancia"], TABLA_ESTILO["desenfoque"])
        margen_tarjeta = neu.margen_elevado(TARJETA_ESTILO["distancia"],
                                            TARJETA_ESTILO["desenfoque"])
        cabeza = tk.Frame(vista, bg=tema.FONDO)
        cabeza.pack(fill="x", padx=(margen_tabla, margen_tabla - margen_tarjeta),
                    pady=(px(10), 0))

        izquierda = tk.Frame(cabeza, bg=tema.FONDO)
        izquierda.pack(side="left", fill="x", expand=True)
        self._kicker = tk.Label(izquierda, font=f.mini_fuerte, fg=tema.CIAN, bg=tema.FONDO)
        self._kicker.pack(anchor="w")
        self._titulo = tk.Label(izquierda, font=f.h2, fg=tema.TEXTO, bg=tema.FONDO,
                                justify="left", wraplength=px(560))
        self._titulo.pack(anchor="w", pady=(px(2), px(4)))
        self._detalle = tk.Frame(izquierda, bg=tema.FONDO)
        self._detalle.pack(anchor="w")
        self._resumen = tk.Label(self._detalle, font=f.pequena, fg=tema.TEXTO_SUAVE,
                                 bg=tema.FONDO)
        self._atajos = tk.Frame(self._detalle, bg=tema.FONDO)
        tk.Label(self._atajos, text=tema.glifo("teclado"), font=tema.fuente_icono(12),
                 fg=tema.AMARILLO, bg=tema.FONDO).pack(side="left")
        tk.Label(self._atajos, text="Enter avanza  ·  ↑ ↓ cambian de fila", font=f.pequena,
                 fg=tema.TEXTO_SUAVE, bg=tema.FONDO).pack(side="left", padx=(px(6), 0))
        self._caja_pasos = tk.Frame(self._detalle, bg=tema.FONDO)
        self._pasos = []
        for texto in PASOS:
            icono = tk.Label(self._caja_pasos, font=tema.fuente_icono(11), bg=tema.FONDO)
            icono.pack(side="left")
            etiqueta = tk.Label(self._caja_pasos, font=f.pequena, bg=tema.FONDO)
            etiqueta.pack(side="left", padx=(px(6), px(18)))
            self._pasos.append((icono, etiqueta, texto))

        derecha = tk.Frame(cabeza, bg=tema.FONDO)
        derecha.pack(side="right")
        self._cifras: dict[str, tk.Label] = {}
        for clave, icono, color, fondo, etiqueta in TARJETAS:
            tarjeta = neu.Panel(derecha, ajustar="ambos", **TARJETA_ESTILO)
            tarjeta.pack(side="left")
            neu.chip(tarjeta.interior, icono, color, fondo, tamano=38,
                     tamano_icono=15).pack(side="left")
            textos = tk.Frame(tarjeta.interior, bg=tema.FONDO)
            textos.pack(side="left", padx=(px(4), px(10)))
            cifra = tk.Label(textos, text="—", font=f.cifra, fg=tema.TEXTO_TENUE,
                             bg=tema.FONDO, width=3, anchor="w")
            cifra.pack(anchor="w")
            tk.Label(textos, text=etiqueta, font=f.mini, fg=tema.TEXTO_SUAVE,
                     bg=tema.FONDO).pack(anchor="w")
            self._cifras[clave] = cifra

        tarjeta_tabla = neu.Panel(vista, **TABLA_ESTILO)
        tarjeta_tabla.pack(fill="both", expand=True)
        self._tabla = TablaNotas(tarjeta_tabla.interior, al_cambiar=self._al_cambiar_notas)
        self._esqueleto = TablaEsqueleto(tarjeta_tabla.interior)
        return vista

    def _crear_aviso(self) -> neu.Panel:
        """Aviso flotante abajo a la derecha con el botón para abrir el PDF generado."""
        px, f = tema.px, tema.fuentes
        aviso = neu.Panel(self, ajustar="ambos", radio=18, relleno=10, distancia=6,
                          desenfoque=10)
        interior = aviso.interior
        neu.chip(interior, "ok", tema.CIAN, tema.CIAN_FONDO, tamano=40,
                 tamano_icono=16).pack(side="left")
        textos = tk.Frame(interior, bg=tema.FONDO)
        textos.pack(side="left", padx=(px(4), px(14)))
        tk.Label(textos, text="PDF generado", font=f.zona, fg=tema.TEXTO,
                 bg=tema.FONDO).pack(anchor="w")
        self._aviso_nombre = tk.Label(textos, font=f.pequena, fg=tema.TEXTO_SUAVE,
                                      bg=tema.FONDO)
        self._aviso_nombre.pack(anchor="w")
        neu.Boton(interior, "Abrir", "externo", self._abrir_generado,
                  variante="primario").pack(side="left")
        neu.Boton(interior, "", "cerrar", self._ocultar_aviso).pack(side="left")
        return aviso

    # — estados de la vista —

    def _mostrar_vista(self, vista: tk.Frame) -> None:
        for otra in (self._vista_inicio, self._vista_trabajo):
            if otra is not vista:
                otra.pack_forget()
        vista.pack(fill="both", expand=True)

    def _mostrar_cargando(self, nombre: str) -> None:
        self._mostrar_vista(self._vista_trabajo)
        self._kicker.configure(text="CARGANDO PLANTILLA")
        self._titulo.configure(text=nombre)
        self._archivo.configure(text=_acortar(nombre))
        self._resumen.pack_forget()
        self._atajos.pack_forget()
        self._caja_pasos.pack(anchor="w", pady=(px_(2), 0))
        self._marcar_paso(0)
        for cifra in self._cifras.values():
            cifra.configure(text="—", fg=tema.TEXTO_TENUE)
        self._tabla.pack_forget()
        self._esqueleto.pack(fill="both", expand=True, anchor="nw")
        self._esqueleto.iniciar()
        self._boton_abrir.configurar(estado="disabled")
        self._boton_generar.configurar(estado="disabled")
        self._poner_estado("carga", "Leyendo la plantilla…")
        self._mostrar_progreso(False)

    def _mostrar_listo(self) -> None:
        plantilla = self._plantilla
        nombre = os.path.basename(self._ruta_pdf)
        paginas = len({f.ubicacion.pagina for f in plantilla.filas})
        self._detener_esqueleto()
        self._kicker.configure(text="INGRESO DE NOTAS")
        self._titulo.configure(text=nombre)
        self._archivo.configure(text=_acortar(nombre))
        self._resumen.configure(
            text=f"{paginas} página(s)  ·  cada criterio de {NOTA_MINIMA} a {NOTA_MAXIMA}  ·  "
                 f"FR aprobatorio desde {FINAL_APROBATORIO}")
        self._caja_pasos.pack_forget()
        self._resumen.pack(anchor="w")
        self._atajos.pack(anchor="w", pady=(px_(4), 0))
        self._tabla.pack(fill="both", expand=True)
        self._boton_abrir.configurar(estado="normal")
        self._boton_generar.configurar(estado="normal")
        self._mostrar_vista(self._vista_trabajo)
        self._actualizar_estado()

    def _detener_esqueleto(self) -> None:
        self._esqueleto.detener()
        self._esqueleto.pack_forget()

    def _marcar_paso(self, actual: int) -> None:
        for indice, (icono, etiqueta, texto) in enumerate(self._pasos):
            if indice < actual:
                icono.configure(text=tema.glifo("hecho"), fg=tema.CIAN)
                etiqueta.configure(text=texto, fg=tema.TEXTO_SUAVE)
            elif indice == actual:
                icono.configure(text=tema.glifo("actual"), fg=tema.AMARILLO)
                etiqueta.configure(text=f"{texto}…", fg=tema.AMARILLO_CLARO)
            else:
                icono.configure(text=tema.glifo("pendiente"), fg=tema.TEXTO_TENUE)
                etiqueta.configure(text=texto, fg=tema.TEXTO_TENUE)

    def _mostrar_progreso(self, visible: bool) -> None:
        if visible:
            self._progreso.pack(side="right")
            self._etiqueta_completas.pack(side="right", padx=(0, tema.px(10)))
        else:
            self._progreso.pack_forget()
            self._etiqueta_completas.pack_forget()

    def _poner_estado(self, icono: str, texto: str) -> None:
        self._estado_icono.configure(text=tema.glifo(icono))
        self._estado.configure(text=texto)

    def _mostrar_aviso(self, ruta: str) -> None:
        self._aviso_nombre.configure(text=_acortar(os.path.basename(ruta)))
        self._aviso.place(in_=self._cuerpo, relx=1.0, rely=1.0, x=-tema.px(MARGEN // 2),
                          y=-tema.px(2), anchor="se")
        tk.Misc.tkraise(self._aviso)     # Canvas.lift() es tag_raise (ítems), no la ventana

    def _ocultar_aviso(self) -> None:
        self._aviso.place_forget()

    def _abrir_generado(self) -> None:
        if self._generado:
            _abrir_archivo(self._generado)

    def _al_cambiar_notas(self) -> None:
        if self._generado:
            self._generado = ""
            self._ocultar_aviso()
        self._actualizar_estado()

    def _actualizar_estado(self) -> None:
        if not self._plantilla:
            self._poner_estado("info", "Abre el PDF de la Mark Sheet.")
            self._mostrar_progreso(False)
            return
        total = len(self._tabla.filas)
        completas = self._tabla.cantidad_completas()
        por_revisar = len(revisar(self._tabla.textos_por_fila()).invalidas)
        if self._generado:
            self._poner_estado("ok", f"Generado: {self._generado}")
        else:
            self._poner_estado("alumnos", f"{total} alumnos detectados  |  "
                                          f"{completas} con notas completas")
        self._cifras["alumnos"].configure(text=str(total), fg=tema.TEXTO)
        self._cifras["completas"].configure(text=str(completas), fg=tema.TEXTO)
        self._cifras["revisar"].configure(text=str(por_revisar),
                                          fg=tema.MAGENTA_CLARO if por_revisar else tema.TEXTO)
        self._mostrar_progreso(True)
        self._progreso.mostrar(completas / max(total, 1))

    # — revisión y escritura —

    def _advertir_si_ya_tiene_valores(self, plantilla: Plantilla) -> None:
        if plantilla.ya_tiene_valores:
            informar(self, "aviso", "PDF ya llenado",
                     "La grilla ya tiene valores: las notas nuevas se superpondrían. "
                     "Usa el PDF original.")

    def _confirmar_revision(self, revision: Revision) -> bool:
        if revision.invalidas:
            self._tabla.resaltar_vacios(revision.invalidas)
            informar(self, "error", "Notas incompletas o inválidas",
                     f"Revisa N° {self._describir(revision.invalidas)}.\n"
                     f"Cada criterio debe estar entre {NOTA_MINIMA} y {NOTA_MAXIMA}.",
                     boton="Revisar")
            return False
        if not revision.calificaciones:
            informar(self, "aviso", "Sin notas", "No hay ninguna fila con notas.")
            return False
        if revision.vacias:
            return preguntar(self, "pregunta", "Filas vacías",
                             f"{len(revision.vacias)} alumno(s) sin notas quedarán en blanco. "
                             "¿Continuar?")
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
            informar(self, "error", "Nombre inválido",
                     "Guarda con otro nombre para conservar el original.")
            return ""
        return ruta

    def _anotaciones(self, revision: Revision) -> list[Anotacion]:
        filas = self._plantilla.filas
        return [Anotacion(filas[indice].ubicacion, calificacion.textos_por_columna())
                for indice, calificacion in revision.calificaciones.items()]

    def _escribir(self, anotaciones: list[Anotacion], ruta: str) -> None:
        self._ocultar_aviso()
        self._boton_generar.configurar(texto="Generando…", estado="disabled")
        self._poner_estado("carga", "Generando PDF…")
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            escribir_anotaciones(self._pdf_bytes, anotaciones, ruta)
        except PermissionError:
            informar(self, "error", "No se pudo guardar",
                     "El archivo está abierto en otro programa. Ciérralo e inténtalo de nuevo.")
            return
        except ErrorMarkSheet as error:
            informar(self, "error", "No se pudo generar", str(error))
            return
        finally:
            self.configure(cursor="")
            self._boton_generar.configurar(texto="Generar PDF…", estado="normal")
            self._actualizar_estado()
        self._generado = ruta
        self._actualizar_estado()
        self._mostrar_aviso(ruta)


def px_(valor: float) -> int:
    return tema.px(valor)


def _acortar(texto: str, largo: int = LARGO_NOMBRE_BARRA) -> str:
    return texto if len(texto) <= largo else texto[:largo - 1] + "…"


def _es_la_misma_ruta(una: str, otra: str) -> bool:
    return os.path.normcase(os.path.abspath(una)) == os.path.normcase(os.path.abspath(otra))


def _abrir_archivo(ruta: str) -> None:
    if hasattr(os, "startfile"):
        os.startfile(ruta)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])
