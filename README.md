# 📚 Planificador de Clases — Primaria (Argentina)

App web simple para que una docente de primaria genere planificaciones de clase.
La IA **conversa** con ella para entender bien qué necesita y después arma una
planificación completa, **descargable en Word**. Puede **recordar su estilo** a
partir de planificaciones anteriores.

Pensada para funcionar **sin costo mensual** (Gemini Flash free tier + Streamlit
Community Cloud + Supabase free).

---

## ¿Cómo funciona para la docente?

1. (Una sola vez) Abre **⚙️ Configuración** en el panel lateral y carga datos de
   su grupo: edad de los alumnos, cantidad, descripción a tener en cuenta,
   recursos y estilo de enseñanza. Quedan guardados y la IA los usa siempre.
2. Elige **materia** y **grado**.
3. Escribe en sus palabras qué quiere enseñar y cuál es el objetivo.
4. (Opcional) Sube su última planificación para que copie su estilo.
5. La IA le hace **algunas preguntas** para entender mejor el contexto.
6. Genera la planificación y la **descarga en Word** lista para imprimir.

Sin login ni contraseñas: entra por un link y listo.

---

## Estructura del proyecto

```
planificador-clases-primaria/
├── app.py             # App Streamlit (UI de una sola pantalla)
├── ai.py              # Llamadas a Gemini (preguntas + generación, manejo de 429)
├── prompts.py         # Persona "maestra de primaria AR" y prompts
├── db.py              # Memoria con Supabase (opcional)
├── exportar.py        # Generación del .docx
├── lectura.py         # Extrae texto de PDF/Word subidos
├── requirements.txt
└── .streamlit/
    ├── config.toml         # Tema minimalista
    └── secrets.toml.example # Plantilla de claves
```

---

## Setup local

1. **Crear entorno e instalar dependencias**

   ```bash
   cd planificador-clases-primaria
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Clave de Gemini (gratis)**

   - Entrá a https://aistudio.google.com/apikey y creá una API key.
   - ⚠️ **Importante:** usá un proyecto de Google **SIN tarjeta de crédito
     asociada**. Así nunca te pueden cobrar: si se llega al límite gratuito, la
     API simplemente espera (error 429), no genera costo.

3. **Configurar secretos**

   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   Editá `secrets.toml` y pegá tu `GEMINI_API_KEY`. (Supabase es opcional.)

4. **Correr**

   ```bash
   streamlit run app.py
   ```

---

## Memoria del estilo (opcional — Supabase)

Si querés que la app **recuerde** las planificaciones previas de la docente:

1. Creá un proyecto gratis en https://supabase.com
2. En el SQL Editor, ejecutá:

   ```sql
   create table planificaciones (
       id uuid primary key default gen_random_uuid(),
       materia text not null,
       grado text not null,
       objetivo text,
       contenido text not null,
       origen text default 'generada',
       created_at timestamptz default now()
   );

   -- Configuración del grupo (una sola fila)
   create table configuracion (
       id int primary key default 1,
       data jsonb,
       updated_at timestamptz default now()
   );
   ```

3. Copiá la **Project URL** y la **anon/service key** a `secrets.toml`
   (`SUPABASE_URL` y `SUPABASE_KEY`).

Si dejás esos campos vacíos, la app funciona igual, pero sin memoria persistente.

---

## Deploy gratis (Streamlit Community Cloud)

1. Subí el proyecto a un repositorio de GitHub.
2. Entrá a https://share.streamlit.io y conectá el repo.
3. En **Settings → Secrets** pegá el contenido de tu `secrets.toml`.
4. Deploy. Te queda un link público (ej. `planificador-mama.streamlit.app`)
   que podés guardar como ícono en el celular/escritorio.

> La app gratuita "se duerme" si no se usa y tarda unos segundos en despertar la
> primera vez. No tiene costo.

---

## Costos y límites

- **Gemini Flash free tier:** ~10 pedidos/min y ~1.500/día. De sobra para una
  persona. Si se supera, la app muestra *"probá de nuevo en un minutito"* y no
  se cobra nada (mientras el proyecto no tenga facturación activada).
- **Streamlit Community Cloud:** gratis.
- **Supabase:** plan free (~500 MB), de sobra para texto.

> Los cupos de los free tiers cambian seguido; conviene confirmar los límites
> vigentes antes de cerrar la configuración.

---

## Cambiar el modelo

En `secrets.toml`, `GEMINI_MODEL` controla qué modelo se usa. Cualquier modelo
**Flash** entra en el free tier (por ejemplo `gemini-2.5-flash`). Ajustalo según
los modelos disponibles al momento de desplegar.
