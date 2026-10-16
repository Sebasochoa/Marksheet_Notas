"""Parámetros de la Mark Sheet: único lugar a tocar si cambia el formato o las reglas."""

# Identificadores internos de los criterios, en orden. Se detectan por posición, no por nombre:
# el 4.º se imprime "LA" (Language) en Juniors y "GV" (Grammar and Vocabulary) en Adults.
CRITERIOS = ("IC", "DM", "PR", "LA")
COLUMNA_TOTAL = "TOTAL"
COLUMNA_FINAL = "FR"
COLUMNAS_GRILLA = CRITERIOS + (COLUMNA_TOTAL, COLUMNA_FINAL)

NOTA_MINIMA = 0
NOTA_MAXIMA = 5
DIVISOR_FINAL = 2          # "To obtain FR divide TOTAL by 2"
FINAL_APROBATORIO = 7      # "70% (7 out of 10) in the FR"

FUENTE = "Helvetica"       # misma fuente y tamaño que las filas del reporte
TAMANO_FUENTE = 8
COLOR_TEXTO_RGB = (0.0, 0.0, 0.0)
