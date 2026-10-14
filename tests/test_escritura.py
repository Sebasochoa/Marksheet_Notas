import importlib.util
import io

import pdfplumber
import pytest
from pypdf import PasswordType, PdfReader

from marksheet.deteccion import detectar_plantilla
from marksheet.escritura import escribir_anotaciones
from marksheet.modelos import Anotacion, FilaPlantilla
from marksheet.notas import calificar
from marksheet_sintetica import crear_pdf

NOTAS = ["4", "5", "3", "4"]
VALORES_ESPERADOS = ["4", "5", "3", "4", "16", "8"]
TOLERANCIA_VERTICAL = 2.0
MARGEN_GRILLA = 15.0
hay_aes = any(importlib.util.find_spec(m) for m in ("cryptography", "Crypto"))
con_aes = pytest.mark.skipif(not hay_aes, reason="AES necesita cryptography o pycryptodome")
ALGORITMOS = ["RC4-40", "RC4-128", pytest.param("AES-128", marks=con_aes),
              pytest.param("AES-256", marks=con_aes)]


def llenar(original: bytes, fila: FilaPlantilla, carpeta) -> bytes:
    ruta = carpeta / "salida.pdf"
    anotacion = Anotacion(fila.ubicacion, calificar(NOTAS).textos_por_columna())
    escribir_anotaciones(original, [anotacion], str(ruta))
    return ruta.read_bytes()


def llenar_primera_fila(original: bytes, carpeta) -> bytes:
    return llenar(original, detectar_plantilla(original).filas[0], carpeta)


def firma_de_cifrado(pdf_bytes: bytes) -> tuple:
    lector = PdfReader(io.BytesIO(pdf_bytes))
    acceso = lector.decrypt("")
    cifrado = lector.trailer["/Encrypt"].get_object()
    return (int(cifrado["/V"]), int(cifrado["/R"]), int(cifrado.get("/Length", 40)),
            int(cifrado["/P"]), acceso)


def metadatos(pdf_bytes: bytes) -> dict:
    lector = PdfReader(io.BytesIO(pdf_bytes))
    if lector.is_encrypted:
        lector.decrypt("")
    return dict(lector.metadata or {})


def palabras_en_la_fila(pdf_bytes: bytes, fila: FilaPlantilla) -> list[dict]:
    ubicacion = fila.ubicacion
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        palabras = pdf.pages[ubicacion.pagina].extract_words()
    inicio_grilla = min(ubicacion.x_por_columna.values()) - MARGEN_GRILLA
    return sorted((p for p in palabras if p["x0"] >= inicio_grilla
                   and abs((p["top"] + p["bottom"]) / 2 - ubicacion.y_centro) < TOLERANCIA_VERTICAL),
                  key=lambda p: p["x0"])


@pytest.mark.parametrize("algoritmo", ALGORITMOS)
def test_salida_conserva_el_cifrado_del_original(algoritmo, tmp_path):
    original = crear_pdf(algoritmo)
    assert firma_de_cifrado(llenar_primera_fila(original, tmp_path)) == firma_de_cifrado(original)


def test_contrasena_de_propietario_desconocida_sigue_restringiendo(tmp_path):
    original = crear_pdf("RC4-128", contrasena_propietario="secreta")
    salida = firma_de_cifrado(llenar_primera_fila(original, tmp_path))
    assert salida == firma_de_cifrado(original) and salida[-1] == PasswordType.USER_PASSWORD


def test_original_sin_cifrar_produce_salida_sin_cifrar(tmp_path):
    salida = llenar_primera_fila(crear_pdf(algoritmo=None), tmp_path)
    assert not PdfReader(io.BytesIO(salida)).is_encrypted


def test_conserva_los_metadatos(tmp_path):
    original = crear_pdf()
    assert metadatos(llenar_primera_fila(original, tmp_path)) == metadatos(original)


def test_valores_quedan_centrados_en_sus_celdas(tmp_path):
    original = crear_pdf()
    fila = detectar_plantilla(original).filas[0]
    palabras = palabras_en_la_fila(llenar(original, fila, tmp_path), fila)
    assert [p["text"] for p in palabras] == VALORES_ESPERADOS
    assert [(p["x0"] + p["x1"]) / 2 for p in palabras] == pytest.approx(
        list(fila.ubicacion.x_por_columna.values()), abs=0.01)


def test_escribe_solo_en_la_pagina_de_cada_alumno(tmp_path):
    original = crear_pdf(paginas=2)
    filas = detectar_plantilla(original).filas
    ultima = filas[-1]
    salida = llenar(original, ultima, tmp_path)
    assert [p["text"] for p in palabras_en_la_fila(salida, ultima)] == VALORES_ESPERADOS
    assert palabras_en_la_fila(salida, filas[len(filas) // 2 - 1]) == []


def test_pdf_generado_se_reconoce_como_ya_llenado(tmp_path):
    assert detectar_plantilla(llenar_primera_fila(crear_pdf(), tmp_path)).ya_tiene_valores
