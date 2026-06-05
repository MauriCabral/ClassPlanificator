"""Utilidad para generar el hash bcrypt de una contraseña.

Uso:
    python crear_usuario.py

Te pide un nombre de usuario y contraseña, e imprime el bloque listo para
pegar en .streamlit/secrets.toml.

Nunca guardes contraseñas en texto plano — siempre usá este script.
"""

import getpass
import re
import sys

import bcrypt


def generar_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def validar_usuario(nombre: str) -> bool:
    return bool(re.match(r"^[a-z0-9_]{3,32}$", nombre))


def main():
    print("=== Crear usuario para el Planificador de clases ===\n")

    username = input("Nombre de usuario (solo letras minúsculas, números y _): ").strip().lower()
    if not validar_usuario(username):
        print("ERROR: El nombre de usuario solo puede tener letras minúsculas, "
              "números y _ (mínimo 3 caracteres).")
        sys.exit(1)

    nombre_mostrar = input(f"Nombre para mostrar (ej: 'Maestra Ana') [{username}]: ").strip()
    if not nombre_mostrar:
        nombre_mostrar = username

    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
    if len(password) < 8:
        print("ERROR: La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    confirmacion = getpass.getpass("Repetí la contraseña: ")
    if password != confirmacion:
        print("ERROR: Las contraseñas no coinciden.")
        sys.exit(1)

    print("\nGenerando hash seguro... ", end="", flush=True)
    hash_resultado = generar_hash(password)
    print("listo.\n")

    print("Copiá este bloque en tu archivo .streamlit/secrets.toml:\n")
    print("─" * 50)
    print(f'[usuarios.{username}]')
    print(f'nombre = "{nombre_mostrar}"')
    print(f'password_hash = "{hash_resultado}"')
    print("─" * 50)
    print("\nNota: podés agregar más usuarios repitiendo el bloque con otro nombre.")


if __name__ == "__main__":
    main()
