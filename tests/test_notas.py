import pytest

from marksheet.errores import CalificacionInvalida
from marksheet.notas import calificar, es_nota_valida, formatear, revisar


def test_calcula_total_y_final():
    calificacion = calificar(["4", "5", "3", "4"])
    assert (calificacion.total, calificacion.final, calificacion.aprobada) == (16, 8, True)


def test_final_menor_a_siete_desaprueba():
    assert not calificar(["2", "2", "3", "2"]).aprobada


def test_acepta_decimales_con_punto_o_coma():
    assert calificar(["4,5", "3.5", "4", "5"]).textos_por_columna() == {
        "IC": "4.5", "DM": "3.5", "PR": "4", "LA": "5", "TOTAL": "17", "FR": "8.5"}


@pytest.mark.parametrize("textos", [["4", "", "3", "2"], ["6", "4", "4", "4"],
                                    ["x", "1", "1", "1"], ["-1", "1", "1", "1"], ["4", "4", "4"]])
def test_rechaza_filas_incompletas_o_fuera_de_rango(textos):
    with pytest.raises(CalificacionInvalida):
        calificar(textos)


@pytest.mark.parametrize("texto, esperado", [("5", True), ("0", True), ("2,5", True),
                                             ("5.1", False), ("", False), ("nan", False)])
def test_valida_cada_nota(texto, esperado):
    assert es_nota_valida(texto) is esperado


def test_formatea_sin_ceros_sobrantes():
    assert [formatear(v) for v in (16.0, 8.5, 0.0, 8.25)] == ["16", "8.5", "0", "8.25"]


def test_revision_separa_calificadas_invalidas_y_vacias():
    revision = revisar([["4", "4", "4", "4"], ["", " ", "", ""], ["9", "1", "1", "1"]])
    assert (list(revision.calificaciones), revision.vacias, revision.invalidas) == ([0], (1,), (2,))
