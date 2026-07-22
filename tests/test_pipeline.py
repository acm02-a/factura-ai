"""Tests del pipeline completo y del extractor por reglas, de punta a punta."""

from pathlib import Path

from factura_ai.domain.models import Decision
from factura_ai.extraction.rule_based import RuleBasedExtractor
from factura_ai.pipeline import procesar_archivos, procesar_texto

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_extractor_reglas_parsea_campos():
    texto = (SAMPLES / "factura_01.txt").read_text(encoding="utf-8")
    f = RuleBasedExtractor().extract(texto)
    assert f.ruc_emisor == "20512345671"
    assert f.numero == "F001-00001234"
    assert f.fecha_emision == "2026-05-14"
    assert f.total == 6938.40
    assert len(f.items) == 3


def test_factura_limpia_se_auto_aprueba():
    texto = (SAMPLES / "factura_01.txt").read_text(encoding="utf-8")
    r = procesar_texto(texto)
    assert r.decision is Decision.AUTO_APROBAR
    assert r.confianza == 100.0
    assert r.issues == []


def test_ruc_invalido_va_a_revision():
    texto = (SAMPLES / "factura_04_ruc_invalido.txt").read_text(encoding="utf-8")
    r = procesar_texto(texto)
    assert r.decision is Decision.REVISAR
    assert any(i.campo == "ruc_emisor" for i in r.errores)


def test_ilegible_se_rechaza():
    texto = (SAMPLES / "factura_05_ilegible.txt").read_text(encoding="utf-8")
    r = procesar_texto(texto)
    assert r.decision is Decision.RECHAZAR


def test_lote_completo_reparte_decisiones():
    rutas = sorted(SAMPLES.glob("*.txt"))
    resultados = procesar_archivos(rutas)
    decisiones = [r.decision for r in resultados]
    assert decisiones.count(Decision.AUTO_APROBAR) == 2
    assert decisiones.count(Decision.REVISAR) == 2
    assert decisiones.count(Decision.RECHAZAR) == 1
