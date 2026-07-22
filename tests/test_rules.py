"""Tests de las reglas de validación de negocio."""

from factura_ai.domain.models import Factura, LineItem, Severidad
from factura_ai.validation.rules import (
    validar,
    validar_fecha,
    validar_igv,
    validar_suma_items,
    validar_total,
)


def _factura_valida() -> Factura:
    return Factura(
        ruc_emisor="20512345671",
        razon_social="EMPRESA DEMO SAC",
        numero="F001-00001234",
        fecha_emision="2026-05-14",
        items=[LineItem(descripcion="Producto", cantidad=1,
                        precio_unitario=1000.0, importe=1000.0)],
        base_imponible=1000.0,
        igv=180.0,
        total=1180.0,
    )


def test_factura_valida_sin_issues():
    assert validar(_factura_valida()) == []


def test_igv_incorrecto_es_error():
    f = _factura_valida()
    f.igv = 150.0  # debería ser 180
    issues = validar_igv(f)
    assert len(issues) == 1
    assert issues[0].severidad is Severidad.ERROR
    assert issues[0].campo == "igv"


def test_igv_dentro_de_tolerancia_por_redondeo():
    f = _factura_valida()
    f.igv = 180.05  # dentro de la tolerancia de S/ 0.10
    assert validar_igv(f) == []


def test_total_incorrecto_es_error():
    f = _factura_valida()
    f.total = 1200.0  # debería ser 1180
    assert any(i.campo == "total" for i in validar_total(f))


def test_suma_items_distinta_es_advertencia():
    f = _factura_valida()
    f.items[0].importe = 900.0  # ya no suma la base imponible
    issues = validar_suma_items(f)
    assert issues and issues[0].severidad is Severidad.ADVERTENCIA


def test_fecha_futura_es_error():
    f = _factura_valida()
    f.fecha_emision = "2099-01-01"
    assert any(i.campo == "fecha_emision" for i in validar_fecha(f))


def test_fecha_mal_formateada_es_error():
    f = _factura_valida()
    f.fecha_emision = "14/05/2026"
    assert any(i.campo == "fecha_emision" for i in validar_fecha(f))
