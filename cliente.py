"""
Cliente de chat básico. Se conecta al servidor en localhost:5000,
envía múltiples mensajes hasta que el usuario escribe 'éxito' y
muestra la respuesta del servidor para cada envío.
"""

import socket
import sys

# ------------------------- CONFIGURACIÓN -------------------------
HOST = "127.0.0.1"
PORT = 5000
BUFFER = 1024


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
    """Bucle de envío de mensajes hasta que el usuario escriba 'éxito'."""
    try:
        while True:
            mensaje = input("> ").strip()
            if not mensaje:
                continue

            # Enviamos el mensaje al servidor
            cliente.sendall(mensaje.encode("utf-8"))

            # Si el usuario escribe 'éxito', terminamos
            if mensaje.lower() == "éxito":
                print("[CLIENTE] Cerrando sesión...")
                break

            # Esperamos la respuesta del servidor
            respuesta = cliente.recv(BUFFER).decode("utf-8")
            print(f"[SERVIDOR] {respuesta}")
    except KeyboardInterrupt:
        print("\n[CLIENTE] Interrumpido por el usuario.")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    cliente = conectar(HOST, PORT)
    try:
        print("Escribí tus mensajes (escribí 'éxito' para salir):")
        enviar_mensajes(cliente)
    finally:
        cliente.close()
        print("[CLIENTE] Conexión cerrada.")


if __name__ == "__main__":
    main()