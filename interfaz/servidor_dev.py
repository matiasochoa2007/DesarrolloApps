"""Servidor local para ver y probar la interfaz en un navegador.

Uso (desde la raíz del repositorio):
    py -m interfaz.servidor_dev            → http://127.0.0.1:8765

Sirve los archivos de interfaz/web y atiende POST /api/<método> llamando a
ApiOrthoimagen, igual que lo hace la ventana de escritorio. Solo escucha en
127.0.0.1 (no es accesible desde otras computadoras).
"""

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from config import settings
from interfaz.api import ApiOrthoimagen
from modules.data_access import BaseDatos
from modules.demo_data import sembrar_datos_demo

CARPETA_WEB = Path(__file__).resolve().parent / "web"


def crear_servidor(api, puerto=8765):
    class Manejador(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(CARPETA_WEB), **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_POST(self):
            nombre = self.path.removeprefix("/api/")
            metodo = None if nombre.startswith("_") else getattr(api, nombre, None)
            if not callable(metodo):
                self.send_error(404)
                return
            largo = int(self.headers.get("Content-Length") or 0)
            argumentos = json.loads(self.rfile.read(largo) or b"[]")
            cuerpo = json.dumps(metodo(*argumentos)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *_):
            pass

    return ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    settings.RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
    bd = BaseDatos(settings.RUTA_BD)
    bd.inicializar()
    sembrar_datos_demo(bd)
    servidor = crear_servidor(ApiOrthoimagen(bd), puerto)
    print(f"Orthoimagen Dental en http://127.0.0.1:{puerto}  (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        bd.cerrar()


if __name__ == "__main__":
    main()
