"""
Servidor de chat básico con sockets TCP y persistencia en SQLite.
Escucha en localhost:5000, recibe mensajes de clientes, los guarda
en una base de datos y responde con una confirmación al cliente.
"""

import socket
import sqlite3
import datetime
import unicodedata

# ------------------------- CONFIGURACIÓN GLOBAL -------------------------
HOST = "127.0.0.1"      # localhost
PORT = 5000             # puerto de escucha
DB_PATH = "chat.db"     # ruta del archivo SQLite


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


# ------------------------- BASE DE DATOS -------------------------
def inicializar_db(db_path: str) -> sqlite3.Connection:
    """
    Crea (si no existe) la tabla 'mensajes' y devuelve la conexión.
    Maneja errores si la DB no es accesible.
    """
    try:
        # timeout para evitar bloqueos si otra conexión está escribiendo
        conexion = sqlite3.connect(db_path, timeout=10)
        cursor = conexion.cursor()
        # Tabla con los campos solicitados: id, contenido, fecha_envio, ip_cliente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contenido TEXT NOT NULL,
                fecha_envio TEXT NOT NULL,
                ip_cliente TEXT NOT NULL
            )
        """)
        conexion.commit()
        print(f"[DB] Base de datos lista en '{db_path}'")
        return conexion
    except sqlite3.Error as e:
        # Si la DB no es accesible, abortamos el arranque del servidor
        print(f"[ERROR DB] No se pudo inicializar la base de datos: {e}")
        raise


def guardar_mensaje(conexion: sqlite3.Connection, contenido: str, ip_cliente: str) -> str:
    """
    Guarda un mensaje en la DB y devuelve el timestamp usado.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO mensajes (contenido, fecha_envio, ip_cliente) VALUES (?, ?, ?)",
            (contenido, timestamp, ip_cliente)
        )
        conexion.commit()
        print(f"[DB] Guardado: '{contenido}' de {ip_cliente} a las {timestamp}")
    except sqlite3.Error as e:
        # Si falla el guardado, avisamos pero no rompemos la respuesta al cliente
        print(f"[ERROR DB] No se pudo guardar el mensaje: {e}")
    return timestamp


# ------------------------- SOCKET -------------------------
def inicializar_socket(host: str, port: int) -> socket.socket:
    """
    Configura el socket TCP/IP del servidor.
    Maneja errores como 'puerto ocupado' (OSError).
    """
    try:
        # AF_INET = IPv4 ; SOCK_STREAM = TCP
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # SO_REUSEADDR permite reutilizar el puerto al reiniciar el servidor
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Asociamos el socket a host:puerto
        servidor.bind((host, port))

        # Empezamos a escuchar (máximo 5 conexiones en cola)
        servidor.listen(5)
        print(f"[SOCKET] Servidor escuchando en {host}:{port}")
        return servidor
    except OSError as e:
        # Aquí caen típicamente: puerto ocupado, permisos, dirección inválida
        print(f"[ERROR SOCKET] No se pudo iniciar el servidor: {e}")
        raise


def aceptar_conexiones(servidor: socket.socket, db: sqlite3.Connection) -> None:
    """
    Bucle principal: acepta clientes, recibe mensajes, los guarda en la DB
    y responde con 'Mensaje recibido: <timestamp>'.
    """
    print("[SOCKET] Esperando conexiones... (Ctrl+C para salir)")
    while True:
        try:
            # Aceptamos una conexión entrante
            cliente_socket, direccion = servidor.accept()
            ip_cliente = direccion[0]
            print(f"[SOCKET] Conexión entrante desde {ip_cliente}:{direccion[1]}")

            # Atendemos al cliente hasta que se desconecte
            with cliente_socket:
                while True:
                    # Recibimos hasta 1024 bytes
                    datos = cliente_socket.recv(1024)
                    if not datos:
                        # El cliente cerró la conexión
                        print(f"[SOCKET] Cliente {ip_cliente} desconectado.")
                        break

                    # Decodificamos el mensaje recibido
                    mensaje = datos.decode("utf-8").strip()
                    if not mensaje:
                        continue

                    # Normalizamos para aceptar 'exito', 'éxito', 'salir' (mayúsculas incluidas)
                    comando = normalizar(mensaje)

                    # Si el cliente manda 'exito' o 'salir', cerramos también desde el server
                    if comando in ("exito", "salir"):
                        print(f"[SOCKET] Cliente {ip_cliente} envió '{mensaje}'. Cerrando.")
                        break

                    # Persistimos el mensaje en la DB
                    timestamp = guardar_mensaje(db, mensaje, ip_cliente)

                    # Respondemos al cliente con la confirmación solicitada
                    respuesta = f"Mensaje recibido: {timestamp}"
                    cliente_socket.sendall(respuesta.encode("utf-8"))

        except KeyboardInterrupt:
            # Cierre limpio con Ctrl+C
            print("\n[SOCKET] Servidor detenido por el usuario.")
            break
        except ConnectionResetError:
            # El cliente cortó abruptamente
            print("[SOCKET] Cliente desconectado abruptamente.")
            continue
        except Exception as e:
            # Cualquier otro error a nivel de conexión
            print(f"[ERROR SOCKET] Error al manejar la conexión: {e}")
            continue


# ------------------------- MAIN -------------------------
def main():
    db = None
    servidor = None
    try:
        # 1) Inicializamos la base de datos
        db = inicializar_db(DB_PATH)

        # 2) Inicializamos el socket TCP/IP
        servidor = inicializar_socket(HOST, PORT)

        # 3) Aceptamos conexiones y procesamos mensajes
        aceptar_conexiones(servidor, db)

    except Exception as e:
        print(f"[FATAL] El servidor no pudo arrancar: {e}")
    finally:
        # Cierre ordenado de recursos
        if servidor:
            servidor.close()
            print("[SOCKET] Socket del servidor cerrado.")
        if db:
            db.close()
            print("[DB] Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    main()