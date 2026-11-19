"""Orthoimagen Dental - aplicación de escritorio.

Ejecutar desde la raíz del repositorio:
    py -m pip install -r requirements.txt     (solo la primera vez)
    py app_escritorio.py

Abre una ventana nativa de Windows (pywebview + Microsoft Edge WebView2) con
la interfaz de interfaz/web. La interfaz no contiene reglas de negocio:
llama a interfaz/api.py, que usa los módulos M1 a M8.
"""

import sys
from pathlib import Path

from config import settings
from interfaz.api import ApiOrthoimagen
from modules.data_access import BaseDatos, ErrorBaseDatos
from modules.demo_data import sembrar_datos_demo

TITULO = "Orthoimagen Dental"


def ruta_interfaz():
    """index.html junto al código o, dentro del .exe, en sys._MEIPASS."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "interfaz" / "web" / "index.html"


def mostrar_error(mensaje):
    """Cuadro de error nativo, sin depender de la interfaz web."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, mensaje, TITULO, 0x10)
    except (ImportError, AttributeError, OSError):
        print(mensaje, file=sys.stderr)


def main():
    try:
        import webview
    except ImportError:
        mostrar_error("Falta la biblioteca pywebview. Instálela con:\n"
                      "py -m pip install -r requirements.txt")
        return 1
    try:
        settings.RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
        bd = BaseDatos(settings.RUTA_BD)
        bd.inicializar()
        sembrar_datos_demo(bd)
    except (ErrorBaseDatos, OSError) as error:
        mostrar_error(getattr(error, "mensaje", str(error)))
        return 1

    api = ApiOrthoimagen(bd, modo_demo=settings.MODO_DEMO)
    webview.create_window(
        TITULO, str(ruta_interfaz()), js_api=api,
        width=1380, height=880, min_size=(1100, 700),
        background_color="#072d28", text_select=True,
    )
    try:
        webview.start(gui="edgechromium", private_mode=True)
    except Exception as error:  # WebView2 ausente o dañado
        mostrar_error("No se pudo abrir la ventana de la aplicación.\n"
                      "Instale Microsoft Edge WebView2 Runtime y vuelva a intentarlo.\n\n"
                      f"Detalle: {error}")
        return 1
    finally:
        bd.cerrar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
