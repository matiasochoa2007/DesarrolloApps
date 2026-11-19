"""Orthoimagen Dental - aplicación de escritorio.

Ejecutar desde la raíz del repositorio:
    py app_escritorio.py

Interfaz gráfica con tkinter (biblioteca estándar). Igual que la consola,
no contiene reglas de negocio: captura datos, llama a los módulos M1 a M7 y
muestra sus mensajes en la barra de estado.
"""

import sys
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

from config import settings
from modules.agenda import agenda_dentista, filtrar_citas, mis_citas
from modules.appointments import (
    cancelar_cita,
    eliminar_cita,
    modificar_cita,
    registrar_cita,
)
from modules.auth_roles import (
    ROL_DENTISTA,
    ROL_PACIENTE,
    ROL_RECEPCIONISTA,
    iniciar_sesion,
)
from modules.availability import consultar_disponibilidad, horarios_del_dia
from modules.data_access import BaseDatos, ErrorBaseDatos
from modules.demo_data import USUARIOS_DEMO, sembrar_datos_demo
from modules.service_catalog import consultar_catalogo

TITULO = "Orthoimagen Dental"
COLOR_PRIMARIO = "#0f766e"
COLOR_PRIMARIO_OSCURO = "#115e59"
COLOR_FONDO = "#f1f5f5"
COLOR_TARJETA = "#ffffff"
COLOR_TEXTO_SUAVE = "#4b5563"
COLOR_ERROR = "#b91c1c"
COLOR_AVISO = "#a16207"
COLOR_EXITO = "#15803d"
FUENTE = "Segoe UI"
TODOS = "(Todos)"
ESCALA = 1.0  # Factor de pantalla (125 %, 150 %…); se calcula al abrir la app.


def px(valor):
    """Convierte pixeles de diseño (pantalla al 100 %) a pixeles reales."""
    return int(round(valor * ESCALA))


