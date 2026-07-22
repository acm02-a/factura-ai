"""
Validación de RUC peruano (Registro Único de Contribuyentes).

Un RUC válido tiene 11 dígitos y su último dígito es un dígito verificador
calculado con el algoritmo de módulo 11 sobre los primeros 10. Además, los dos
primeros dígitos identifican el tipo de contribuyente (10, 15, 17 = persona
natural; 20 = persona jurídica; entre otros).

Implementar el checksum de verdad — en vez de solo chequear "son 11 dígitos" —
es lo que permite rechazar un RUC tipeado con un error, que es el caso real que
un sistema de facturación tiene que atajar.
"""

from __future__ import annotations

# Pesos oficiales aplicados a los primeros 10 dígitos del RUC.
_PESOS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)

# Prefijos de tipo de contribuyente aceptados por SUNAT.
_PREFIJOS_VALIDOS = ("10", "15", "16", "17", "20")


def digito_verificador(ruc10: str) -> int:
    """Calcula el dígito verificador esperado para los primeros 10 dígitos."""
    suma = sum(int(d) * peso for d, peso in zip(ruc10, _PESOS))
    resto = suma % 11
    resultado = 11 - resto
    if resultado == 10:
        return 0
    if resultado == 11:
        return 1
    return resultado


def es_ruc_valido(ruc: str | None) -> bool:
    """True si `ruc` es un RUC peruano válido (formato, prefijo y checksum)."""
    if not ruc:
        return False
    ruc = ruc.strip()
    if len(ruc) != 11 or not ruc.isdigit():
        return False
    if ruc[:2] not in _PREFIJOS_VALIDOS:
        return False
    return int(ruc[-1]) == digito_verificador(ruc[:10])


def tipo_contribuyente(ruc: str) -> str:
    """Describe el tipo de contribuyente según el prefijo del RUC."""
    return {
        "10": "Persona natural",
        "15": "Persona natural (no domiciliada)",
        "16": "Persona natural (no domiciliada)",
        "17": "Persona natural (no domiciliada)",
        "20": "Persona jurídica",
    }.get(ruc[:2], "Desconocido")
