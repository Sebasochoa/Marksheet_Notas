import pytest

from marksheet.config import COLUMNAS_GRILLA
from marksheet.deteccion import detectar_plantilla
from marksheet.deteccion.geometria import Borde, Palabra
from marksheet.deteccion.grilla import buscar_encabezado, construir_grilla
from marksheet.deteccion.renglones import (agrupar_en_renglones, leer_renglon_alumno,
                                           separar_apellidos_y_nombres)
from marksheet.errores import PlantillaNoReconocida
from marksheet_sintetica import (ALUMNOS, CORTES_COLUMNAS, ROTULOS, ROTULOS_ADULTOS,
                                 centro_fila, centros_columnas, crear_pdf,
                                 crear_pdf_sin_plantilla)

ANCHO_LETRA, ESPACIO, ALTO_TEXTO = 5.0, 2.2, 8.0
TOP_PRIMER_ALUMNO = 163.87


def palabra(texto, x0, top=100.0):
    return Palabra(texto, x0, x0 + ANCHO_LETRA * len(texto), top, top + ALTO_TEXTO)


def palabras_desde(texto, x0, top):
    palabras = []
    for parte in texto.split():
        palabras.append(palabra(parte, x0, top))
        x0 += ANCHO_LETRA * len(parte) + ESPACIO
    return palabras


def renglon_alumno(numero, apellidos, nombres, top=TOP_PRIMER_ALUMNO, marca=""):
    palabras = [palabra(numero, 25, top)] + ([palabra(marca, 50, top)] if marca else [])
    palabras += [palabra("10000" + numero, 70, top)]
    palabras += palabras_desde(apellidos, 135, top) + palabras_desde(nombres, 267, top)
    return leer_renglon_alumno(palabras)


def palabras_de_encabezado(rotulos=ROTULOS):
    return [palabra(r, centro - ANCHO_LETRA * len(r) / 2, top=139.4)
            for r, centro in zip(rotulos, centros_columnas())]


def encabezado(rotulos=ROTULOS):
    return buscar_encabezado([palabras_de_encabezado(rotulos)])


def lineas(vertical, posiciones, desde, hasta):
    """Cada línea de la grilla es un rectángulo de 0.5 pt: dos bordes paralelos."""
    if vertical:
        return [Borde(True, x + d, x + d, desde, hasta) for x in posiciones for d in (0, 0.5)]
    return [Borde(False, desde, hasta, y + d, y + d) for y in posiciones for d in (0, 0.5)]


def test_agrupa_palabras_por_renglon_y_las_ordena():
    palabras = [palabra("B", 50, 100.5), palabra("A", 10, 100.0), palabra("C", 10, 114.2)]
    assert [[p.texto for p in r] for r in agrupar_en_renglones(palabras)] == [["A", "B"], ["C"]]


def test_lee_renglon_con_marca():
    alumno = renglon_alumno("5", "COLINA VIZCARRA", "CESAR", marca="F")
    assert (alumno.numero, alumno.marca, alumno.codigo) == ("5", "F", "100005")


@pytest.mark.parametrize("textos", [
    (("5", 405), ("5", 433), ("20", 520), ("10", 554)),      # fila de máximos
    (("N0", 28), ("CODE", 86), ("LAST", 172)),                # encabezado izquierdo
    (("1", 25), ("365320", 70)),                               # código sin nombre
])
def test_descarta_renglones_que_no_son_de_alumnos(textos):
    assert leer_renglon_alumno([palabra(texto, x) for texto, x in textos]) is None


def test_separa_apellidos_por_el_inicio_de_la_columna_de_nombres():
    renglones = [renglon_alumno("1", "VIRU LA ROSA", "NICOLE HELENA", 100),
                 renglon_alumno("2", "CUBA PAZ", "KRISTIAN", 114),
                 renglon_alumno("3", "YOZA", "KIARA NAMIE", 128)]
    assert separar_apellidos_y_nombres(renglones) == [
        ("VIRU LA ROSA", "NICOLE HELENA"), ("CUBA PAZ", "KRISTIAN"), ("YOZA", "KIARA NAMIE")]


