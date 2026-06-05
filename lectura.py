"""Extrae texto de archivos subidos (PDF, Word o texto plano)."""

import io

from docx import Document
from pypdf import PdfReader


def extraer_texto(archivo) -> str:
    """Recibe un UploadedFile de Streamlit y devuelve su texto."""
    nombre = (archivo.name or "").lower()
    datos = archivo.getvalue()

    if nombre.endswith(".pdf"):
        return _de_pdf(datos)
    if nombre.endswith(".docx"):
        return _de_docx(datos)
    if nombre.endswith((".txt", ".md")):
        return datos.decode("utf-8", errors="ignore")
    # Intento por defecto: tratar como texto.
    return datos.decode("utf-8", errors="ignore")


def _de_pdf(datos: bytes) -> str:
    lector = PdfReader(io.BytesIO(datos))
    partes = [pagina.extract_text() or "" for pagina in lector.pages]
    return "\n".join(partes).strip()


def _de_docx(datos: bytes) -> str:
    doc = Document(io.BytesIO(datos))
    return "\n".join(p.text for p in doc.paragraphs).strip()
