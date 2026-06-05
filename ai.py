"""Wrapper de Gemini con manejo amable de límites (error 429)."""

import google.generativeai as genai

import prompts


class LimiteAlcanzado(Exception):
    """Se alcanzó el cupo gratuito momentáneamente (error 429)."""


def _configurar(api_key: str):
    genai.configure(api_key=api_key)


def _modelo(api_key: str, model_name: str, system_instruction: str):
    _configurar(api_key)
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )


def _es_429(err: Exception) -> bool:
    texto = str(err).lower()
    return "429" in texto or "resource_exhausted" in texto or "quota" in texto


def siguiente_pregunta(api_key, model_name, historial, config_texto=""):
    """Dada la conversación, devuelve la próxima pregunta o '[LISTO]'.

    historial: lista de dicts {"role": "user"|"assistant", "content": str}
    """
    modelo = _modelo(api_key, model_name, prompts.prompt_preguntas(config_texto))
    contenido = _historial_a_gemini(historial)
    try:
        resp = modelo.generate_content(contenido)
        return (resp.text or "").strip()
    except Exception as err:  # noqa: BLE001
        if _es_429(err):
            raise LimiteAlcanzado from err
        raise


def generar_planificacion(api_key, model_name, materia, grado, historial,
                          previas="", config_texto=""):
    """Genera la planificación final con todo el contexto recopilado."""
    sistema = prompts.prompt_generacion(materia, grado, previas, config_texto)
    modelo = _modelo(api_key, model_name, sistema)

    resumen = _resumen_contexto(materia, grado, historial)
    try:
        resp = modelo.generate_content(resumen)
        return (resp.text or "").strip()
    except Exception as err:  # noqa: BLE001
        if _es_429(err):
            raise LimiteAlcanzado from err
        raise


def _historial_a_gemini(historial):
    """Convierte el historial interno al formato de la API de Gemini."""
    out = []
    for msg in historial:
        role = "user" if msg["role"] == "user" else "model"
        out.append({"role": role, "parts": [msg["content"]]})
    # Si el último turno fue del asistente (o no hay nada), pedimos arrancar.
    if not out or out[-1]["role"] == "model":
        out.append({"role": "user", "parts": ["Empecemos."]})
    return out


def _resumen_contexto(materia, grado, historial):
    lineas = [f"Materia: {materia}", f"Grado: {grado}", "", "Contexto recopilado:"]
    for msg in historial:
        quien = "Docente" if msg["role"] == "user" else "Asistente"
        lineas.append(f"- {quien}: {msg['content']}")
    lineas.append("")
    lineas.append("Generá ahora la planificación completa.")
    return "\n".join(lineas)