def activar_dpi():
    """En Windows, evita que la ventana se vea borrosa o cortada con escalado."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass


NOMBRE_ROL = {
    ROL_PACIENTE: "Paciente",
    ROL_RECEPCIONISTA: "Recepción",
    ROL_DENTISTA: "Dentista",
}


def color_de_mensaje(mensaje):
    """Rojo para errores, ámbar para avisos y verde para confirmaciones."""
    if mensaje.startswith("Error"):
        return COLOR_ERROR
    if mensaje.startswith("Aviso"):
        return COLOR_AVISO
    return COLOR_EXITO


def mover_fecha(texto, dias):
    """Suma días a una fecha AAAA-MM-DD; si no es válida parte de mañana."""
    try:
        base = datetime.strptime(texto.strip(), "%Y-%m-%d").date()
    except ValueError:
        base = date.today()
    return (base + timedelta(days=dias)).isoformat()


# -- Ventana principal -------------------------------------------------------------


class App(tk.Tk):
    def __init__(self, bd):
        super().__init__()
        global ESCALA
        ESCALA = max(1.0, self.winfo_fpixels("1i") / 96)
        self.bd = bd
        self.sesion = None
        self.pantalla = None
        self.title(f"{TITULO} · Sistema de citas")
        ancho = min(px(1180), self.winfo_screenwidth() - px(40))
        alto = min(px(720), self.winfo_screenheight() - px(80))
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(px(980), ancho), min(px(600), alto))
        self.configure(bg=COLOR_FONDO)
        self._poner_icono()
        self._configurar_estilos()
        self.mostrar_login()

    def _poner_icono(self):
        # Dentro del .exe los archivos empaquetados están en sys._MEIPASS.
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        try:
            self.iconbitmap(default=str(base / "assets" / "orthoimagen.ico"))
        except tk.TclError:
            pass

    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure(".", font=(FUENTE, 10), background=COLOR_FONDO)
        estilo.configure("TFrame", background=COLOR_FONDO)
        estilo.configure("TLabel", background=COLOR_FONDO)
        estilo.configure("Tarjeta.TFrame", background=COLOR_TARJETA)
        estilo.configure("Tarjeta.TLabel", background=COLOR_TARJETA)
        estilo.configure("Titulo.TLabel", background=COLOR_TARJETA,
                         foreground=COLOR_PRIMARIO, font=(FUENTE, 22, "bold"))
        estilo.configure("Suave.TLabel", background=COLOR_TARJETA,
                         foreground=COLOR_TEXTO_SUAVE)
        estilo.configure("Seccion.TLabel", font=(FUENTE, 12, "bold"),
                         foreground=COLOR_PRIMARIO)
        estilo.configure("Encabezado.TFrame", background=COLOR_PRIMARIO)
        estilo.configure("Encabezado.TLabel", background=COLOR_PRIMARIO,
                         foreground="white", font=(FUENTE, 13, "bold"))
        estilo.configure("EncabezadoSuave.TLabel", background=COLOR_PRIMARIO,
                         foreground="#ccfbf1")
        estilo.configure("Primario.TButton", background=COLOR_PRIMARIO,
                         foreground="white", font=(FUENTE, 10, "bold"),
                         padding=(16, 7), borderwidth=0)
        estilo.map("Primario.TButton",
                   background=[("active", COLOR_PRIMARIO_OSCURO),
                               ("disabled", "#9ca3af")])
        estilo.configure("Peligro.TButton", background=COLOR_ERROR,
                         foreground="white", padding=(16, 7), borderwidth=0)
        estilo.map("Peligro.TButton", background=[("active", "#991b1b")])
        estilo.configure("TButton", padding=(12, 6))
        estilo.configure("Treeview", rowheight=px(28), font=(FUENTE, 10),
                         fieldbackground=COLOR_TARJETA, background=COLOR_TARJETA)
        estilo.map("Treeview", background=[("selected", COLOR_PRIMARIO)],
                   foreground=[("selected", "white")])
        estilo.configure("TCombobox", padding=4)
        estilo.map("TCombobox",
                   fieldbackground=[("readonly", COLOR_TARJETA)],
                   selectbackground=[("readonly", COLOR_TARJETA)],
                   selectforeground=[("readonly", "black")])
        estilo.configure("TEntry", padding=4)
        estilo.configure("Treeview.Heading", font=(FUENTE, 10, "bold"))
        estilo.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", padding=(18, 8), font=(FUENTE, 10),
                         background="#dbe5e5", borderwidth=0)
        estilo.map("TNotebook.Tab",
                   background=[("selected", COLOR_FONDO)],
                   foreground=[("selected", COLOR_PRIMARIO)],
                   expand=[("selected", (0, 0, 0, 0))])

    def _cambiar_pantalla(self, pantalla):
        if self.pantalla is not None:
            self.pantalla.destroy()
        self.pantalla = pantalla
        pantalla.pack(fill="both", expand=True)

    def mostrar_login(self):
        self.sesion = None
        self._cambiar_pantalla(PantallaLogin(self, self))

    def mostrar_principal(self, sesion):
        self.sesion = sesion
        self._cambiar_pantalla(PantallaPrincipal(self, self))

    def confirmar(self, titulo, texto):
        """Pregunta sí/no. Las pruebas sustituyen este método."""
        return messagebox.askyesno(titulo, texto, parent=self)


# -- Inicio de sesión (RF-11) --------------------------------------------------------


class PantallaLogin(ttk.Frame):
    def __init__(self, padre, app):
        super().__init__(padre)
        self.app = app
        self.usuario = tk.StringVar()
        self.contrasena = tk.StringVar()

        tarjeta = ttk.Frame(self, style="Tarjeta.TFrame", padding=36)
        tarjeta.place(relx=0.5, rely=0.47, anchor="center")

        ttk.Label(tarjeta, text="🦷 " + TITULO, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(tarjeta, text="Sistema de citas · Inicie sesión con su usuario",
                  style="Suave.TLabel").pack(anchor="w", pady=(2, 22))

        ttk.Label(tarjeta, text="Usuario", style="Tarjeta.TLabel").pack(anchor="w")
        self.entrada_usuario = ttk.Entry(tarjeta, textvariable=self.usuario,
                                         width=36, font=(FUENTE, 11))
        self.entrada_usuario.pack(fill="x", pady=(2, 12), ipady=3)
        ttk.Label(tarjeta, text="Contraseña", style="Tarjeta.TLabel").pack(anchor="w")
        entrada_clave = ttk.Entry(tarjeta, textvariable=self.contrasena, show="•",
                                  width=36, font=(FUENTE, 11))
        entrada_clave.pack(fill="x", pady=(2, 16), ipady=3)

        ttk.Button(tarjeta, text="Iniciar sesión", style="Primario.TButton",
                   command=self.iniciar).pack(fill="x")
        self.mensaje = tk.Label(tarjeta, text="", bg=COLOR_TARJETA, fg=COLOR_ERROR,
                                font=(FUENTE, 10), wraplength=px(320), justify="left")
        self.mensaje.pack(anchor="w", pady=(12, 0))

        usuarios = ", ".join(u for u, _, _, _ in USUARIOS_DEMO)
        ttk.Label(tarjeta, text=f"Usuarios de demostración: {usuarios}\n"
                                "(contraseñas en el README)",
                  style="Suave.TLabel", font=(FUENTE, 8), justify="left"
                  ).pack(anchor="w", pady=(18, 0))

        for entrada in (self.entrada_usuario, entrada_clave):
            entrada.bind("<Return>", lambda _evento: self.iniciar())
        self.entrada_usuario.focus_set()

    def iniciar(self):
        resultado = iniciar_sesion(self.app.bd, self.usuario.get(), self.contrasena.get())
        if not resultado["exito"]:
            self.mensaje.configure(text=resultado["mensaje"])
            self.contrasena.set("")
            return
        self.app.mostrar_principal(resultado["sesion"])


# -- Pantalla principal por rol --------------------------------------------------------


class PantallaPrincipal(ttk.Frame):
    def __init__(self, padre, app):
        super().__init__(padre)
        self.app = app
        self.bd = app.bd
        self.sesion = app.sesion
        rol = self.sesion["rol"]

        encabezado = ttk.Frame(self, style="Encabezado.TFrame", padding=(20, 12))
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="🦷 " + TITULO, style="Encabezado.TLabel").pack(side="left")
        ttk.Button(encabezado, text="Cerrar sesión",
                   command=app.mostrar_login).pack(side="right")
        ttk.Label(encabezado, style="EncabezadoSuave.TLabel",
                  text=f"{self.sesion['nombre_usuario']} · {NOMBRE_ROL[rol]}   "
                  ).pack(side="right")

        self.estado = tk.Label(self, text="", anchor="w", bg="#e5eeee",
                               font=(FUENTE, 10), padx=16, pady=7)
        self.estado.pack(side="bottom", fill="x")

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        self.pestana_agendar = None
        if rol in (ROL_PACIENTE, ROL_RECEPCIONISTA):
            self.pestana_agendar = PestanaAgendar(self.pestanas, self)
            titulo = "Agendar cita" if rol == ROL_PACIENTE else "Registrar cita"
            self.pestanas.add(self.pestana_agendar, text=titulo)
        self.pestana_citas = PestanaCitas(self.pestanas, self)
        titulo_citas = {ROL_PACIENTE: "Mis citas", ROL_RECEPCIONISTA: "Citas",
                        ROL_DENTISTA: "Mi agenda"}[rol]
        self.pestanas.add(self.pestana_citas, text=titulo_citas)
        self.pestana_catalogo = PestanaCatalogo(self.pestanas, self)
        self.pestanas.add(self.pestana_catalogo, text="Catálogo de servicios")

        self.avisar(f"Bienvenido(a), {self.sesion['nombre_usuario']}.")

    def avisar(self, mensaje):
        """Muestra un mensaje en la barra de estado con su color."""
        self.estado.configure(text=mensaje, fg=color_de_mensaje(mensaje) if mensaje else "black")

    def citas_cambiaron(self):
        """Refresca las pestañas después de agendar, modificar o cancelar."""
        self.pestana_citas.cargar(silencioso=True)
        if self.pestana_agendar is not None:
            self.pestana_agendar.ver_horarios(silencioso=True)

    # -- Catálogos para listas desplegables --

    def opciones_dentistas(self):
        try:
            return {f"{d['nombre']} {d['apellidos']}"
                    + (f" · {d['especialidad']}" if d["especialidad"] else ""):
                    d["id_odontologo"] for d in self.bd.listar_odontologos()}
        except ErrorBaseDatos as error:
            self.avisar(error.mensaje)
            return {}

    def opciones_servicios(self):
        resultado = consultar_catalogo(self.bd, self.sesion)
        return {f"{s['nombre']} ({s['duracion_min']} min)": s["id_servicio"]
                for s in resultado["servicios"]}

    def opciones_pacientes(self):
        try:
            return {f"{p['nombre']} {p['apellidos']} · {p['telefono']}": p["id_paciente"]
                    for p in self.bd.listar_pacientes()}
        except ErrorBaseDatos as error:
            self.avisar(error.mensaje)
            return {}


def combo(padre, opciones, ancho=38, con_todos=False):
    valores = ([TODOS] if con_todos else []) + list(opciones)
    caja = ttk.Combobox(padre, values=valores, state="readonly", width=ancho)
    if con_todos:
        caja.set(TODOS)
    return caja


def selector_fecha(padre, variable, al_cambiar):
    """Campo de fecha con botones para mover un día atrás o adelante."""
    marco = ttk.Frame(padre)
    entrada = ttk.Entry(marco, textvariable=variable, width=14, font=(FUENTE, 10))
    entrada.pack(side="left", ipady=2)

    def mover(dias):
        variable.set(mover_fecha(variable.get(), dias))
        al_cambiar()

    ttk.Button(marco, text="◀", width=3, command=lambda: mover(-1)).pack(side="left", padx=(6, 0))
    ttk.Button(marco, text="▶", width=3, command=lambda: mover(1)).pack(side="left", padx=(2, 0))
    entrada.bind("<Return>", lambda _evento: al_cambiar())
    return marco


# -- Agendar / registrar cita (RF-07, RF-02, RF-01) -------------------------------------


class PestanaAgendar(ttk.Frame):
    def __init__(self, padre, principal):
        super().__init__(padre, padding=20)
        self.principal = principal
        self.bd = principal.bd
        self.sesion = principal.sesion
        self.es_recepcion = self.sesion["rol"] == ROL_RECEPCIONISTA

        self.mapa_pacientes = principal.opciones_pacientes() if self.es_recepcion else {}
        self.mapa_dentistas = principal.opciones_dentistas()
        self.mapa_servicios = principal.opciones_servicios()
        self.fecha = tk.StringVar(value=mover_fecha(date.today().isoformat(), 1))
        self.motivo = tk.StringVar()

        formulario = ttk.Frame(self)
        formulario.pack(side="left", fill="y", anchor="n")
        ttk.Label(formulario, text="Datos de la cita", style="Seccion.TLabel"
                  ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        fila = 1
        self.combo_paciente = None
        if self.es_recepcion:
            ttk.Label(formulario, text="Paciente").grid(row=fila, column=0, sticky="w", pady=6)
            self.combo_paciente = combo(formulario, self.mapa_pacientes)
            self.combo_paciente.grid(row=fila, column=1, sticky="w", pady=6)
            fila += 1

        ttk.Label(formulario, text="1. Dentista").grid(row=fila, column=0, sticky="w", pady=6)
        self.combo_dentista = combo(formulario, self.mapa_dentistas)
        self.combo_dentista.grid(row=fila, column=1, sticky="w", pady=6)
        self.combo_dentista.bind("<<ComboboxSelected>>", lambda _e: self.ver_horarios())
        fila += 1

        ttk.Label(formulario, text="2. Fecha").grid(row=fila, column=0, sticky="w", pady=6)
        selector_fecha(formulario, self.fecha, self.ver_horarios).grid(
            row=fila, column=1, sticky="w", pady=6)
        fila += 1

        ttk.Label(formulario, text="4. Servicio").grid(row=fila, column=0, sticky="w", pady=6)
        self.combo_servicio = combo(formulario, self.mapa_servicios)
        self.combo_servicio.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        ttk.Label(formulario, text="Motivo (opcional)").grid(row=fila, column=0, sticky="w", pady=6)
        ttk.Entry(formulario, textvariable=self.motivo, width=41).grid(
            row=fila, column=1, sticky="w", pady=6)
        fila += 1

        ttk.Button(formulario, text="5. Confirmar cita", style="Primario.TButton",
                   command=self.confirmar).grid(row=fila, column=1, sticky="w", pady=(16, 0))

        horarios = ttk.Frame(self, padding=(36, 0, 0, 0))
        horarios.pack(side="left", fill="both", expand=True, anchor="n")
        ttk.Label(horarios, text="3. Horarios libres", style="Seccion.TLabel").pack(anchor="w")
        self.titulo_horarios = ttk.Label(horarios, text="Elija un dentista y una fecha.",
                                         foreground=COLOR_TEXTO_SUAVE)
        self.titulo_horarios.pack(anchor="w", pady=(2, 8))
        self.lista_horarios = tk.Listbox(
            horarios, height=10, width=16, font=(FUENTE, 12), exportselection=False,
            activestyle="none", selectbackground=COLOR_PRIMARIO, borderwidth=1,
            relief="solid", highlightthickness=0)
        self.lista_horarios.pack(anchor="w")
        self.ocupados = ttk.Label(horarios, text="", foreground=COLOR_TEXTO_SUAVE)
        self.ocupados.pack(anchor="w", pady=(8, 0))

    def id_de(self, caja, mapa):
        return mapa.get(caja.get(), "") if caja is not None else ""

    def ver_horarios(self, silencioso=False):
        self.lista_horarios.delete(0, "end")
        self.ocupados.configure(text="")
        id_dentista = self.id_de(self.combo_dentista, self.mapa_dentistas)
        if id_dentista == "":
            if not silencioso:
                self.principal.avisar("Aviso: Elija primero un dentista.")
            return
        resultado = consultar_disponibilidad(self.bd, self.sesion, id_dentista,
                                             self.fecha.get())
        if not silencioso or not resultado["exito"]:
            self.principal.avisar(resultado["mensaje"])
        if not resultado["exito"]:
            self.titulo_horarios.configure(text="")
            return
        for hora in resultado["libres"]:
            self.lista_horarios.insert("end", hora)
        self.titulo_horarios.configure(
            text=f"{self.combo_dentista.get().split(' · ')[0]} · {self.fecha.get().strip()}")
        if resultado["ocupados"]:
            self.ocupados.configure(text="Ocupados: " + ", ".join(resultado["ocupados"]))

    def hora_elegida(self):
        seleccion = self.lista_horarios.curselection()
        return self.lista_horarios.get(seleccion[0]) if seleccion else ""

    def confirmar(self):
        datos = {
            "fecha": self.fecha.get(),
            "hora": self.hora_elegida(),
            "dentista": self.id_de(self.combo_dentista, self.mapa_dentistas),
            "servicio": self.id_de(self.combo_servicio, self.mapa_servicios),
            "motivo": self.motivo.get(),
        }
        if self.es_recepcion:
            datos["paciente"] = self.id_de(self.combo_paciente, self.mapa_pacientes)
        resultado = registrar_cita(self.bd, self.sesion, datos)
        self.principal.avisar(resultado["mensaje"])
        if resultado["exito"]:
            self.motivo.set("")
            self.principal.citas_cambiaron()


# -- Citas: mis citas, filtros y agenda (RF-06, RF-03, RF-04, RF-05) -----------------------


COLUMNAS_CITAS = (
    ("id_cita", "Folio", 60), ("fecha", "Fecha", 100), ("hora", "Hora", 60),
    ("paciente", "Paciente", 170), ("dentista", "Dentista", 160),
    ("servicio", "Servicio", 170), ("estatus", "Estatus", 110), ("motivo", "Motivo", 160),
)


class PestanaCitas(ttk.Frame):
    def __init__(self, padre, principal):
        super().__init__(padre, padding=20)
        self.principal = principal
        self.bd = principal.bd
        self.sesion = principal.sesion
        self.rol = self.sesion["rol"]
        self.citas = {}

        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 12))
        self.fecha = tk.StringVar()
        if self.rol == ROL_PACIENTE:
            ttk.Label(filtros, text="Sus citas registradas", style="Seccion.TLabel").pack(side="left")
            ttk.Button(filtros, text="Actualizar", command=self.cargar).pack(side="right")
        elif self.rol == ROL_RECEPCIONISTA:
            self.mapa_dentistas = principal.opciones_dentistas()
            self.mapa_pacientes = principal.opciones_pacientes()
            ttk.Label(filtros, text="Día").pack(side="left")
            ttk.Entry(filtros, textvariable=self.fecha, width=12).pack(side="left", padx=(6, 14))
            ttk.Label(filtros, text="Dentista").pack(side="left")
            self.combo_dentista = combo(filtros, self.mapa_dentistas, 24, con_todos=True)
            self.combo_dentista.pack(side="left", padx=(6, 14))
            ttk.Label(filtros, text="Paciente").pack(side="left")
            self.combo_paciente = combo(filtros, self.mapa_pacientes, 28, con_todos=True)
            self.combo_paciente.pack(side="left", padx=(6, 14))
            ttk.Button(filtros, text="Filtrar", style="Primario.TButton",
                       command=self.cargar).pack(side="left")
            ttk.Button(filtros, text="Limpiar", command=self.limpiar_filtros).pack(side="left", padx=6)
        else:
            self.fecha.set(date.today().isoformat())
            ttk.Label(filtros, text="Agenda del día").pack(side="left")
            selector_fecha(filtros, self.fecha, self.cargar).pack(side="left", padx=8)

        tabla = ttk.Frame(self)
        tabla.pack(fill="both", expand=True)
        self.arbol = ttk.Treeview(tabla, columns=[c for c, _, _ in COLUMNAS_CITAS],
                                  show="headings", selectmode="browse")
        for clave, texto, ancho in COLUMNAS_CITAS:
            self.arbol.heading(clave, text=texto)
            self.arbol.column(clave, width=px(ancho), anchor="w")
        self.arbol.tag_configure("Cancelada", foreground="#9ca3af")
        self.arbol.tag_configure("Reprogramada", foreground=COLOR_AVISO)
        barra = ttk.Scrollbar(tabla, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        if self.rol in (ROL_PACIENTE, ROL_RECEPCIONISTA):
            acciones = ttk.Frame(self)
            acciones.pack(fill="x", pady=(12, 0))
            ttk.Button(acciones, text="Modificar…", style="Primario.TButton",
                       command=self.modificar).pack(side="left")
            ttk.Button(acciones, text="Cancelar cita",
                       command=self.cancelar).pack(side="left", padx=8)
            if self.rol == ROL_RECEPCIONISTA:
                ttk.Button(acciones, text="Eliminar", style="Peligro.TButton",
                           command=self.eliminar).pack(side="right")
            self.arbol.bind("<Double-1>", lambda _e: self.modificar())

        self.cargar(silencioso=True)

    def limpiar_filtros(self):
        self.fecha.set("")
        self.combo_dentista.set(TODOS)
        self.combo_paciente.set(TODOS)
        self.cargar()

    def consultar(self):
        if self.rol == ROL_PACIENTE:
            return mis_citas(self.bd, self.sesion)
        if self.rol == ROL_RECEPCIONISTA:
            return filtrar_citas(
                self.bd, self.sesion, self.fecha.get(),
                self.mapa_dentistas.get(self.combo_dentista.get(), ""),
                self.mapa_pacientes.get(self.combo_paciente.get(), ""),
            )
        return agenda_dentista(self.bd, self.sesion, self.fecha.get())

    def cargar(self, silencioso=False):
        resultado = self.consultar()
        self.arbol.delete(*self.arbol.get_children())
        self.citas = {cita["id_cita"]: cita for cita in resultado["citas"]}
        for cita in resultado["citas"]:
            valores = [cita.get(clave) or "" for clave, _, _ in COLUMNAS_CITAS]
            self.arbol.insert("", "end", iid=str(cita["id_cita"]), values=valores,
                              tags=(cita["estatus"],))
        if not silencioso or not resultado["exito"]:
            mensaje = resultado["mensaje"] or f"{len(resultado['citas'])} cita(s) encontradas."
            self.principal.avisar(mensaje)

    def cita_seleccionada(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            self.principal.avisar("Aviso: Seleccione una cita de la lista.")
            return None
        return self.citas[int(seleccion[0])]

    def modificar(self):
        cita = self.cita_seleccionada()
        if cita is not None:
            DialogoModificar(self, cita)

    def cancelar(self):
        cita = self.cita_seleccionada()
        if cita is None:
            return
        if not self.principal.app.confirmar(
                "Cancelar cita",
                f"¿Cancelar la cita {cita['id_cita']} del {cita['fecha']} a las "
                f"{cita['hora']}? El horario quedará libre."):
            return
        resultado = cancelar_cita(self.bd, self.sesion, cita["id_cita"])
        self.principal.avisar(resultado["mensaje"])
        self.principal.citas_cambiaron()

    def eliminar(self):
        cita = self.cita_seleccionada()
        if cita is None:
            return
        if not self.principal.app.confirmar(
                "Eliminar cita",
                f"¿Eliminar definitivamente la cita {cita['id_cita']} de "
                f"{cita['paciente']}? Esta acción no se puede deshacer."):
            return
        resultado = eliminar_cita(self.bd, self.sesion, cita["id_cita"])
        self.principal.avisar(resultado["mensaje"])
        self.principal.citas_cambiaron()


class DialogoModificar(tk.Toplevel):
    """Ventana para modificar una cita (RF-03)."""

    def __init__(self, pestana, cita):
        super().__init__(pestana)
        self.pestana = pestana
        self.principal = pestana.principal
        self.cita = cita
        self.title(f"Modificar cita {cita['id_cita']}")
        self.configure(bg=COLOR_FONDO, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(pestana.winfo_toplevel())

        self.mapa_dentistas = self.principal.opciones_dentistas()
        self.mapa_servicios = self.principal.opciones_servicios()
        self.es_recepcion = self.principal.sesion["rol"] == ROL_RECEPCIONISTA
        self.fecha = tk.StringVar(value=cita["fecha"])
        self.motivo = tk.StringVar(value=cita["motivo"] or "")

        ttk.Label(self, text=f"Paciente: {cita['paciente']}", style="Seccion.TLabel"
                  ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        fila = 1
        self.combo_dentista = None
        if self.es_recepcion:
            ttk.Label(self, text="Dentista").grid(row=fila, column=0, sticky="w", pady=5)
            self.combo_dentista = combo(self, self.mapa_dentistas)
            self.combo_dentista.set(self._etiqueta(self.mapa_dentistas, cita["id_odontologo"]))
            self.combo_dentista.grid(row=fila, column=1, sticky="w", pady=5)
            fila += 1
        else:
            ttk.Label(self, text=f"Dentista: {cita['dentista']}").grid(
                row=fila, column=0, columnspan=2, sticky="w", pady=5)
            fila += 1

        ttk.Label(self, text="Fecha").grid(row=fila, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.fecha, width=14).grid(row=fila, column=1, sticky="w", pady=5)
        fila += 1
        ttk.Label(self, text="Hora").grid(row=fila, column=0, sticky="w", pady=5)
        self.combo_hora = ttk.Combobox(self, values=horarios_del_dia(), state="readonly", width=10)
        self.combo_hora.set(cita["hora"])
        self.combo_hora.grid(row=fila, column=1, sticky="w", pady=5)
        fila += 1
        ttk.Label(self, text="Servicio").grid(row=fila, column=0, sticky="w", pady=5)
        self.combo_servicio = combo(self, self.mapa_servicios)
        self.combo_servicio.set(self._etiqueta(self.mapa_servicios, cita["id_servicio"]))
        self.combo_servicio.grid(row=fila, column=1, sticky="w", pady=5)
        fila += 1
        ttk.Label(self, text="Motivo").grid(row=fila, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.motivo, width=41).grid(row=fila, column=1, sticky="w", pady=5)
        fila += 1

        self.mensaje = tk.Label(self, text="", bg=COLOR_FONDO, fg=COLOR_ERROR,
                                wraplength=px(380), justify="left")
        self.mensaje.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(8, 0))
        fila += 1
        botones = ttk.Frame(self)
        botones.grid(row=fila, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botones, text="Cerrar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar cambios", style="Primario.TButton",
                   command=self.guardar).pack(side="right", padx=8)

    @staticmethod
    def _etiqueta(mapa, identificador):
        for etiqueta, valor in mapa.items():
            if valor == identificador:
                return etiqueta
        return ""

    def guardar(self):
        cambios = {
            "fecha": self.fecha.get(),
            "hora": self.combo_hora.get(),
            "servicio": self.mapa_servicios.get(self.combo_servicio.get(), ""),
            "motivo": self.motivo.get(),
        }
        if self.combo_dentista is not None:
            cambios["dentista"] = self.mapa_dentistas.get(self.combo_dentista.get(), "")
        resultado = modificar_cita(self.principal.bd, self.principal.sesion,
                                   self.cita["id_cita"], cambios)
        if not resultado["exito"]:
            self.mensaje.configure(text=resultado["mensaje"])
            return
        self.principal.avisar(resultado["mensaje"])
        self.principal.citas_cambiaron()
        self.destroy()


# -- Catálogo de servicios (RF-08) ---------------------------------------------------------


class PestanaCatalogo(ttk.Frame):
    def __init__(self, padre, principal):
        super().__init__(padre, padding=20)
        self.principal = principal
        cabecera = ttk.Frame(self)
        cabecera.pack(fill="x", pady=(0, 12))
        ttk.Label(cabecera, text="Servicios de la clínica", style="Seccion.TLabel").pack(side="left")
        ttk.Button(cabecera, text="Actualizar", command=self.cargar).pack(side="right")
        columnas = (("nombre", "Servicio", 220), ("duracion", "Duración", 90),
                    ("precio", "Precio", 110), ("descripcion", "Descripción", 380))
        self.arbol = ttk.Treeview(self, columns=[c for c, _, _ in columnas], show="headings")
        for clave, texto, ancho in columnas:
            self.arbol.heading(clave, text=texto)
            self.arbol.column(clave, width=px(ancho), anchor="w")
        self.arbol.pack(fill="both", expand=True)
        self.cargar(silencioso=True)

    def cargar(self, silencioso=False):
        resultado = consultar_catalogo(self.principal.bd, self.principal.sesion)
        self.arbol.delete(*self.arbol.get_children())
        for servicio in resultado["servicios"]:
            precio = servicio["precio"]
            self.arbol.insert("", "end", values=(
                servicio["nombre"], f"{servicio['duracion_min']} min",
                f"${precio:,.2f} MXN" if precio is not None else "A consultar",
                servicio["descripcion"] or ""))
        if not silencioso or resultado["mensaje"]:
            self.principal.avisar(resultado["mensaje"]
                                  or f"{len(resultado['servicios'])} servicio(s) en el catálogo.")


def main():
    activar_dpi()
    try:
        settings.RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
        bd = BaseDatos(settings.RUTA_BD)
        bd.inicializar()
        sembrar_datos_demo(bd)
    except (ErrorBaseDatos, OSError) as error:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror(TITULO, getattr(error, "mensaje", str(error)))
        raiz.destroy()
        return 1
    app = App(bd)
    try:
        app.mainloop()
    finally:
        bd.cerrar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
