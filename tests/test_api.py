"""Tests de la API REST."""

from pathlib import Path

from fastapi.testclient import TestClient

from factura_ai.api.main import app

client = TestClient(app)
SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_procesar_factura_limpia():
    texto = (SAMPLES / "factura_01.txt").read_text(encoding="utf-8")
    r = client.post("/facturas/procesar", json={"texto": texto})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "auto_aprobar"
    assert body["factura"]["ruc_emisor"] == "20512345671"


def test_procesar_texto_vacio_es_422():
    r = client.post("/facturas/procesar", json={"texto": ""})
    assert r.status_code == 422  # validación de Pydantic (min_length)
