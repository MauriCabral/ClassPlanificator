"""Wrapper de Gemini (SDK google-genai) con manejo amable de límites (429)."""

import re

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

import prompts


class LimiteAlcanzado(Exception):
    """Se alcanzó el cupo gratuito momentáneamente (error 429).

    segundos_espera: cuánto falta (aprox.) para poder volver a pedir.
    """

    def __init__(self, segundos_espera: int = 60):
        self.segundos_espera = segundos_espera
        super().__init__("Se alcanzó el límite de uso gratuito.")


class ErrorTemporalIA(Exception):
    """El servicio de Gemini falló de forma transitoria (error 5xx).

    No es un problema de cupo: suele resolverse reintentando en segundos.
    """

    def __init__(self):
        super().__init__("El servicio de IA no respondió; probá de nuevo en un momento.")


def _cliente(api_key: str) -> "genai.Client":
    return genai.Client(api_key=api_key)


def _es_429(err: Exception) -> bool:
    # El SDK nuevo expone .code en sus errores; igual chequeamos el texto
    # para cubrir cualquier variante.
    if getattr(err, "code", None) == 429:
        return True
    texto = str(err).lower()
    return "429" in texto or "resource_exhausted" in texto or "quota" in texto


def _segundos_espera(err: Exception) -> int:
    """Extrae del error de Gemini cuántos segundos hay que esperar.

    La API suele incluir algo como `retry_delay { seconds: 37 }` o
    `"retryDelay": "37s"`. Si no se encuentra, asumimos 60s (el cupo por
    minuto se renueva cada minuto).
    """
    texto = str(err)
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", texto)
    if not m:
        m = re.search(r"retryDelay[\"'\s:]+(\d+)s", texto)
    if not m:
        m = re.search(r"seconds[\"'\s:]+(\d+)", texto)
    if m:
        return int(m.group(1)) + 3  # pequeño margen
    return 60


def _lanzar_limite(err: Exception):
    raise LimiteAlcanzado(_segundos_espera(err)) from err


def _es_servidor_caido(err: Exception) -> bool:
    """True si Gemini devolvió un error 5xx (sobrecarga, falla interna, etc.)."""
    if isinstance(err, genai_errors.ServerError):
        return True
    return getattr(err, "code", None) in (500, 502, 503, 504)


def siguiente_pregunta(api_key, model_name, historial, config_texto=""):
    """Dada la conversación, devuelve la próxima pregunta o '[LISTO]'.

    historial: lista de dicts {"role": "user"|"assistant", "content": str}
    """
    cliente = _cliente(api_key)
    contenido = _historial_a_gemini(historial)
    try:
        resp = cliente.models.generate_content(
            model=model_name,
            contents=contenido,
            config=types.GenerateContentConfig(
                system_instruction=prompts.prompt_preguntas(config_texto),
            ),
        )
        return (resp.text or "").strip()
    except Exception as err:  # noqa: BLE001
        if _es_429(err):
            _lanzar_limite(err)
        if _es_servidor_caido(err):
            raise ErrorTemporalIA() from err
        raise


def generar_planificacion(api_key, model_name, materia, grado, historial,
                          previas="", config_texto=""):
    """Genera la planificación final con todo el contexto recopilado."""
    cliente = _cliente(api_key)
    sistema = prompts.prompt_generacion(materia, grado, previas, config_texto)
    resumen = _resumen_contexto(materia, grado, historial)
    try:
        resp = cliente.models.generate_content(
            model=model_name,
            contents=resumen,
            config=types.GenerateContentConfig(system_instruction=sistema),
        )
        return (resp.text or "").strip()
    except Exception as err:  # noqa: BLE001
        if _es_429(err):
            _lanzar_limite(err)
        if _es_servidor_caido(err):
            raise ErrorTemporalIA() from err
        raise


def _historial_a_gemini(historial):
    """Convierte el historial interno al formato de la API de Gemini."""
    out = []
    for msg in historial:
        role = "user" if msg["role"] == "user" else "model"
        out.append({"role": role, "parts": [{"text": msg["content"]}]})
    # Si el último turno fue del asistente (o no hay nada), pedimos arrancar.
    if not out or out[-1]["role"] == "model":
        out.append({"role": "user", "parts": [{"text": "Empecemos."}]})
    return out


def _resumen_contexto(materia, grado, historial):
    lineas = [f"Materia: {materia}", f"Grado: {grado}", "", "Contexto recopilado:"]
    for msg in historial:
        quien = "Docente" if msg["role"] == "user" else "Asistente"
        lineas.append(f"- {quien}: {msg['content']}")
    lineas.append("")
    lineas.append("Generá ahora la planificación completa.")
    return "\n".join(lineas)