def test_con_una_sola_fila_separa_por_el_mayor_hueco():
    renglones = [renglon_alumno("1", "LEON REY", "LAURA EMILIA")]
    assert separar_apellidos_y_nombres(renglones) == [("LEON REY", "LAURA EMILIA")]


def test_encabezado_ignora_la_leyenda_que_repite_las_siglas():
    leyenda = [[palabra(sigla, 420, top), palabra("=", 445, top)]
               for sigla, top in (("IC", 630), ("DM", 642))]
    rotulos = encabezado()
    hallado = buscar_encabezado(leyenda + [list(rotulos.values())])
    assert set(hallado) == set(COLUMNAS_GRILLA) and all(p.top == 139.4 for p in hallado.values())


def test_criterios_se_reconocen_por_posicion_y_no_por_nombre():
    hallado = encabezado(ROTULOS_ADULTOS)
    assert [hallado[c].texto for c in COLUMNAS_GRILLA] == list(ROTULOS_ADULTOS)


def test_renglon_sin_total_no_es_encabezado():
    sin_total = [p for p in palabras_de_encabezado() if p.texto != "TOTAL"]
    assert buscar_encabezado([sin_total]) is None


def test_grilla_centra_columnas_y_filas_entre_sus_lineas():
    bordes = (lineas(True, CORTES_COLUMNAS, 137.48, 300.0)
              + lineas(False, (137.48, 147.50, 157.52, 171.72), 392.70, 574.40))
    grilla = construir_grilla(encabezado(), bordes, alto_pagina=842.0)
    assert list(grilla.x_por_columna.values()) == pytest.approx(centros_columnas())
    assert grilla.centros_de_filas([renglon_alumno("1", "PEREZ", "ANA")]) == pytest.approx(
        [centro_fila(0)])


def test_sin_lineas_usa_el_centro_de_rotulos_y_renglones():
    rotulos = encabezado()
    grilla = construir_grilla(rotulos, bordes=[], alto_pagina=842.0)
    alumno = renglon_alumno("1", "PEREZ", "ANA")
    assert grilla.x_por_columna["IC"] == pytest.approx(rotulos["IC"].centro_x)
    assert grilla.centros_de_filas([alumno]) == [pytest.approx(alumno.centro_y)]


def test_detecta_los_alumnos_de_una_marksheet_cifrada():
    plantilla = detectar_plantilla(crear_pdf("RC4-40"))
    alumnos = [fila.alumno for fila in plantilla.filas]
    assert [a.nombre_completo for a in alumnos] == [
        "PEREZ LOPEZ, ANA MARIA", "DE LA CRUZ SOTO, LUIS", "QUISPE, ROSA ELENA"]
    assert [a.marca for a in alumnos] == ["", "F", ""]
    assert not plantilla.ya_tiene_valores


def test_ubica_cada_alumno_en_el_centro_de_su_celda():
    filas = detectar_plantilla(crear_pdf()).filas
    assert [f.ubicacion.y_centro for f in filas] == pytest.approx(
        [centro_fila(i) for i in range(len(ALUMNOS))])
    assert list(filas[0].ubicacion.x_por_columna.values()) == pytest.approx(centros_columnas())


@pytest.mark.parametrize("rotulos", [ROTULOS, ROTULOS_ADULTOS])
def test_plantilla_informa_los_criterios_como_los_imprime_el_pdf(rotulos):
    plantilla = detectar_plantilla(crear_pdf(rotulos=rotulos))
    assert plantilla.rotulos_criterios == tuple(rotulos[:4])
    assert len(plantilla.filas) == len(ALUMNOS)


def test_detecta_cada_pagina_por_separado():
    filas = detectar_plantilla(crear_pdf(paginas=2)).filas
    assert [f.ubicacion.pagina for f in filas] == [0] * len(ALUMNOS) + [1] * len(ALUMNOS)


def test_rechaza_un_pdf_sin_plantilla():
    with pytest.raises(PlantillaNoReconocida):
        detectar_plantilla(crear_pdf_sin_plantilla())
