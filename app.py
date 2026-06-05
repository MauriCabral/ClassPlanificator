"""Planificador de Clases para docentes de primaria (Argentina)."""

import streamlit as st

import ai
import auth
import db
import exportar
import lectura
import prompts

# ----------------------------------------------------------------------------
# Configuración general (debe ir primero)
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Planificador de clases",
    page_icon="📚",
    layout="centered",
)

GRADOS = ["1° grado", "2° grado", "3° grado", "4° grado", "5° grado", "6° grado"]
ESTILOS = [
    "Actividades lúdicas (juegos)", "Trabajo en grupos",
    "Material concreto / manipulativo", "Uso de tecnología",
    "Ejemplos de la vida cotidiana", "Mucha ejercitación escrita", "Arte y creatividad",
]

# ----------------------------------------------------------------------------
# Secretos — cargados antes del login para poder mostrar error de config
# ----------------------------------------------------------------------------
def _secreto(clave, defecto=""):
    try:
        return st.secrets.get(clave, defecto)
    except Exception:  # noqa: BLE001
        return defecto


API_KEY = _secreto("GEMINI_API_KEY")
MODELO  = _secreto("GEMINI_MODEL", "gemini-2.5-flash")
SUPA_URL = _secreto("SUPABASE_URL")
SUPA_KEY = _secreto("SUPABASE_KEY")

if not API_KEY:
    st.error(
        "Falta configurar la clave de Gemini. Pedile a quien instaló la app "
        "que complete `GEMINI_API_KEY` en la configuración."
    )
    st.stop()

# Login — antes de inyectar CSS principal para que la pantalla de login
# use su propio estilo definido en auth.py
auth.login_requerido()

# ----------------------------------------------------------------------------
# CSS principal (solo se ejecuta si el usuario está autenticado)
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Nunito:wght@300;400;500;600;700&display=swap');

:root {
  --bg:          #FDF8F6;
  --surface:     #FFFFFF;
  --rose:        #D4849A;
  --rose-deep:   #B86B82;
  --rose-pale:   #FAF0F3;
  --rose-light:  #F2D9E0;
  --mauve:       #8B6E7F;
  --mauve-deep:  #6E5465;
  --sidebar-bg:  #F8F1F4;
  --text:        #2D1F26;
  --text-2:      #7A5568;
  --muted:       #B09AA8;
  --border:      #EAD8E0;
  --r:           10px;
  --sh-sm:       0 1px 4px rgba(45,31,38,0.07);
  --sh-md:       0 4px 16px rgba(45,31,38,0.10);
}

/* ═══ BASE ═══ */
.stApp { background: var(--bg) !important; font-family: 'Nunito', sans-serif !important; }
#MainMenu, footer, [data-testid="stDeployButton"], [data-testid="stHeader"] { visibility: hidden !important; }
.block-container { max-width: 780px !important; padding-top: 2rem !important; padding-bottom: 4rem !important; }

/* ═══ TIPOGRAFÍA ═══ */
h1 { font-family: 'Cormorant Garamond', serif !important; font-size: 2.6rem !important; font-weight: 600 !important; color: var(--text) !important; letter-spacing: -0.3px !important; line-height: 1.1 !important; }
h2, h3 { font-family: 'Cormorant Garamond', serif !important; color: var(--rose-deep) !important; }
p { color: var(--text) !important; line-height: 1.7 !important; }

