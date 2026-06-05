"""Autenticación simple con usuario/contraseña hasheada con bcrypt.

Las credenciales van en secrets.toml bajo [usuarios.<nombre>]:
    nombre = "Maestra Ana"
    password_hash = "$2b$12$..."   # generado con crear_usuario.py

Si no hay usuarios configurados, la app pasa directo (modo desarrollo).
"""

import bcrypt
import streamlit as st

_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Nunito:wght@300;400;500;600;700&display=swap');

:root {
  --rose:      #D4849A;
  --rose-deep: #B86B82;
  --cream:     #FDF8F6;
  --text:      #2D1F26;
  --text-2:    #7A5568;
  --muted:     #B09AA8;
  --border:    #EAD8E0;
}

.stApp {
  background: linear-gradient(145deg, #2D0F1A 0%, #4A1E2E 55%, #1E0B12 100%) !important;
  font-family: 'Nunito', sans-serif !important;
}
#MainMenu, footer, [data-testid="stDeployButton"],
[data-testid="stHeader"] { visibility: hidden !important; }

.block-container {
  max-width: 430px !important;
  background: var(--cream) !important;
  border-radius: 24px !important;
  padding: 2.8rem 2.6rem 2.4rem !important;
  box-shadow: 0 28px 70px rgba(0,0,0,0.50), 0 0 0 1px rgba(212,132,154,0.12) !important;
  margin-top: 7vh !important;
  border-top: 3px solid var(--rose) !important;
}

h1 {
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 2rem !important; font-weight: 600 !important;
  color: var(--text) !important; text-align: center !important;
  letter-spacing: -0.3px !important; line-height: 1.2 !important;
  margin-bottom: 0 !important;
}

label {
  font-weight: 700 !important; font-size: 0.76rem !important;
  color: var(--text-2) !important; letter-spacing: 0.6px !important;
  text-transform: uppercase !important;
}

.stTextInput input {
  font-family: 'Nunito', sans-serif !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important; background: white !important;
  color: var(--text) !important; font-size: 0.95rem !important;
  box-shadow: 0 1px 3px rgba(45,31,38,0.05) !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput input:focus {
  border-color: var(--rose) !important;
  box-shadow: 0 0 0 3px rgba(212,132,154,0.12) !important;
}

[data-testid="baseButton-primary"],
[data-testid="baseButton-secondaryFormSubmit"] {
  font-family: 'Nunito', sans-serif !important;
  background: var(--rose) !important; color: white !important;
  border: none !important; border-radius: 8px !important;
  font-weight: 700 !important; font-size: 0.92rem !important;
  box-shadow: 0 4px 14px rgba(212,132,154,0.35) !important;
  transition: all 0.15s ease !important;
}
[data-testid="baseButton-primary"]:hover,
[data-testid="baseButton-secondaryFormSubmit"]:hover {
  background: var(--rose-deep) !important;
  box-shadow: 0 6px 18px rgba(212,132,154,0.42) !important;
}

[data-testid="stAlert"] {
  border-radius: 10px !important; border: none !important;
  font-family: 'Nunito', sans-serif !important; font-size: 0.88rem !important;
}
</style>
"""


def _credenciales() -> dict:
    """Carga los usuarios desde secrets. Devuelve {username_lower: {nombre, password_hash}}."""
    try:
        usuarios_raw = st.secrets.get("usuarios", {})
        result = {}
        for username, datos in usuarios_raw.items():
            result[username.lower()] = {
                "nombre": datos.get("nombre", username),
                "password_hash": datos.get("password_hash", ""),
            }
        return result
    except Exception:
        return {}


def _verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except Exception:
        return False


def login_requerido() -> bool:
    """Muestra la pantalla de login si no hay sesión activa.

    Retorna True si el usuario está autenticado.
    Llama a st.stop() si no lo está (la app no continúa).
    """
    if st.session_state.get("autenticado"):
        return True

    usuarios = _credenciales()
    if not usuarios:
        st.session_state["autenticado"] = True
        st.session_state["usuario_nombre"] = "Docente"
        return True

    _mostrar_login(usuarios)
    st.stop()
    return False


def cerrar_sesion():
    """Cierra la sesión y limpia el estado completo."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def _mostrar_login(usuarios: dict):
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
      <div style="display:inline-flex; align-items:center; justify-content:center;
                  width:60px; height:60px; background:#D4849A; border-radius:16px;
                  font-size:1.7rem; margin-bottom:1rem; box-shadow:0 8px 20px rgba(212,132,154,0.40);">
        📚
      </div>
      <h1 style="font-family:'Cormorant Garamond',serif; font-size:2rem; font-weight:600;
                 color:#2D1F26; margin:0 0 6px; line-height:1.2;">
        Planificador de clases
      </h1>
      <p style="color:#7A5568; font-size:0.88rem; margin:0; font-family:'Nunito',sans-serif;">
        Ingresá para continuar
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        usuario  = st.text_input("Usuario",    placeholder="tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

    if submitted:
        usuario_key = usuario.lower().strip()
        datos = usuarios.get(usuario_key)
        if datos and datos["password_hash"] and _verificar_password(password, datos["password_hash"]):
            st.session_state["autenticado"] = True
            st.session_state["usuario_nombre"] = datos["nombre"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown("""
    <p style="text-align:center; font-size:0.75rem; color:#B09AA8;
              font-family:'Nunito',sans-serif; margin-top:1.5rem;">
      ¿Problemas para ingresar? Contactá a quien configuró la app.
    </p>
    """, unsafe_allow_html=True)
