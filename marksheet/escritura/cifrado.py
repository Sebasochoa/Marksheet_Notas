"""Conserva en la salida el mismo cifrado, permisos y contraseña de propietario del original."""
from __future__ import annotations

import io
import secrets
from dataclasses import dataclass

from pypdf import PasswordType, PdfReader, PdfWriter
from pypdf.generic import DictionaryObject

from ..errores import FormatoNoSoportado

CONTRASENA_VACIA = ""
BYTES_CONTRASENA_ALEATORIA = 16
LONGITUD_RC4_BASICA = 40           # bits de /Length en RC4 de 40 bits
VERSION_AES_256 = 5                # /V de AES-256
REVISION_AES_256_ISO = 6           # /R 5 es el borrador de Adobe; /R 6, el de PDF 2.0
VERSION_CON_FILTROS = 4            # /V con crypt filters: RC4-128 o AES-128 según /CFM
METODO_AES_128 = "/AESV2"


@dataclass(frozen=True)
class Proteccion:
    algoritmo: str                 # nombre que acepta PdfWriter.encrypt(algorithm=...)
    permisos: int                  # valor /P del original
    contrasena_propietario: str


def abrir_descifrado(pdf_bytes: bytes) -> tuple[PdfReader, Proteccion | None]:
    """Lector listo para usar y la protección a reaplicar (None si el original no está cifrado)."""
    lector = PdfReader(io.BytesIO(pdf_bytes))
    if not lector.is_encrypted:
        return lector, None
    acceso = lector.decrypt(CONTRASENA_VACIA)
    if acceso == PasswordType.NOT_DECRYPTED:
        raise FormatoNoSoportado("El PDF pide contraseña para abrirse.")
    return lector, _proteccion_del_original(lector, acceso)


def aplicar(escritor: PdfWriter, proteccion: Proteccion) -> None:
    escritor.encrypt(CONTRASENA_VACIA, proteccion.contrasena_propietario,
                     permissions_flag=proteccion.permisos, algorithm=proteccion.algoritmo)


def _proteccion_del_original(lector: PdfReader, acceso: PasswordType) -> Proteccion:
    diccionario = lector.trailer["/Encrypt"].get_object()
    return Proteccion(
        algoritmo=_algoritmo(diccionario),
        permisos=int(diccionario["/P"]),
        contrasena_propietario=_contrasena_propietario(acceso),
    )


def _contrasena_propietario(acceso: PasswordType) -> str:
    """Si la clave vacía abrió el original como propietario, su contraseña de propietario es
    vacía y se replica igual. Si no, es desconocida: se usa una aleatoria para que los permisos
    restringidos sigan vigentes."""
    if acceso == PasswordType.OWNER_PASSWORD:
        return CONTRASENA_VACIA
    return secrets.token_hex(BYTES_CONTRASENA_ALEATORIA)


def _algoritmo(diccionario: DictionaryObject) -> str:
    """Traduce /V, /R, /Length y /CFM del diccionario /Encrypt al nombre que usa pypdf."""
    version = int(diccionario.get("/V", 0))
    if version == VERSION_AES_256:
        return "AES-256" if int(diccionario["/R"]) >= REVISION_AES_256_ISO else "AES-256-R5"
    if version == VERSION_CON_FILTROS and _usa_aes_128(diccionario):
        return "AES-128"
    longitud = int(diccionario.get("/Length", LONGITUD_RC4_BASICA))
    return "RC4-40" if longitud <= LONGITUD_RC4_BASICA else "RC4-128"


def _usa_aes_128(diccionario: DictionaryObject) -> bool:
    filtros = diccionario.get("/CF", DictionaryObject()).get_object()
    filtro = filtros.get(diccionario.get("/StmF", "/StdCF"), DictionaryObject()).get_object()
    return filtro.get("/CFM") == METODO_AES_128
