"""Errores esperables de la aplicación; la interfaz muestra su mensaje tal cual."""


class ErrorMarkSheet(Exception):
    """Base de todos los errores propios."""


class PlantillaNoReconocida(ErrorMarkSheet):
    """El PDF no contiene la grilla de notas con filas de alumnos."""


class FormatoNoSoportado(ErrorMarkSheet):
    """El PDF usa algo que la escritura no maneja (rotación, origen desplazado, contraseña)."""


class CalificacionInvalida(ErrorMarkSheet):
    """Una fila tiene notas incompletas o fuera de rango."""
