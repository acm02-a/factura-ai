"""Tests del validador de RUC (algoritmo de dígito verificador módulo 11)."""

from factura_ai.validation.ruc import digito_verificador, es_ruc_valido


def test_rucs_reales_validos():
    # RUCs reales de entidades peruanas (verificables públicamente).
    assert es_ruc_valido("20131312955")   # SUNAT
    assert es_ruc_valido("20100070970")
    assert es_ruc_valido("20131380951")


def test_digito_verificador_cambiado_es_invalido():
    # Mismo RUC con el último dígito alterado: el checksum lo rechaza.
    assert es_ruc_valido("20131312955")
    assert not es_ruc_valido("20131312954")


def test_formato_invalido():
    assert not es_ruc_valido("2013131295")     # 10 dígitos
    assert not es_ruc_valido("201313129555")   # 12 dígitos
    assert not es_ruc_valido("2013131295X")    # no numérico
    assert not es_ruc_valido("")
    assert not es_ruc_valido(None)


def test_prefijo_invalido():
    # Un número de 11 dígitos con checksum correcto pero prefijo no válido.
    base = "9912345678"
    ruc = base + str(digito_verificador(base))
    assert not es_ruc_valido(ruc)  # prefijo 99 no es tipo de contribuyente


def test_digito_verificador_coincide_con_generado():
    base = "2051234567"
    ruc = base + str(digito_verificador(base))
    assert es_ruc_valido(ruc)
