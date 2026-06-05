"""Memoria persistente con Supabase (opcional).

Si no hay credenciales de Supabase configuradas, todas las funciones
degradan de forma segura: la app sigue funcionando, pero sin memoria.

Tabla esperada en Supabase (SQL en el README):

    create table planificaciones (
        id uuid primary key default gen_random_uuid(),
        materia text not null,
        grado text not null,
        objetivo text,
        contenido text not null,
        origen text default 'generada',
        created_at timestamptz default now()
    );
"""

from supabase import create_client


def _cliente(url, key):
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:  # noqa: BLE001
        return None


def memoria_activa(url, key) -> bool:
    return bool(url and key)


def guardar_planificacion(url, key, materia, grado, objetivo, contenido, origen):
    """Guarda una planificación (subida o generada). Devuelve True si se guardó."""
    cli = _cliente(url, key)
    if cli is None:
        return False
    try:
        cli.table("planificaciones").insert(
            {
                "materia": materia,
                "grado": str(grado),
                "objetivo": objetivo or "",
                "contenido": contenido,
                "origen": origen,
            }
        ).execute()
        return True
    except Exception:  # noqa: BLE001
        return False


def guardar_config(url, key, data: dict):
    """Guarda (upsert) la configuración del grupo. Devuelve True si se guardó."""
    cli = _cliente(url, key)
    if cli is None:
        return False
    try:
        cli.table("configuracion").upsert({"id": 1, "data": data}).execute()
        return True
    except Exception:  # noqa: BLE001
        return False


def cargar_config(url, key) -> dict:
    """Devuelve la configuración guardada, o {} si no hay."""
    cli = _cliente(url, key)
    if cli is None:
        return {}
    try:
        res = cli.table("configuracion").select("data").eq("id", 1).limit(1).execute()
        if res.data:
            return res.data[0].get("data") or {}
        return {}
    except Exception:  # noqa: BLE001
        return {}


def recuperar_previas(url, key, materia, limite=2):
    """Devuelve el texto de las últimas planificaciones de esa materia."""
    cli = _cliente(url, key)
    if cli is None:
        return ""
    try:
        res = (
            cli.table("planificaciones")
            .select("contenido")
            .eq("materia", materia)
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
        textos = [row["contenido"] for row in (res.data or []) if row.get("contenido")]
        return "\n\n=====\n\n".join(textos)
    except Exception:  # noqa: BLE001
        return ""
