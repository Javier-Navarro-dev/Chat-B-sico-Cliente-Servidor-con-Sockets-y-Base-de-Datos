"""
Cliente de chat básico. Se conecta al servidor en localhost:5000,
envía múltiples mensajes hasta que el usuario escribe 'exito' o 'salir',
y muestra la respuesta del servidor para cada envío.
"""

import socket
import sys
import unicodedata

# ------------------------- CONFIGURACIÓN -------------------------
HOST = "127.0.0.1"
PORT = 5000
BUFFER = 1024


# ------------------------- UTILIDADES -------------------------
def normalizar(texto: str) -> str:
    """
    Saca tildes/diacríticos y pasa a minúsculas.
    Sirve para comparar comandos como 'exito', 'éxito', 'EXITO', 'salir', etc.
    """
    sin_tildes = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return sin_tildes.lower().strip()


# ------------------------- SOCKET -------------------------
def conectar(host: str, port: int) -> socket.socket:
    """Crea y conecta un socket TCP al servidor."""
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((host, port))
        print(f"[CLIENTE] Conectado a {host}:{port}")
        return cliente
    except ConnectionRefusedError:
        print("[ERROR] El servidor no está disponible. ¿Está corriendo?")
        sys.exit(1)
    except OSError as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)


def enviar_mensajes(cliente: socket.socket) -> None:
    """Bucle de envío de mensajes hasta que el usuario escriba 'exito' o 'salir'."""
    try:
        while True:
            mensaje = input("> ").strip()
            if not mensaje:
                continue

            # Normalizamos para comparar sin importar mayúsculas ni tildes
            comando = normalizar(mensaje)

            # Enviamos el mensaje al servidor
            cliente.sendall(mensaje.encode("utf-8"))

            # Si el usuario escribe 'exito' o 'salir', terminamos
            if comando in ("exito", "salir"):
                print("[CLIENTE] Cerrando sesión...")
                break

            # Esperamos la respuesta del servidor
            respuesta = cliente.recv(BUFFER).decode("utf-8")
            print(f"[SERVIDOR] {respuesta}")
    except KeyboardInterrupt:
        print("\n[CLIENTE] Interrumpido por el usuario.")
    except Exception as e:
        print(f"[ERROR] {e}")


# ------------------------- MAIN -------------------------
def main():
    cliente = conectar(HOST, PORT)
    try:
        print("Escribí tus mensajes (escribí 'exito' o 'salir' para terminar):")
        enviar_mensajes(cliente)
    finally:
        cliente.close()
        print("[CLIENTE] Conexión cerrada.")


if __name__ == "__main__":
    main()