"""Superficies neumórficas dibujadas con Pillow: paneles, botones, campos, chips y barras."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

from . import tema

_CACHE: dict = {}
LIMITE_CACHE = 400
AREA_SUPERMUESTREO = 250_000     # debajo de esto se dibuja a 2x para suavizar bordes


def _rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _capa(tam, color: str) -> Image.Image:
    return Image.new("RGB", tam, _rgb(color))


def _degradado(tam, inicio: str, fin: str) -> Image.Image:
    mascara = Image.linear_gradient("L").rotate(90).resize(tam)
    return Image.composite(_capa(tam, fin), _capa(tam, inicio), mascara)


def margen_elevado(distancia: float, desenfoque: float) -> int:
    return tema.px(distancia) + 2 * tema.px(desenfoque)


def superficie(ancho: int, alto: int, radio: int, modo: str = "elevado", margen: int = 0,
               distancia: int = 4, desenfoque: int = 6, relleno: str | None = None,
               degradado: tuple[str, str] | None = None, resplandor: str | None = None,
               anillo: str | None = None) -> ImageTk.PhotoImage:
    """modo: 'elevado' (sombra hacia fuera), 'hundido' (sombra interior) o 'plano'."""
    relleno = relleno or tema.FONDO
    ancho, alto = max(int(ancho), 2), max(int(alto), 2)
    clave = (ancho, alto, radio, modo, margen, distancia, desenfoque, relleno, degradado,
             resplandor, anillo)
    if clave in _CACHE:
        return _CACHE[clave]
    s = 2 if ancho * alto <= AREA_SUPERMUESTREO else 1
    tam = (ancho * s, alto * s)
    m = margen * s
    caja = (m, m, tam[0] - m - 1, tam[1] - m - 1)
    r = min(radio * s, (caja[2] - caja[0]) // 2, (caja[3] - caja[1]) // 2)
    forma = Image.new("L", tam, 0)
    ImageDraw.Draw(forma).rounded_rectangle(caja, r, fill=255)
    imagen = _capa(tam, tema.FONDO)
    d, b = distancia * s, desenfoque * s
    if modo == "elevado":
        for color, dx in ((resplandor or tema.SOMBRA, d), (tema.LUZ, -d)):
            sombra = ImageChops.offset(forma, dx, dx).filter(ImageFilter.GaussianBlur(b))
            imagen.paste(_capa(tam, color), (0, 0), sombra)
    cuerpo = _degradado(tam, *degradado) if degradado else _capa(tam, relleno)
    imagen.paste(cuerpo, (0, 0), forma)
    if modo == "hundido":
        for color, dx in ((tema.SOMBRA, d), (tema.LUZ, -d)):
            hueco = ImageChops.invert(ImageChops.offset(forma, dx, dx))
            alfa = ImageChops.multiply(hueco.filter(ImageFilter.GaussianBlur(b)), forma)
            imagen.paste(_capa(tam, color), (0, 0), alfa)
    if anillo:
        grosor = max(2, round(1.5 * s * tema.ESCALA))
        ImageDraw.Draw(imagen).rounded_rectangle(caja, r, outline=_rgb(anillo), width=grosor)
    if s > 1:
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)
    if len(_CACHE) > LIMITE_CACHE:
        _CACHE.clear()
    foto = ImageTk.PhotoImage(imagen)
    _CACHE[clave] = foto
    return foto


class Panel(tk.Canvas):
    """Superficie con un Frame 'interior' para el contenido.

    ajustar=None: el contenido llena el panel; 'alto': el alto sigue al contenido;
    'ambos': ancho y alto siguen al contenido.
    """

    def __init__(self, padre: tk.Misc, modo: str = "elevado", radio: int = 18,
                 relleno: int = 18, distancia: int = 6, desenfoque: int = 9,
                 ajustar: str | None = None, color: str | None = None):
        super().__init__(padre, bg=tema.FONDO, highlightthickness=0, bd=0, width=1, height=1)
        px = tema.px
        self._estilo = dict(radio=px(radio), modo=modo, distancia=px(distancia),
                            desenfoque=px(desenfoque), relleno=color or tema.FONDO)
        self._margen = margen_elevado(distancia, desenfoque) if modo == "elevado" else 0
        self._borde = self._margen + px(relleno)
        self._ajustar = ajustar
        self._foto = None
        self._tarea = None
        self.interior = tk.Frame(self, bg=color or tema.FONDO)
        self._fondo = self.create_image(0, 0, anchor="nw")
        self._ventana = self.create_window(self._borde, self._borde, window=self.interior,
                                           anchor="nw")
        self.bind("<Configure>", self._al_redimensionar)
        if ajustar:
            self.interior.bind("<Configure>", self._al_ajustar_interior, add="+")

    def _al_redimensionar(self, evento: tk.Event) -> None:
        if self._ajustar != "ambos":
            self.itemconfigure(self._ventana, width=max(1, evento.width - 2 * self._borde))
        if not self._ajustar:
            self.itemconfigure(self._ventana, height=max(1, evento.height - 2 * self._borde))
        if self._tarea:
            self.after_cancel(self._tarea)
        self._tarea = self.after(30, self._pintar)

    def _al_ajustar_interior(self, evento: tk.Event) -> None:
        borde = 2 * self._borde
        if self._ajustar == "ambos":
            self.configure(width=evento.width + borde, height=evento.height + borde)
        else:
            self.configure(height=evento.height + borde)

    def _pintar(self) -> None:
        self._tarea = None
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 4 or alto < 4:
            return
        self._foto = superficie(ancho, alto, margen=self._margen, **self._estilo)
        self.itemconfigure(self._fondo, image=self._foto)


class Boton(tk.Canvas):
    """Botón con icono; variantes 'primario' (cian, con resplandor) y 'secundario'."""

    def __init__(self, padre: tk.Misc, texto: str = "", icono: str | None = None,
                 comando: Callable[[], None] | None = None, variante: str = "secundario",
                 estado: str = "normal"):
        super().__init__(padre, bg=tema.FONDO, highlightthickness=0, bd=0, takefocus=1,
                         cursor="hand2")
        self._d, self._b = tema.px(3), tema.px(5)
        self._m = self._d + 2 * self._b
        self._texto, self._icono, self._comando = texto, icono, comando
        self._variante, self._estado = variante, estado
        self._hover = self._presion = self._foco = False
        self._foto = None
        self._img = self.create_image(0, 0, anchor="nw")
        self._ico = self.create_text(0, 0, anchor="w", font=tema.fuente_icono(13))
        self._lbl = self.create_text(0, 0, anchor="w", font=tema.fuentes.boton)
        self.bind("<Enter>", lambda _e: self._cambiar(hover=True))
        self.bind("<Leave>", lambda _e: self._cambiar(hover=False, presion=False))
        self.bind("<ButtonPress-1>", lambda _e: self._cambiar(presion=True))
        self.bind("<ButtonRelease-1>", self._soltar)
        self.bind("<FocusIn>", lambda _e: self._cambiar(foco=True))
        self.bind("<FocusOut>", lambda _e: self._cambiar(foco=False))
        self.bind("<space>", lambda _e: self.invocar())
        self.bind("<Return>", lambda _e: self.invocar())
        self._medir()

    def configurar(self, texto: str | None = None, estado: str | None = None) -> None:
        if texto is not None:
            self._texto = texto
        if estado is not None:
            self._estado = estado
        self._medir()

    def invocar(self) -> None:
        if self._estado != "disabled" and self._comando:
            self.after_idle(self._comando)

    def _soltar(self, _evento) -> None:
        disparar = self._presion and self._hover
        self._cambiar(presion=False)
        if disparar:
            self.invocar()

    def _cambiar(self, **cambios) -> None:
        for clave, valor in cambios.items():
            setattr(self, "_" + clave, valor)
        self._pintar()

    def _medir(self) -> None:
        px = tema.px
        ancho_ico = tema.fuente_icono(13).measure(tema.glifo(self._icono)) if self._icono else 0
        ancho_txt = tema.fuentes.boton.measure(self._texto) if self._texto else 0
        hueco = px(8) if self._icono and self._texto else 0
        self._h = px(40)
        self._w = ancho_ico + hueco + ancho_txt + 2 * px(17) if self._texto else self._h
        m = self._m
        self.configure(width=self._w + 2 * m, height=self._h + 2 * m,cursor="arrow" if self._estado == "disabled" else "hand2")
        x = m + (self._w - ancho_ico) // 2 if not self._texto else m + px(17)
        y = m + self._h // 2
        self.coords(self._ico, x, y)
        self.coords(self._lbl, x + ancho_ico + hueco, y)
        self.itemconfigure(self._ico, text=tema.glifo(self._icono) if self._icono else "")
        self.itemconfigure(self._lbl, text=self._texto)
        self._pintar()

    def _pintar(self) -> None:
        primario = self._variante == "primario"
        apagado = self._estado == "disabled"
        base = dict(radio=tema.px(12), margen=self._m, distancia=self._d, desenfoque=self._b,
                    anillo=tema.CIAN_CLARO if self._foco and not apagado else None)
        if apagado:
            estilo = dict(modo="plano", relleno=tema.mezclar(tema.CIAN_OSCURO, tema.FONDO, .65)
                          if primario else tema.HOVER)
            tinta = tema.mezclar(tema.TINTA_SOBRE_CIAN, tema.CIAN_OSCURO, .5) if primario \
                else tema.TEXTO_TENUE
            tinta_icono = tinta
        elif primario:
            if self._presion:
                estilo = dict(modo="hundido", relleno=tema.CIAN_OSCURO)
            else:
                degradado = ("#6fdcf8", "#14a0c8") if self._hover else ("#4fd3f5", tema.CIAN_OSCURO)
                estilo = dict(modo="elevado", degradado=degradado,
                              resplandor=tema.CIAN_RESPLANDOR)
            tinta = tinta_icono = tema.TINTA_SOBRE_CIAN
        else:
            if self._presion:
                estilo = dict(modo="hundido")
            else:
                estilo = dict(modo="elevado", relleno=tema.HOVER if self._hover else tema.FONDO)
            tinta = tema.TEXTO
            tinta_icono = tema.CIAN_CLARO if self._hover else tema.CIAN
        self._foto = superficie(self._w + 2 * self._m, self._h + 2 * self._m, **base, **estilo)
        self.itemconfigure(self._img, image=self._foto)
        self.itemconfigure(self._ico, fill=tinta_icono)
        self.itemconfigure(self._lbl, fill=tinta)


class Campo(tk.Canvas):
    """Campo hundido con un Entry centrado; anillo cian con foco y magenta si hay error."""

    def __init__(self, padre: tk.Misc, variable: tk.StringVar | None = None, ancho: int = 52,
                 alto: int = 34, con_entrada: bool = True):
        self._w, self._h = tema.px(ancho), tema.px(alto)
        super().__init__(padre, width=self._w, height=self._h, bg=tema.FONDO,
                         highlightthickness=0, bd=0)
        self._error = self._foco = False
        self._foto = None
        self._img = self.create_image(0, 0, anchor="nw")
        self.entrada: tk.Entry | None = None
        if con_entrada:
            self.entrada = tk.Entry(
                self, textvariable=variable, justify="center", font=tema.fuentes.celda,
                fg=tema.TEXTO, bg=tema.FONDO, relief="flat", bd=0, highlightthickness=0,
                insertbackground=tema.CIAN, selectbackground=tema.CIAN_OSCURO,
                selectforeground="#ffffff")
            self.create_window(self._w // 2, self._h // 2, window=self.entrada,
                               width=self._w - tema.px(14))
            self.entrada.bind("<FocusIn>", lambda _e: self._cambiar(foco=True), add="+")
            self.entrada.bind("<FocusOut>", lambda _e: self._cambiar(foco=False), add="+")
            self.bind("<Button-1>", lambda _e: self.entrada.focus_set())
        self._pintar()

    def marcar_error(self, error: bool) -> None:
        if error != self._error:
            self._cambiar(error=error)

    def _cambiar(self, **cambios) -> None:
        for clave, valor in cambios.items():
            setattr(self, "_" + clave, valor)
        self._pintar()

    def _pintar(self) -> None:
        relleno = tema.MAGENTA_FONDO if self._error else tema.FONDO
        anillo = tema.MAGENTA if self._error else (tema.CIAN if self._foco else None)
        self._foto = superficie(self._w, self._h, tema.px(10), modo="hundido",
                                distancia=tema.px(2), desenfoque=tema.px(3), relleno=relleno,
                                anillo=anillo)
        self.itemconfigure(self._img, image=self._foto)
        if self.entrada:
            self.entrada.configure(bg=relleno)


def chip(padre: tk.Misc, icono: str, color: str, fondo: str | None = None, tamano: int = 40,
         radio: int = 12, tamano_icono: int = 15,
         degradado: tuple[str, str] | None = None) -> tk.Canvas:
    """Icono dentro de un cuadrado elevado y teñido."""
    px = tema.px
    d, b = px(3), px(4)
    m = d + 2 * b
    lado = px(tamano)
    lienzo = tk.Canvas(padre, width=lado + 2 * m, height=lado + 2 * m, bg=tema.FONDO,
                       highlightthickness=0, bd=0)
    lienzo._foto = superficie(lado + 2 * m, lado + 2 * m, px(radio), "elevado", margen=m,
                              distancia=d, desenfoque=b, relleno=fondo or tema.FONDO,
                              degradado=degradado)
    lienzo.create_image(0, 0, anchor="nw", image=lienzo._foto)
    lienzo.create_text(m + lado // 2, m + lado // 2, text=tema.glifo(icono), fill=color,
                       font=tema.fuente_icono(tamano_icono))
    return lienzo


class Pastilla(tk.Canvas):
    """Resultado redondeado (FR): cian si aprueba, magenta si no."""

    TONOS = {"cian": (tema.CIAN_FONDO, tema.CIAN_CLARO),
             "magenta": (tema.MAGENTA_FONDO, tema.MAGENTA_CLARO)}

    def __init__(self, padre: tk.Misc, ancho: int = 50, alto: int = 26):
        self._w, self._h = tema.px(ancho), tema.px(alto)
        super().__init__(padre, width=self._w, height=self._h, bg=tema.FONDO,
                         highlightthickness=0, bd=0)
        self._img = self.create_image(0, 0, anchor="nw")
        self._txt = self.create_text(self._w // 2, self._h // 2, font=tema.fuentes.celda_fuerte)
        self._foto = None

    def mostrar(self, texto: str, tono: str | None) -> None:
        if not tono:
            self.itemconfigure(self._img, image="")
            self.itemconfigure(self._txt, text="")
            return
        fondo, tinta = self.TONOS[tono]
        self._foto = superficie(self._w, self._h, self._h // 2, "plano", relleno=fondo)
        self.itemconfigure(self._img, image=self._foto)
        self.itemconfigure(self._txt, text=texto, fill=tinta)


class Barra(tk.Canvas):
    """Barra de progreso: canal hundido con relleno en degradado cian."""

    def __init__(self, padre: tk.Misc, ancho: int = 140, alto: int = 10):
        self._w, self._h = tema.px(ancho), tema.px(alto)
        super().__init__(padre, width=self._w, height=self._h, bg=tema.FONDO,
                         highlightthickness=0, bd=0)
        self._canal = superficie(self._w, self._h, self._h // 2, "hundido",
                                 distancia=tema.px(1), desenfoque=tema.px(2))
        self.create_image(0, 0, anchor="nw", image=self._canal)
        self._relleno = self.create_image(tema.px(2), tema.px(2), anchor="nw")
        self._foto = None

    def mostrar(self, fraccion: float) -> None:
        interior = self._w - 2 * tema.px(2)
        alto = self._h - 2 * tema.px(2)
        ancho = round(interior * max(0.0, min(fraccion, 1.0)))
        if ancho < 2:
            self.itemconfigure(self._relleno, image="")
            return
        self._foto = superficie(max(ancho, alto), alto, alto // 2, "plano",
                                degradado=(tema.CIAN_OSCURO, tema.CIAN))
        self.itemconfigure(self._relleno, image=self._foto)