/* ═══ SIDEBAR ═══ */
[data-testid="stSidebar"] {
  background: var(--sidebar-bg) !important;
  border-right: 1.5px solid var(--border) !important;
  box-shadow: 2px 0 14px rgba(45,31,38,0.06) !important;
}
[data-testid="stSidebarContent"] { padding: 1.5rem 1.3rem !important; }

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { font-family: 'Cormorant Garamond', serif !important; color: var(--rose-deep) !important; font-size: 1.3rem !important; }
[data-testid="stSidebar"] p { color: var(--text) !important; }
[data-testid="stSidebar"] label {
  color: var(--text-2) !important; font-weight: 700 !important;
  font-size: 0.72rem !important; letter-spacing: 0.6px !important; text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stCaption p { color: var(--muted) !important; font-size: 0.8rem !important; }

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
  background: var(--surface) !important; border: 1.5px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--r) !important;
  font-family: 'Nunito', sans-serif !important; font-size: 0.88rem !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder { color: var(--muted) !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: var(--surface) !important; border: 1.5px solid var(--border) !important;
  border-radius: var(--r) !important; color: var(--text) !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
  background: var(--rose-light) !important; color: var(--rose-deep) !important;
}
[data-testid="stSidebar"] .stButton button {
  background: var(--surface) !important; color: var(--text-2) !important;
  border: 1.5px solid var(--border) !important; font-size: 0.83rem !important;
  font-weight: 600 !important; border-radius: 8px !important; box-shadow: var(--sh-sm) !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: var(--rose) !important; color: white !important;
  border-color: var(--rose) !important; transform: none !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: 0.8rem 0 !important; }

/* ═══ BOTONES ═══ */
.stButton button {
  font-family: 'Nunito', sans-serif !important;
  border-radius: 8px !important; padding: 0.5rem 1.4rem !important;
  font-weight: 600 !important; font-size: 0.9rem !important;
  transition: all 0.15s ease !important;
  border: 1.5px solid var(--border) !important;
  background: var(--surface) !important; color: var(--text) !important;
  box-shadow: var(--sh-sm) !important;
}
.stButton button:hover {
  border-color: var(--rose) !important; color: var(--rose-deep) !important;
  background: var(--rose-pale) !important; transform: none !important;
}
[data-testid="baseButton-primary"] {
  background: var(--rose) !important; color: white !important;
  border-color: var(--rose) !important; font-weight: 700 !important;
  box-shadow: 0 3px 12px rgba(212,132,154,0.35) !important;
}
[data-testid="baseButton-primary"]:hover {
  background: var(--rose-deep) !important; border-color: var(--rose-deep) !important; color: white !important;
}
[data-testid="stDownloadButton"] button {
  background: var(--mauve) !important; color: white !important;
  border-color: var(--mauve) !important; font-weight: 700 !important;
  box-shadow: 0 3px 12px rgba(139,110,127,0.30) !important;
}
[data-testid="stDownloadButton"] button:hover {
  background: var(--mauve-deep) !important; border-color: var(--mauve-deep) !important; color: white !important;
}

/* ═══ INPUTS ═══ */
.stTextInput input, .stTextArea textarea {
  font-family: 'Nunito', sans-serif !important;
  border: 1.5px solid var(--border) !important; border-radius: var(--r) !important;
  background: var(--surface) !important; color: var(--text) !important;
  font-size: 0.93rem !important; box-shadow: var(--sh-sm) !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--rose) !important; box-shadow: 0 0 0 3px rgba(212,132,154,0.12) !important;
}
.stTextInput label, .stTextArea label,
.stSelectbox label, .stFileUploader label, .stMultiSelect label {
  color: var(--text-2) !important; font-weight: 700 !important;
  font-size: 0.78rem !important; letter-spacing: 0.5px !important; text-transform: uppercase !important;
}
[data-testid="stSelectbox"] > div > div {
  border: 1.5px solid var(--border) !important; border-radius: var(--r) !important;
  background: var(--surface) !important; color: var(--text) !important;
}

/* ═══ FORMULARIO ═══ */
[data-testid="stForm"] {
  border: 1.5px solid var(--border) !important; border-radius: 16px !important;
  padding: 1.5rem 1.6rem !important; background: var(--surface) !important;
  box-shadow: var(--sh-md) !important;
}

