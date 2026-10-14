# Llenar Mark Sheet

Escribe las notas del Speaking Test (IC, DM, PR, LA) sobre la Mark Sheet en PDF que genera
BI Publisher, calcula TOTAL y FR, y guarda una copia idéntica al original con el mismo
cifrado, permisos y metadatos. Requiere Python 3.9 o superior.

## Estructura

```
main.py                  punto de entrada: python main.py [archivo.pdf]
marksheet/
  config.py              columnas, rango de notas, regla de FR y fuente
  modelos.py             Alumno, Ubicacion, FilaPlantilla, Plantilla, Anotacion
  errores.py             excepciones propias (la interfaz muestra su mensaje)
  notas.py               validación, TOTAL, FR, formato y revisión de filas
  deteccion/             lectura de la plantilla
    geometria.py         Palabra, Borde y utilidades geométricas
    renglones.py         N°, marca, código, apellidos y nombres
    grilla.py            encabezado, columnas y filas de la grilla
    detector.py          orquestación por página (único módulo con pdfplumber)
  escritura/             escritura sobre el PDF
    capa.py              capa transparente con los valores (reportlab)
    cifrado.py           lee y reaplica el cifrado del original (pypdf)
    escritor.py          fusión de la capa, metadatos y guardado
  interfaz/              tkinter
    fila.py              fila de un alumno: campos y TOTAL/FR en vivo
    tabla.py             tabla desplazable y navegación con teclado
    ventana.py           flujo abrir → ingresar → generar
    inicio.py            arranque y nitidez en pantallas con escalado
tests/                   pytest sobre una Mark Sheet sintética con datos ficticios
```

Las dependencias van en un solo sentido: `interfaz` usa `deteccion`, `escritura` y `notas`;
estos no conocen la interfaz ni entre sí, y comparten solo `modelos`, `config` y `errores`.

## Comandos

```
pip install -r requirements-dev.txt
python main.py
python -m pytest
pyinstaller --onefile --windowed --name LlenarMarkSheet main.py
```
