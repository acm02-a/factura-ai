"""Anclaje de pytest: al existir este archivo en la raiz, pytest agrega esta
carpeta a sys.path y los tests pueden importar el paquete `factura_ai` sin
instalarlo. Sin esto, `pytest tests/` falla en un checkout limpio (ej. CI)."""