/* ═══ CHAT ═══ */
[data-testid="stChatMessage"] {
  border-radius: 12px !important; padding: 1rem 1.3rem !important;
  margin-bottom: 0.6rem !important; border: 1px solid var(--border) !important;
}
[data-testid="stChatMessage"]:has([data-testid*="User"]) { background: var(--rose-pale) !important; border-color: var(--rose-light) !important; }
[data-testid="stChatMessage"]:has([data-testid*="Assistant"]) { background: var(--surface) !important; box-shadow: var(--sh-sm) !important; }
[data-testid="stChatInput"] textarea {
  border: 1.5px solid var(--border) !important; border-radius: var(--r) !important;
  background: var(--surface) !important; font-family: 'Nunito', sans-serif !important; color: var(--text) !important;
}
[data-testid="stChatInput"] { border: none !important; background: transparent !important; }

/* ═══ ALERTAS ═══ */
[data-testid="stAlert"] {
  border-radius: var(--r) !important; border: none !important;
  font-family: 'Nunito', sans-serif !important; font-size: 0.9rem !important;
}

/* ═══ MISC ═══ */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }
.stCaption, .stCaption p { color: var(--muted) !important; font-size: 0.82rem !important; }
[data-testid="stSpinner"] > div { border-top-color: var(--rose) !important; }
[data-testid="stFileUploader"] {
  border: 2px dashed var(--rose-light) !important; border-radius: 12px !important;
  background: var(--rose-pale) !important;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Estado de sesión
# ----------------------------------------------------------------------------
if "fase" not in st.session_state:
    st.session_state.fase = "inicio"
    st.session_state.historial = []
    st.session_state.previas = ""
    st.session_state.resultado = ""
    st.session_state.materia = ""
    st.session_state.grado = GRADOS[0]
    st.session_state.objetivo = ""
    st.session_state.config = db.cargar_config(SUPA_URL, SUPA_KEY)


def reiniciar():
    for clave in ("fase", "historial", "previas", "resultado", "objetivo"):
        st.session_state.pop(clave, None)
    st.rerun()


def config_texto():
    return prompts.formato_config(st.session_state.config)


# ----------------------------------------------------------------------------
# Encabezado principal
# ----------------------------------------------------------------------------
def _encabezado(subtitulo="Contame qué querés enseñar y armo la planificación por vos."):
    st.markdown(f"""
    <div style="margin-bottom:1.8rem; padding-bottom:1.4rem; border-bottom:1.5px solid #EAD8E0;">
      <p style="font-family:'Nunito',sans-serif; font-size:0.72rem; font-weight:700;
                color:#B09AA8; letter-spacing:1px; text-transform:uppercase; margin:0 0 6px;">
        Planificador · Primaria Argentina
      </p>
      <h1 style="margin:0; font-family:'Cormorant Garamond',serif; font-size:2.6rem;
                 font-weight:600; color:#2D1F26; line-height:1.05; letter-spacing:-0.3px;">
        Planificador de clases
      </h1>
      <p style="margin:8px 0 0; color:#7A5568; font-size:0.93rem;
                font-family:'Nunito',sans-serif; line-height:1.5;">
        {subtitulo}
      </p>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Indicador de fase
# ----------------------------------------------------------------------------
def _fase_badge(fase_actual):
    fases  = [("✏️", "Datos"), ("💬", "Preguntas"), ("⚙️", "Generando"), ("✅", "Resultado")]
    claves = ["inicio", "preguntas", "generar", "resultado"]
    idx = claves.index(fase_actual) if fase_actual in claves else 0

    partes = []
    for i, (icono, nombre) in enumerate(fases):
        if i < idx:
            s = "background:#F2D9E0; color:#B86B82; border:1.5px solid #EAD8E0;"
        elif i == idx:
            s = "background:#D4849A; color:white; border:1.5px solid #D4849A;"
        else:
            s = "background:transparent; color:#B09AA8; border:1.5px solid #EAD8E0;"
        partes.append(
            f'<span style="padding:5px 13px; border-radius:6px; font-size:0.75rem;'
            f'font-weight:600; letter-spacing:0.2px; font-family:\'Nunito\',sans-serif; {s}">'
            f'{icono} {nombre}</span>'
        )
    st.markdown(
        f'<div style="display:flex; gap:8px; margin-bottom:1.5rem; flex-wrap:wrap;">{"".join(partes)}</div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Panel lateral — Configuración del grupo
# ----------------------------------------------------------------------------
def panel_configuracion():
    cfg = st.session_state.config or {}
    with st.sidebar:
        nombre_usuario = st.session_state.get("usuario_nombre", "")
        st.markdown(f"""
        <div style="margin-bottom:1.1rem; padding-bottom:0.9rem; border-bottom:1.5px solid #EAD8E0;">
          <p style="font-family:'Cormorant Garamond',serif; font-size:1.35rem;
                    font-weight:600; color:#B86B82; margin:0 0 3px; letter-spacing:-0.2px;">Configuración</p>
          {"<p style='font-size:0.82rem; color:#7A5568; margin:0; font-family:Nunito,sans-serif;'>👩‍🏫 " + nombre_usuario + "</p>" if nombre_usuario else ""}
        </div>
        """, unsafe_allow_html=True)

        st.caption("Datos de tu grupo que la IA tendrá siempre en cuenta.")

        if st.button("Cerrar sesión", use_container_width=True):
            auth.cerrar_sesion()

        st.divider()

        with st.form("config_form"):
            edad     = st.text_input("Edad promedio", value=cfg.get("edad", ""), placeholder="Ej: 9 años")
            cantidad = st.text_input("Cantidad de alumnos",   value=cfg.get("cantidad", ""), placeholder="Ej: 25")
            descripcion = st.text_area(
                "Descripción del grupo",
                value=cfg.get("descripcion", ""),
                placeholder="Grupo diverso, algunos con dificultades de lectura...",
                height=90,
            )
            recursos = st.text_area(
                "Recursos disponibles",
                value=cfg.get("recursos", ""),
                placeholder="Pizarrón, manuales, una notebook...",
                height=65,
            )
            preferencias = st.multiselect(
                "Estilo de enseñanza", ESTILOS,
                default=[p for p in cfg.get("preferencias", []) if p in ESTILOS],
            )
            if st.form_submit_button("Guardar", use_container_width=True):
                nueva = {
                    "edad": edad.strip(), "cantidad": cantidad.strip(),
                    "descripcion": descripcion.strip(), "recursos": recursos.strip(),
                    "preferencias": preferencias,
                }
                st.session_state.config = nueva
                guardado = db.guardar_config(SUPA_URL, SUPA_KEY, nueva)
                if guardado:
                    st.success("Configuración guardada.")
                else:
                    st.info("Guardada para esta sesión.")

        st.divider()

        st.markdown("""
        <p style="font-family:'Nunito',sans-serif; font-size:0.72rem; font-weight:700;
                  color:#7A5568; letter-spacing:0.6px; text-transform:uppercase; margin:0 0 10px;">
          Mis materias
        </p>""", unsafe_allow_html=True)

        materias_cfg = st.session_state.config.get("materias", []) if st.session_state.config else []

        for i, mat in enumerate(materias_cfg):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<p style="margin:2px 0; font-size:0.9rem; color:#2D1F26; '
                    f'font-family:Nunito,sans-serif; padding:4px 0;">{mat}</p>',
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("✕", key=f"rm_mat_{i}", help="Quitar"):
                    materias_cfg.pop(i)
                    if not st.session_state.config:
                        st.session_state.config = {}
                    st.session_state.config["materias"] = materias_cfg
                    if st.session_state.materia == mat:
                        st.session_state.materia = materias_cfg[0] if materias_cfg else ""
                    db.guardar_config(SUPA_URL, SUPA_KEY, st.session_state.config)
                    st.rerun()

        if not materias_cfg:
            st.caption("Todavía no agregaste ninguna materia.")

        inp_c, btn_c = st.columns([3, 1])
        with inp_c:
            nueva_mat = st.text_input(
                "", placeholder="Ej: Matemática", label_visibility="collapsed",
                key="inp_nueva_materia",
            )
        with btn_c:
            if st.button("＋", key="btn_add_materia", use_container_width=True, help="Agregar materia"):
                nm = nueva_mat.strip()
                if nm and nm not in materias_cfg:
                    materias_cfg.append(nm)
                    if not st.session_state.config:
                        st.session_state.config = {}
                    st.session_state.config["materias"] = materias_cfg
                    db.guardar_config(SUPA_URL, SUPA_KEY, st.session_state.config)
                    st.rerun()


panel_configuracion()


# ----------------------------------------------------------------------------
# FASE 1 — Datos iniciales
# ----------------------------------------------------------------------------
if st.session_state.fase == "inicio":
    _encabezado()

    materias_disp = (st.session_state.config or {}).get("materias", [])

    col1, col2 = st.columns(2)
    with col1:
        if materias_disp:
            idx_mat = materias_disp.index(st.session_state.materia) if st.session_state.materia in materias_disp else 0
            st.session_state.materia = st.selectbox("Materia", materias_disp, index=idx_mat)
        else:
            st.info("← Agregá materias en el panel de configuración.")
            st.session_state.materia = ""
    with col2:
        st.session_state.grado = st.selectbox(
            "Grado", GRADOS, index=GRADOS.index(st.session_state.grado))

    st.session_state.objetivo = st.text_area(
        "¿Qué querés enseñar? ¿Cuál es el objetivo?",
        value=st.session_state.objetivo,
        height=130,
        placeholder="Ej: Quiero introducir las fracciones en 4° grado, que entiendan "
                    "la idea de parte-todo usando ejemplos de la vida diaria...",
    )

    archivo = st.file_uploader(
        "Subí tu última planificación de esta materia (opcional) — la IA copiará tu estilo.",
        type=["pdf", "docx", "txt", "md"],
    )

    if st.button("Comenzar", type="primary", use_container_width=True):
        if not st.session_state.materia:
            st.warning("Primero agregá al menos una materia en el panel de configuración.")
            st.stop()
        objetivo_limpio = st.session_state.objetivo.strip()
        if not objetivo_limpio:
            st.warning("Contame al menos brevemente qué querés enseñar.")
            st.stop()
        if len(objetivo_limpio) < 10:
            st.warning("Necesito un poco más de detalle para poder ayudarte bien.")
            st.stop()
        if len(objetivo_limpio) > 2000:
            st.warning("El objetivo es muy largo. Resumilo en unas pocas oraciones.")
            st.stop()

        texto_subido = ""
        if archivo is not None:
            try:
                texto_subido = lectura.extraer_texto(archivo)
            except Exception:  # noqa: BLE001
                st.warning("No pude leer el archivo, sigo sin él.")
        if texto_subido:
            db.guardar_planificacion(SUPA_URL, SUPA_KEY, st.session_state.materia,
                                     st.session_state.grado, st.session_state.objetivo,
                                     texto_subido, "subida")

        memoria = db.recuperar_previas(SUPA_URL, SUPA_KEY, st.session_state.materia)
        st.session_state.previas = "\n\n=====\n\n".join(
            t for t in (texto_subido, memoria) if t
        )

        primer_mensaje = (
            f"Quiero planificar {st.session_state.materia} para "
            f"{st.session_state.grado}. {st.session_state.objetivo.strip()}"
        )
        st.session_state.historial = [{"role": "user", "content": primer_mensaje}]

        with st.spinner("Pensando la primera pregunta..."):
            try:
                pregunta = ai.siguiente_pregunta(
                    API_KEY, MODELO, st.session_state.historial, config_texto())
            except ai.LimiteAlcanzado:
                st.warning("Hay mucho uso en este momento. Probá de nuevo en un minutito.")
                st.stop()

        if pregunta == "[LISTO]":
            st.session_state.fase = "generar"
        else:
            st.session_state.historial.append({"role": "assistant", "content": pregunta})
            st.session_state.fase = "preguntas"
        st.rerun()


# ----------------------------------------------------------------------------
# FASE 2 — Conversación
# ----------------------------------------------------------------------------
elif st.session_state.fase == "preguntas":
    _encabezado(f"{st.session_state.materia} · {st.session_state.grado}")
    _fase_badge("preguntas")

    for msg in st.session_state.historial[1:]:
        avatar = "👩‍🏫" if msg["role"] == "user" else "🤖"
        with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar=avatar):
            st.write(msg["content"])

    if st.button("Ya te conté suficiente — generá la planificación", use_container_width=True):
        st.session_state.fase = "generar"
        st.rerun()

    respuesta = st.chat_input("Escribí tu respuesta...")
    if respuesta:
        st.session_state.historial.append({"role": "user", "content": respuesta})
        with st.spinner("Pensando..."):
            try:
                pregunta = ai.siguiente_pregunta(
                    API_KEY, MODELO, st.session_state.historial, config_texto())
            except ai.LimiteAlcanzado:
                st.warning("Hay mucho uso en este momento. Probá de nuevo en un minutito.")
                st.stop()
        if pregunta == "[LISTO]":
            st.session_state.fase = "generar"
        else:
            st.session_state.historial.append({"role": "assistant", "content": pregunta})
        st.rerun()


# ----------------------------------------------------------------------------
# FASE 3 — Generación
# ----------------------------------------------------------------------------
elif st.session_state.fase == "generar":
    _encabezado(f"{st.session_state.materia} · {st.session_state.grado}")
    _fase_badge("generar")

    with st.spinner("Armando tu planificación... puede tardar unos segundos."):
        try:
            resultado = ai.generar_planificacion(
                API_KEY, MODELO, st.session_state.materia, st.session_state.grado,
                st.session_state.historial, st.session_state.previas, config_texto(),
            )
        except ai.LimiteAlcanzado:
            st.warning("Hay mucho uso en este momento. Probá de nuevo en un minutito.")
            if st.button("Reintentar"):
                st.rerun()
            st.stop()

    st.session_state.resultado = resultado
    db.guardar_planificacion(SUPA_URL, SUPA_KEY, st.session_state.materia,
                             st.session_state.grado, st.session_state.objetivo,
                             resultado, "generada")
    st.session_state.fase = "resultado"
    st.rerun()


# ----------------------------------------------------------------------------
# FASE 4 — Resultado
# ----------------------------------------------------------------------------
elif st.session_state.fase == "resultado":
    _encabezado(f"{st.session_state.materia} · {st.session_state.grado}")
    _fase_badge("resultado")

    docx_bytes = exportar.planificacion_a_docx(
        st.session_state.materia, st.session_state.grado,
        st.session_state.resultado, st.session_state.objetivo,
        st.session_state.config,
    )
    nombre = f"Planificacion_{st.session_state.materia}_{st.session_state.grado}".replace(" ", "_")

    st.markdown("""
    <div style="background:#FAF0F3; border-radius:14px; padding:1rem 1.4rem;
                margin-bottom:1.2rem; display:flex; align-items:center; gap:12px;
                border:1.5px solid #F2D9E0;">
      <span style="font-size:1.5rem;">✨</span>
      <div>
        <p style="margin:0; font-weight:700; color:#2D1F26; font-size:0.95rem;
                  font-family:'Nunito',sans-serif;">
          ¡Tu planificación está lista!</p>
        <p style="margin:0; color:#7A5568; font-size:0.82rem; font-family:'Nunito',sans-serif;">
          Revisala abajo y descargala en Word cuando quieras.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️  Descargar en Word", data=docx_bytes, file_name=f"{nombre}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary", use_container_width=True,
        )
    with col2:
        if st.button("✦  Nueva planificación", use_container_width=True):
            reiniciar()

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white; border:1.5px solid #EAD8E0; border-radius:20px;
                padding:2.5rem 2.8rem; box-shadow:0 4px 20px rgba(45,31,38,0.07);">
    """, unsafe_allow_html=True)
    st.markdown(st.session_state.resultado)
    st.markdown("</div>", unsafe_allow_html=True)
