"""Tests de humo: no requieren red ni credenciales.

Verifican que la lógica pura (prompts, parseo de límites, exportación a Word
y la degradación segura de la base de datos) funcione sin romperse.
"""

import ai
import db
import exportar
import prompts


# ── prompts ────────────────────────────────────────────────────────────────
def test_formato_config_vacio():
    assert prompts.formato_config({}) == ""


def test_formato_config_incluye_campos():
    cfg = {"edad": "9 años", "cantidad": "25", "preferencias": ["Trabajo en grupos"]}
    texto = prompts.formato_config(cfg)
    assert "9 años" in texto
    assert "25" in texto
    assert "Trabajo en grupos" in texto


def test_prompt_generacion_menciona_materia_y_grado():
    p = prompts.prompt_generacion("Matemática", "4° grado")
    assert "Matemática" in p
    assert "4° grado" in p


# ── ai: detección y parseo de límites (429) ──────────────────────────────────
def test_es_429_detecta_variantes():
    assert ai._es_429(Exception("429 RESOURCE_EXHAUSTED"))
    assert ai._es_429(Exception("Quota exceeded"))
    assert not ai._es_429(Exception("algo cualquiera"))


def test_segundos_espera_lee_retry_delay():
    err = Exception("429 ... retry_delay { seconds: 37 }")
    # 37 + 3 de margen
    assert ai._segundos_espera(err) == 40


def test_segundos_espera_default():
    assert ai._segundos_espera(Exception("sin info de retry")) == 60


# ── exportar: genera un .docx válido ─────────────────────────────────────────
def test_exportar_devuelve_docx():
    data = exportar.planificacion_a_docx(
        "Matemática", "4° grado", "# Tema\nFracciones\n- punto uno",
    )
    assert isinstance(data, (bytes, bytearray))
    # Un .docx es un ZIP: empieza con la firma "PK".
    assert data[:2] == b"PK"


# ── db: degrada sin credenciales (no debe romper) ────────────────────────────
def test_db_sin_credenciales():
    assert db.memoria_activa("", "") is False
    assert db.cargar_config("", "") == {}
    assert db.guardar_config("", "", {"x": 1}) is False
    assert db.recuperar_previas("", "", "Matemática") == ""
