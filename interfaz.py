"""
Módulo: interfaz.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4

Descripción:
    Interfaz gráfica (Tkinter) para usar el sistema sin escribir código.
    Se navega con un menú lateral:

    * Inicio    -> resumen con totales, siguiente paso sugerido y últimas reservas.
    * Clientes  -> registrar clientes y activarlos / inactivarlos.
    * Servicios -> crear salas, alquileres de equipo y asesorías.
    * Reservas  -> reservar un servicio para un cliente, confirmarla o cancelarla.
    * Registro  -> ver y buscar en el archivo sistema.log (eventos y errores).

    Mejoras de usabilidad:
    * Búsqueda y ordenamiento (clic en el encabezado) en todas las tablas.
    * Estados con color (verde = activo/disponible/confirmada, ámbar = pendiente...).
    * Menú con clic derecho sobre las filas.
    * Barra de estado inferior para los mensajes de éxito (sin ventanas molestas).
    * Atajos: Enter envía el formulario, Ctrl+1..5 cambia de sección, F1 abre la ayuda.

    Los errores se muestran en una ventana de aviso y quedan en el log;
    la aplicación nunca se cierra por un dato mal escrito.

Ejecución:
    python interfaz.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font as tkfont
from datetime import date, timedelta

from cliente import Cliente
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
from reserva import GestorReservas
from excepciones import ErrorSistema
from gestor_logs import GestorLogs


# ----------------------------------------------------------------------
# Paleta de colores
# ----------------------------------------------------------------------
COLORES = {
    "lateral": "#16324f",        # menú lateral
    "lateral_hover": "#21446a",
    "lateral_texto": "#c9d7e6",
    "fondo": "#eef2f6",          # fondo de las páginas
    "superficie": "#ffffff",     # tarjetas
    "borde": "#d3dce6",
    "texto": "#1c2733",
    "suave": "#5f6f80",
    "acento": "#2563c9",
    "acento_hover": "#1d4fa3",
    "ok": "#1e7f4f",
    "aviso": "#a86400",
    "error": "#b3261e",
    "apagado": "#8592a0",
    "cebra": "#f6f8fb",
    "encabezado_tabla": "#e7edf4",
}

# Color del texto de cada estado en las tablas
ESTADO_COLOR = {
    "ACTIVO": COLORES["ok"],
    "DISPONIBLE": COLORES["ok"],
    "CONFIRMADA": COLORES["ok"],
    "PENDIENTE": COLORES["aviso"],
    "INACTIVO": COLORES["apagado"],
    "NO_DISPONIBLE": COLORES["apagado"],
    "CANCELADA": COLORES["error"],
}


# ----------------------------------------------------------------------
# Textos de ayuda: uno por módulo
# ----------------------------------------------------------------------
AYUDA = {
    "Cómo usar esta aplicación": (
        "Software FJ permite gestionar CLIENTES, SERVICIOS y RESERVAS.\n\n"
        "Orden recomendado:\n"
        "  1. Clientes: registre al menos un cliente.\n"
        "  2. Servicios: cree al menos un servicio.\n"
        "  3. Reservas: elija cliente y servicio y registre la reserva.\n"
        "  4. Confirme o cancele la reserva.\n"
        "  5. Registro: revise qué quedó guardado en el log.\n\n"
        "La sección Inicio le indica en todo momento cuál es el siguiente paso.\n\n"
        "Si algún dato es incorrecto, aparecerá un mensaje explicando el error. "
        "Corríjalo y vuelva a intentar: el programa no se cierra."
    ),
    "Atajos de teclado": (
        "  • Enter: envía el formulario en el que está escribiendo.\n"
        "  • Ctrl+1 … Ctrl+5: Inicio, Clientes, Servicios, Reservas, Registro.\n"
        "  • F1: abre esta ayuda.\n\n"
        "En las tablas:\n"
        "  • Clic en un encabezado: ordena por esa columna (otro clic invierte el orden).\n"
        "  • Clic derecho sobre una fila: muestra las acciones disponibles.\n"
        "  • Casilla Buscar: filtra las filas mientras escribe."
    ),
    "Clientes (cliente.py)": (
        "Sirve para registrar a las personas o empresas que contratan servicios.\n\n"
        "Datos que pide:\n"
        "  • Identificación: número de documento (será el ID del cliente).\n"
        "  • Nombre completo.\n"
        "  • Correo electrónico válido (ej. ana@correo.com).\n"
        "  • Teléfono de contacto.\n"
        "  • Dirección.\n\n"
        "Un cliente puede estar ACTIVO o INACTIVO. Solo los clientes ACTIVOS "
        "pueden hacer reservas. Use el botón 'Activar / Inactivar' para cambiarlo."
    ),
    "Servicios (servicio.py y subclases)": (
        "Sirve para crear los servicios que ofrece Software FJ. Hay tres tipos:\n\n"
        "  • Reserva de sala (reserva_sala.py): se cobra por hora.\n"
        "      Pide nombre de la sala, horas (máx. 12), capacidad (1-100) y costo por hora.\n\n"
        "  • Alquiler de equipo (alquiler_equipo.py): se cobra por día y por equipo.\n"
        "      Pide tipo de equipo, cantidad (1-50), días (1-30) y tarifa diaria.\n\n"
        "  • Asesoría especializada (asesoria_especializada.py): se cobra por hora.\n"
        "      Pide tipo de asesoría, especialista, horas (máx. 40) y tarifa por hora.\n\n"
        "Todos tienen nombre, descripción y precio base (cargo fijo). "
        "El costo se calcula automáticamente. Un servicio NO_DISPONIBLE no se puede reservar."
    ),
    "Reservas (reserva.py)": (
        "Sirve para unir un cliente con un servicio en una fecha.\n\n"
        "  • Registrar: crea la reserva en estado PENDIENTE.\n"
        "  • Confirmar: calcula el costo final (con IVA si se marca y con el "
        "descuento indicado) y la pasa a CONFIRMADA.\n"
        "  • Cancelar: pide un motivo y la pasa a CANCELADA.\n\n"
        "La fecha se escribe como AAAA-MM-DD y no puede ser una fecha pasada. "
        "Los botones 'Hoy' y 'Mañana' la llenan por usted."
    ),
    "Registro de eventos (gestor_logs.py)": (
        "Todo lo que pasa en el sistema (registros, cambios de estado y errores) "
        "se guarda en el archivo sistema.log.\n\n"
        "En esta sección puede leer ese archivo, filtrar por nivel y buscar texto:\n"
        "  • INFO: operaciones exitosas.\n"
        "  • WARNING: avisos.\n"
        "  • ERROR: fallos controlados (datos inválidos, operaciones no permitidas)."
    ),
    "Errores (excepciones.py)": (
        "Define los errores propios del sistema, por ejemplo:\n\n"
        "  • ParametroFaltante: falta un dato obligatorio.\n"
        "  • DatosClienteInvalidos / DatosServicioInvalidos: un dato no cumple su formato.\n"
        "  • ServicioNoDisponibleError: el servicio no se puede reservar.\n"
        "  • ReservaInvalidaError, EstadoReservaError (excepciones_reserva.py): "
        "problemas con las reservas.\n\n"
        "Cada error tiene un código (ej. [VAL-001]) que aparece en el mensaje y en el log."
    ),
    "Base del sistema (entidad_base.py)": (
        "Es la clase 'madre' de Cliente, Servicio y Reserva. Les da a todas:\n\n"
        "  • Un ID único.\n"
        "  • Un estado controlado (solo valores permitidos).\n"
        "  • Fecha de creación y de última modificación.\n\n"
        "No se usa directamente desde la interfaz, pero todo el sistema se apoya en ella."
    ),
}

# Campos propios de cada tipo de servicio: (etiqueta, nombre del parámetro, pista)
CAMPOS_SERVICIO = {
    "Reserva de sala": (ReservaSala, [
        ("Nombre de la sala", "nombre_sala", "Ej. Sala Galeras"),
        ("Horas", "horas", "Máximo 12"),
        ("Capacidad (personas)", "capacidad", "De 1 a 100"),
        ("Costo por hora", "costo_hora", "En pesos"),
    ]),
    "Alquiler de equipo": (AlquilerEquipo, [
        ("Tipo de equipo", "tipo_equipo", "Ej. Portátil, videobeam"),
        ("Cantidad", "cantidad", "De 1 a 50"),
        ("Días", "dias", "De 1 a 30"),
        ("Tarifa diaria", "tarifa_diaria", "Por equipo, en pesos"),
    ]),
    "Asesoría especializada": (AsesoriaEspecializada, [
        ("Tipo de asesoría", "tipo_asesoria", ""),
        ("Especialista", "especialista", "Nombre del profesional"),
        ("Horas", "horas", "Máximo 40"),
        ("Tarifa por hora", "tarifa_hora", "En pesos"),
    ]),
}

# Parámetros de servicio que son texto (el resto se convierten a número)
CAMPOS_TEXTO = {"nombre_sala", "tipo_equipo", "tipo_asesoria", "especialista"}


# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------
def a_numero(texto):
    """Convierte el texto a número si se puede; si no, lo deja igual para que la clase lo valide."""
    texto = texto.strip()
    if texto == "":
        return None
    try:
        numero = float(texto.replace(",", "."))
        return int(numero) if numero.is_integer() else numero
    except ValueError:
        return texto


def texto_o_none(texto):
    """Devuelve None si el campo está vacío (así la clase avisa 'falta el dato')."""
    texto = texto.strip()
    return texto if texto else None


def pesos(valor):
    """Formato de moneda simple: $ 1.234.567"""
    return "$ " + f"{valor:,.0f}".replace(",", ".")


def _clave_orden(valor):
    """Clave para ordenar columnas: números (incluidos montos en pesos) antes que texto."""
    texto = str(valor)
    if texto.startswith("$ "):
        texto = texto[2:].replace(".", "")
    try:
        return (0, float(texto.replace(",", ".")), "")
    except ValueError:
        return (1, 0, texto.lower())


# ----------------------------------------------------------------------
# Tabla con búsqueda, orden por columna, filas cebra y estados con color
# ----------------------------------------------------------------------
class Tabla(ttk.Frame):
    """Treeview con casilla de búsqueda, orden al hacer clic y mensaje cuando está vacía.

    La última columna de cada fila debe ser el estado: se usa para darle color.
    """

    def __init__(self, padre, columnas, buscar=True, altura=None):
        super().__init__(padre)
        self.columnas = [nombre for nombre, _ in columnas]
        self._filas = []
        self._orden = (None, False)
        self._texto_vacio = "Todavía no hay registros."
        self.texto_buscar = tk.StringVar()
        self.contador = None

        if buscar:
            barra = ttk.Frame(self)
            barra.pack(fill="x", pady=(0, 8))
            ttk.Label(barra, text="Buscar:", style="Suave.TLabel").pack(side="left")
            ttk.Entry(barra, textvariable=self.texto_buscar, width=28).pack(side="left", padx=6)
            self.texto_buscar.trace_add("write", lambda *_: self._pintar())
            self.contador = ttk.Label(barra, style="Suave.TLabel")
            self.contador.pack(side="right")

        marco = ttk.Frame(self)
        marco.pack(fill="both", expand=True)
        opciones = {"height": altura} if altura else {}
        self.arbol = ttk.Treeview(marco, columns=self.columnas, show="headings",
                                  selectmode="browse", **opciones)
        for nombre, ancho in columnas:
            self.arbol.heading(nombre, text=nombre, command=lambda n=nombre: self._ordenar(n))
            self.arbol.column(nombre, width=ancho, minwidth=50, anchor="w")
        barra_y = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra_y.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra_y.pack(side="right", fill="y")

        self.arbol.tag_configure("par", background=COLORES["cebra"])
        for estado, color in ESTADO_COLOR.items():
            self.arbol.tag_configure(estado, foreground=color)

        self.vacio = tk.Label(self.arbol, bg=COLORES["superficie"], fg=COLORES["suave"],
                              font=("TkDefaultFont", 10), justify="center")

    # --- datos -------------------------------------------------------
    def cargar(self, filas, vacio=None):
        """filas: lista de (iid, (valor1, valor2, ..., estado))."""
        self._filas = list(filas)
        if vacio:
            self._texto_vacio = vacio
        self._pintar()

    def seleccion(self):
        seleccion = self.arbol.selection()
        return seleccion[0] if seleccion else None

    # --- dibujo ------------------------------------------------------
    def _pintar(self):
        anterior = self.seleccion()
        self.arbol.delete(*self.arbol.get_children())

        filtro = self.texto_buscar.get().strip().lower()
        filas = [f for f in self._filas
                 if not filtro or filtro in " ".join(map(str, f[1])).lower()]

        columna, descendente = self._orden
        if columna is not None:
            indice = self.columnas.index(columna)
            filas.sort(key=lambda f: _clave_orden(f[1][indice]), reverse=descendente)

        for numero, (iid, valores) in enumerate(filas):
            etiquetas = [str(valores[-1])]
            if numero % 2:
                etiquetas.append("par")
            self.arbol.insert("", "end", iid=iid, values=valores, tags=etiquetas)

        if anterior and self.arbol.exists(anterior):
            self.arbol.selection_set(anterior)

        if self.contador is not None:
            total = len(self._filas)
            self.contador.config(text=f"{len(filas)} de {total}" if filtro else f"{total} en total")

        if filas:
            self.vacio.place_forget()
        else:
            texto = f"Ningún resultado contiene «{filtro}»." if filtro else self._texto_vacio
            self.vacio.config(text=texto)
            self.vacio.place(relx=0.5, rely=0.45, anchor="center")

    def _ordenar(self, columna):
        actual, descendente = self._orden
        self._orden = (columna, not descendente if actual == columna else False)
        for nombre in self.columnas:
            flecha = ""
            if nombre == columna:
                flecha = "  ▼" if self._orden[1] else "  ▲"
            self.arbol.heading(nombre, text=nombre + flecha)
        self._pintar()

    def menu_contextual(self, acciones):
        """acciones: lista de (texto, función). Se muestra con clic derecho sobre una fila."""
        menu = tk.Menu(self, tearoff=False)
        for texto, funcion in acciones:
            menu.add_command(label=texto, command=funcion)

        def abrir(evento):
            fila = self.arbol.identify_row(evento.y)
            if fila:
                self.arbol.selection_set(fila)
                self.arbol.focus(fila)
                menu.tk_popup(evento.x_root, evento.y_root)

        self.arbol.bind("<Button-3>", abrir)   # Windows / Linux
        self.arbol.bind("<Button-2>", abrir)   # macOS


# ----------------------------------------------------------------------
# Ventana principal
# ----------------------------------------------------------------------
class AplicacionFJ(tk.Tk):
    """Ventana principal de Software FJ."""

    SECCIONES = [
        ("inicio", "🏠", "Inicio"),
        ("clientes", "👤", "Clientes"),
        ("servicios", "🛠", "Servicios"),
        ("reservas", "📅", "Reservas"),
        ("registro", "📄", "Registro"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Software FJ - Gestión de Clientes, Servicios y Reservas")
        self.geometry("1120x700")
        self.minsize(960, 600)
        self.configure(bg=COLORES["fondo"])

        self.log = GestorLogs.obtener_instancia()
        self.clientes = {}          # id (texto) -> Cliente
        self.servicios = {}         # código (texto) -> Servicio
        self.gestor_reservas = GestorReservas()
        self._id_aviso = None

        self._configurar_estilos()
        self._crear_menu_lateral()

        derecha = tk.Frame(self, bg=COLORES["fondo"])
        derecha.pack(side="left", fill="both", expand=True)
        self.contenedor = tk.Frame(derecha, bg=COLORES["fondo"])
        self.contenedor.pack(fill="both", expand=True)
        self.contenedor.rowconfigure(0, weight=1)
        self.contenedor.columnconfigure(0, weight=1)
        self._crear_barra_estado(derecha)

        self.vistas = {}
        self._crear_vista_inicio()
        self._crear_vista_clientes()
        self._crear_vista_servicios()
        self._crear_vista_reservas()
        self._crear_vista_registro()

        self._crear_atajos()
        self._centrar()
        self.mostrar("inicio")
        self.log.info("Interfaz gráfica iniciada", origen="Interfaz")

    # ------------------------------------------------------------------
    # Apariencia general
    # ------------------------------------------------------------------
    def _configurar_estilos(self):
        familias = set(tkfont.families(self))
        self.fuente = next((f for f in ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans")
                            if f in familias), "Helvetica")
        F, C = self.fuente, COLORES

        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        # Por defecto todo va sobre tarjetas blancas
        estilo.configure(".", font=(F, 10), background=C["superficie"], foreground=C["texto"],
                         bordercolor=C["borde"], focuscolor=C["acento"])
        estilo.configure("Fondo.TFrame", background=C["fondo"])
        estilo.configure("Suave.TLabel", foreground=C["suave"])
        estilo.configure("Pista.TLabel", foreground=C["apagado"], font=(F, 8))
        estilo.configure("Etiqueta.TLabel", font=(F, 9, "bold"), foreground=C["suave"])
        estilo.configure("TitPagina.TLabel", background=C["fondo"], font=(F, 18, "bold"))
        estilo.configure("SubPagina.TLabel", background=C["fondo"], foreground=C["suave"], font=(F, 10))

        estilo.configure("TEntry", fieldbackground="white", padding=5, bordercolor=C["borde"],
                         lightcolor=C["borde"], darkcolor=C["borde"])
        estilo.map("TEntry", bordercolor=[("focus", C["acento"])], lightcolor=[("focus", C["acento"])])
        estilo.configure("TCombobox", padding=4, arrowsize=14)
        estilo.map("TCombobox", fieldbackground=[("readonly", "white")],
                   selectbackground=[("readonly", "white")], selectforeground=[("readonly", C["texto"])])

        estilo.configure("TButton", padding=(12, 6), background="white", bordercolor=C["borde"],
                         lightcolor="white", darkcolor=C["borde"])
        estilo.map("TButton", background=[("disabled", "#f3f5f8"), ("active", "#eef3f9")],
                   foreground=[("disabled", C["apagado"])])
        estilo.configure("Primario.TButton", font=(F, 10, "bold"), foreground="white",
                         background=C["acento"], bordercolor=C["acento"],
                         lightcolor=C["acento"], darkcolor=C["acento"], padding=(14, 8))
        estilo.map("Primario.TButton",
                   background=[("disabled", "#a9c1ea"), ("active", C["acento_hover"])],
                   foreground=[("disabled", "white")])
        estilo.configure("Peligro.TButton", foreground=C["error"])

        estilo.configure("Treeview", rowheight=28, fieldbackground="white", background="white",
                         bordercolor=C["borde"])
        estilo.map("Treeview", background=[("selected", "#d6e4fa")],
                   foreground=[("selected", C["texto"])])
        estilo.configure("Treeview.Heading", font=(F, 9, "bold"), background=C["encabezado_tabla"],
                         foreground=C["suave"], relief="flat", padding=(6, 6))
        estilo.map("Treeview.Heading", background=[("active", "#dbe4ee")])

    def _crear_menu_lateral(self):
        C, F = COLORES, self.fuente
        lateral = tk.Frame(self, bg=C["lateral"], width=200)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        tk.Label(lateral, text="Software FJ", bg=C["lateral"], fg="white",
                 font=(F, 16, "bold"), anchor="w").pack(fill="x", padx=18, pady=(20, 0))
        tk.Label(lateral, text="Gestión de clientes,\nservicios y reservas", bg=C["lateral"],
                 fg=C["lateral_texto"], font=(F, 9), anchor="w", justify="left").pack(fill="x", padx=18, pady=(0, 22))

        self.botones_menu = {}
        for clave, icono, texto in self.SECCIONES:
            self.botones_menu[clave] = self._item_menu(lateral, f"{icono}   {texto}",
                                                       lambda c=clave: self.mostrar(c))

        ayuda = self._item_menu(lateral, "❓   Ayuda  (F1)", self.mostrar_ayuda)
        ayuda.pack_forget()
        ayuda.pack(side="bottom", fill="x", pady=(0, 16))

    def _item_menu(self, padre, texto, comando):
        C = COLORES
        item = tk.Label(padre, text=texto, bg=C["lateral"], fg=C["lateral_texto"],
                        font=(self.fuente, 11), anchor="w", padx=18, pady=10, cursor="hand2")
        item.pack(fill="x")
        item.activo = False
        item.bind("<Button-1>", lambda e: comando())
        item.bind("<Enter>", lambda e: item.activo or item.config(bg=C["lateral_hover"]))
        item.bind("<Leave>", lambda e: item.activo or item.config(bg=C["lateral"]))
        return item

    def _crear_barra_estado(self, padre):
        self.barra_estado = tk.Label(padre, text="Listo.", anchor="w", padx=16, pady=6,
                                     bg="#e3e9f0", fg=COLORES["suave"], font=(self.fuente, 9))
        self.barra_estado.pack(side="bottom", fill="x")

    def _crear_atajos(self):
        for numero, (clave, _, _) in enumerate(self.SECCIONES, start=1):
            self.bind_all(f"<Control-Key-{numero}>", lambda e, c=clave: self.mostrar(c))
        self.bind_all("<F1>", lambda e: self.mostrar_ayuda())

    def _centrar(self):
        self.update_idletasks()
        ancho, alto = self.winfo_width(), self.winfo_height()
        x = max((self.winfo_screenwidth() - ancho) // 2, 0)
        y = max((self.winfo_screenheight() - alto) // 3, 0)
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def mostrar(self, clave):
        C = COLORES
        for nombre, item in self.botones_menu.items():
            item.activo = nombre == clave
            item.config(bg=C["fondo"] if item.activo else C["lateral"],
                        fg=C["texto"] if item.activo else C["lateral_texto"],
                        font=(self.fuente, 11, "bold" if item.activo else "normal"))
        self.vistas[clave].tkraise()

        if clave == "inicio":
            self._refrescar_inicio()
        elif clave == "reservas":
            self._actualizar_combos_reserva()
        elif clave == "registro":
            self._cargar_log()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def avisar(self, texto, tipo="ok"):
        """Muestra un mensaje en la barra de estado durante unos segundos."""
        colores = {"ok": COLORES["ok"], "error": COLORES["error"], "aviso": COLORES["aviso"]}
        iconos = {"ok": "✔  ", "error": "✖  ", "aviso": "⚠  "}
        self.barra_estado.config(text=iconos[tipo] + texto, fg=colores[tipo])
        if self._id_aviso:
            self.after_cancel(self._id_aviso)
        self._id_aviso = self.after(7000, lambda: self.barra_estado.config(
            text="Listo.", fg=COLORES["suave"]))

    def _ejecutar(self, accion, exito=None):
        """Ejecuta una acción mostrando cualquier error en pantalla (sin cerrar el programa)."""
        try:
            resultado = accion()
        except ErrorSistema as error:
            self.avisar("No se pudo completar la operación. Revise el dato indicado.", "error")
            messagebox.showerror("Dato no válido", str(error), parent=self)
            return None
        except Exception as error:  # Error inesperado: se registra y se informa.
            self.log.error("Error inesperado en la interfaz", error, origen="Interfaz")
            self.avisar("Ocurrió un error inesperado. Quedó guardado en el registro.", "error")
            messagebox.showerror("Error inesperado", f"{type(error).__name__}: {error}", parent=self)
            return None
        if exito:
            self.avisar(exito)
        return resultado if resultado is not None else True

    def _pagina(self, clave, titulo, descripcion):
        """Crea una página con título y devuelve el marco donde va su contenido."""
        pagina = ttk.Frame(self.contenedor, style="Fondo.TFrame", padding=(24, 20, 24, 16))
        pagina.grid(row=0, column=0, sticky="nsew")
        ttk.Label(pagina, text=titulo, style="TitPagina.TLabel").pack(anchor="w")
        ttk.Label(pagina, text=descripcion, style="SubPagina.TLabel").pack(anchor="w", pady=(2, 16))
        cuerpo = ttk.Frame(pagina, style="Fondo.TFrame")
        cuerpo.pack(fill="both", expand=True)
        self.vistas[clave] = pagina
        return cuerpo

    def _tarjeta(self, padre, titulo=None, padding=16):
        """Bloque blanco con borde fino. Devuelve (marco_exterior, cuerpo)."""
        marco = tk.Frame(padre, bg=COLORES["superficie"], highlightthickness=1,
                         highlightbackground=COLORES["borde"], highlightcolor=COLORES["borde"])
        if titulo:
            tk.Label(marco, text=titulo, bg=COLORES["superficie"], fg=COLORES["texto"],
                     font=(self.fuente, 11, "bold"), anchor="w").pack(fill="x", padx=padding,
                                                                     pady=(padding - 2, 0))
        cuerpo = ttk.Frame(marco, padding=padding)
        cuerpo.pack(fill="both", expand=True)
        return marco, cuerpo

    @staticmethod
    def _formulario(padre, campos, ancho=28, al_enviar=None):
        """Crea etiqueta + caja (+ pista opcional) por campo y devuelve {clave: Entry}.

        campos: lista de (etiqueta, clave) o (etiqueta, clave, pista).
        """
        entradas = {}
        fila = 0
        for campo in campos:
            etiqueta, clave = campo[0], campo[1]
            pista = campo[2] if len(campo) > 2 else ""
            ttk.Label(padre, text=etiqueta, style="Etiqueta.TLabel").grid(
                row=fila, column=0, sticky="w", pady=(8 if fila else 0, 2))
            caja = ttk.Entry(padre, width=ancho)
            caja.grid(row=fila + 1, column=0, sticky="ew")
            if al_enviar:
                caja.bind("<Return>", lambda e: al_enviar())
            entradas[clave] = caja
            fila += 2
            if pista:
                ttk.Label(padre, text=pista, style="Pista.TLabel").grid(row=fila, column=0, sticky="w")
                fila += 1
        padre.columnconfigure(0, weight=1)
        return entradas

    @staticmethod
    def _limpiar(entradas):
        for caja in entradas.values():
            if isinstance(caja, ttk.Combobox) and caja.cget("state") == "readonly":
                continue
            caja.delete(0, "end")

    # ------------------------------------------------------------------
    # Inicio (resumen)
    # ------------------------------------------------------------------
    def _crear_vista_inicio(self):
        cuerpo = self._pagina("inicio", "Resumen", "Estado actual de clientes, servicios y reservas.")
        C, F = COLORES, self.fuente

        fila = ttk.Frame(cuerpo, style="Fondo.TFrame")
        fila.pack(fill="x")
        self.metricas = {}
        definicion = [("clientes", "Clientes"), ("servicios", "Servicios"),
                      ("reservas", "Reservas"), ("ingresos", "Ingresos confirmados")]
        for columna, (clave, titulo) in enumerate(definicion):
            marco, interior = self._tarjeta(fila, padding=16)
            marco.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 12, 0))
            fila.columnconfigure(columna, weight=1, uniform="metricas")
            ttk.Label(interior, text=titulo, style="Suave.TLabel").pack(anchor="w")
            valor = tk.Label(interior, text="0", bg=C["superficie"], fg=C["texto"],
                             font=(F, 22, "bold"), anchor="w")
            valor.pack(anchor="w", pady=(2, 0))
            detalle = ttk.Label(interior, text="", style="Suave.TLabel")
            detalle.pack(anchor="w")
            self.metricas[clave] = (valor, detalle)

        abajo = ttk.Frame(cuerpo, style="Fondo.TFrame")
        abajo.pack(fill="both", expand=True, pady=(16, 0))

        marco, interior = self._tarjeta(abajo, "Siguiente paso")
        marco.pack(side="left", fill="y", padx=(0, 12))
        marco.configure(width=300)
        self.texto_siguiente = tk.Label(interior, text="", bg=C["superficie"], fg=C["texto"],
                                        font=(F, 11), wraplength=250, justify="left", anchor="w")
        self.texto_siguiente.pack(anchor="w", fill="x")
        self.boton_siguiente = ttk.Button(interior, style="Primario.TButton")
        self.boton_siguiente.pack(anchor="w", pady=(14, 0))

        marco, interior = self._tarjeta(abajo, "Reservas recientes")
        marco.pack(side="left", fill="both", expand=True)
        self.tabla_recientes = Tabla(interior, [
            ("ID", 80), ("Cliente", 150), ("Servicio", 150), ("Fecha", 100),
            ("Costo", 110), ("Estado", 100)], buscar=False)
        self.tabla_recientes.pack(fill="both", expand=True)

    def _refrescar_inicio(self):
        clientes = list(self.clientes.values())
        servicios = list(self.servicios.values())
        reservas = list(self.gestor_reservas.listar_reservas())

        activos = sum(1 for c in clientes if c.estado == "ACTIVO")
        disponibles = sum(1 for s in servicios if s.estado == "DISPONIBLE")
        pendientes = sum(1 for r in reservas if r.estado == "PENDIENTE")
        confirmadas = [r for r in reservas if r.estado == "CONFIRMADA"]
        ingresos = sum(r.costo_total for r in confirmadas)

        datos = {
            "clientes": (len(clientes), f"{activos} activos"),
            "servicios": (len(servicios), f"{disponibles} disponibles"),
            "reservas": (len(reservas), f"{pendientes} por confirmar"),
            "ingresos": (pesos(ingresos), f"{len(confirmadas)} reservas confirmadas"),
        }
        for clave, (valor, detalle) in datos.items():
            self.metricas[clave][0].config(text=valor)
            self.metricas[clave][1].config(text=detalle)

        if not clientes:
            texto, boton, destino = "Registre su primer cliente para empezar.", "Ir a Clientes", "clientes"
        elif not servicios:
            texto, boton, destino = "Cree un servicio para poder reservarlo.", "Ir a Servicios", "servicios"
        elif not reservas:
            texto, boton, destino = ("Ya tiene clientes y servicios: registre la primera reserva.",
                                     "Ir a Reservas", "reservas")
        elif pendientes:
            texto = (f"Hay {pendientes} reserva{'s' if pendientes > 1 else ''} "
                     f"pendiente{'s' if pendientes > 1 else ''} de confirmar.")
            boton, destino = "Revisar reservas", "reservas"
        else:
            texto, boton, destino = ("No hay reservas pendientes. Puede revisar el registro "
                                     "de eventos.", "Ver registro", "registro")
        self.texto_siguiente.config(text=texto)
        self.boton_siguiente.config(text=boton, command=lambda: self.mostrar(destino))

        recientes = reservas[-8:][::-1]
        self.tabla_recientes.cargar(
            [(str(r.id), (r.id, r.cliente.nombre, r.servicio.nombre, r.fecha_realizacion,
                          pesos(r.costo_total), r.estado)) for r in recientes],
            vacio="Las reservas que registre aparecerán aquí.")

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------
    def _crear_vista_clientes(self):
        cuerpo = self._pagina("clientes", "Clientes",
                              "Personas o empresas que contratan servicios. Solo los activos pueden reservar.")

        marco, formulario = self._tarjeta(cuerpo, "Nuevo cliente")
        marco.pack(side="left", fill="y", padx=(0, 16))
        campos = ttk.Frame(formulario)
        campos.pack(fill="x")
        self.entradas_cliente = self._formulario(campos, [
            ("Identificación", "identificacion", "Número de documento"),
            ("Nombre completo", "nombre"),
            ("Correo", "correo", "Ej. ana@correo.com"),
            ("Teléfono", "telefono"),
            ("Dirección", "direccion"),
        ], ancho=28, al_enviar=self.registrar_cliente)
        ttk.Button(formulario, text="Registrar cliente", style="Primario.TButton",
                   command=self.registrar_cliente).pack(fill="x", pady=(18, 4))
        ttk.Button(formulario, text="Limpiar campos",
                   command=lambda: self._limpiar(self.entradas_cliente)).pack(fill="x")

        marco, lista = self._tarjeta(cuerpo, "Clientes registrados")
        marco.pack(side="left", fill="both", expand=True)
        self.tabla_clientes = Tabla(lista, [
            ("ID", 100), ("Nombre", 170), ("Correo", 190), ("Teléfono", 110), ("Estado", 90)])
        self.tabla_clientes.pack(fill="both", expand=True)
        self.tabla_clientes.menu_contextual([("Activar / Inactivar", self.cambiar_estado_cliente)])
        ttk.Button(lista, text="Activar / Inactivar seleccionado",
                   command=self.cambiar_estado_cliente).pack(anchor="e", pady=(10, 0))
        self._refrescar_clientes()

    def registrar_cliente(self):
        datos = {clave: texto_o_none(caja.get()) for clave, caja in self.entradas_cliente.items()}

        def accion():
            if datos["identificacion"] in self.clientes:
                raise ErrorSistema(f"Ya existe un cliente con identificación {datos['identificacion']}.",
                                   "CLI-DUP")
            cliente = Cliente(**datos)
            self.clientes[str(cliente.id)] = cliente
            return cliente

        cliente = self._ejecutar(accion)
        if cliente:
            self._refrescar_clientes()
            self._limpiar(self.entradas_cliente)
            self.entradas_cliente["identificacion"].focus_set()
            self.avisar(f"Cliente «{cliente.nombre}» registrado.")

    def cambiar_estado_cliente(self):
        id_cliente = self.tabla_clientes.seleccion()
        if not id_cliente:
            self.avisar("Seleccione un cliente de la lista.", "aviso")
            return
        cliente = self.clientes[id_cliente]
        nuevo = "INACTIVO" if cliente.estado == "ACTIVO" else "ACTIVO"
        if self._ejecutar(lambda: cliente.cambiar_estado(nuevo),
                          exito=f"Cliente «{cliente.nombre}» ahora está {nuevo}."):
            self._refrescar_clientes()

    def _refrescar_clientes(self):
        self.tabla_clientes.cargar(
            [(str(c.id), (c.id, c.nombre, c.correo, c.telefono, c.estado)) for c in self.clientes.values()],
            vacio="Aún no hay clientes.\nRegistre el primero con el formulario de la izquierda.")

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------
    def _crear_vista_servicios(self):
        cuerpo = self._pagina("servicios", "Servicios",
                              "Salas, alquiler de equipos y asesorías que se pueden reservar.")

        marco, formulario = self._tarjeta(cuerpo, "Nuevo servicio")
        marco.pack(side="left", fill="y", padx=(0, 16))

        ttk.Label(formulario, text="Tipo de servicio", style="Etiqueta.TLabel").pack(anchor="w")
        self.tipo_servicio = ttk.Combobox(formulario, state="readonly", values=list(CAMPOS_SERVICIO))
        self.tipo_servicio.current(0)
        self.tipo_servicio.pack(fill="x", pady=(2, 6))
        self.tipo_servicio.bind("<<ComboboxSelected>>", lambda e: self._dibujar_campos_servicio())

        comunes = ttk.Frame(formulario)
        comunes.pack(fill="x")
        self.entradas_servicio = self._formulario(comunes, [
            ("Nombre", "nombre"), ("Descripción", "descripcion"),
            ("Precio base", "precio_base", "Cargo fijo, en pesos")],
            ancho=26, al_enviar=self.crear_servicio)

        ttk.Separator(formulario).pack(fill="x", pady=12)
        self.marco_especificos = ttk.Frame(formulario)
        self.marco_especificos.pack(fill="x")
        self.entradas_especificas = {}
        self._dibujar_campos_servicio()

        ttk.Button(formulario, text="Crear servicio", style="Primario.TButton",
                   command=self.crear_servicio).pack(fill="x", pady=(18, 4))
        ttk.Button(formulario, text="Limpiar campos", command=self._limpiar_servicio).pack(fill="x")

        marco, lista = self._tarjeta(cuerpo, "Servicios creados")
        marco.pack(side="left", fill="both", expand=True)
        self.tabla_servicios = Tabla(lista, [
            ("Código", 80), ("Tipo", 150), ("Nombre", 160), ("Costo", 110), ("Estado", 120)])
        self.tabla_servicios.pack(fill="both", expand=True)
        self.tabla_servicios.arbol.bind("<<TreeviewSelect>>", self._mostrar_detalle_servicio)
        self.tabla_servicios.menu_contextual([("Disponible / No disponible", self.cambiar_estado_servicio)])

        detalle = tk.Frame(lista, bg=COLORES["cebra"], highlightthickness=1,
                           highlightbackground=COLORES["borde"])
        detalle.pack(fill="x", pady=(10, 0))
        self.detalle_servicio = tk.Label(detalle, text="Seleccione un servicio para ver su detalle.",
                                         bg=COLORES["cebra"], fg=COLORES["suave"], justify="left",
                                         anchor="w", wraplength=560, font=(self.fuente, 10))
        self.detalle_servicio.pack(fill="x", padx=10, pady=8)

        ttk.Button(lista, text="Disponible / No disponible",
                   command=self.cambiar_estado_servicio).pack(anchor="e", pady=(10, 0))
        self._refrescar_servicios()

    def _dibujar_campos_servicio(self):
        for widget in self.marco_especificos.winfo_children():
            widget.destroy()
        _, campos = CAMPOS_SERVICIO[self.tipo_servicio.get()]
        self.entradas_especificas = self._formulario(self.marco_especificos, campos, ancho=26,
                                                     al_enviar=self.crear_servicio)
        # El tipo de asesoría se elige de una lista para evitar errores de escritura.
        if "tipo_asesoria" in self.entradas_especificas:
            caja = self.entradas_especificas["tipo_asesoria"]
            fila = caja.grid_info()["row"]
            caja.destroy()
            combo = ttk.Combobox(self.marco_especificos, state="readonly", width=24,
                                 values=AsesoriaEspecializada.TIPOS_ASESORIA)
            combo.current(0)
            combo.grid(row=fila, column=0, sticky="ew")
            self.entradas_especificas["tipo_asesoria"] = combo

    def _limpiar_servicio(self):
        self._limpiar(self.entradas_servicio)
        self._dibujar_campos_servicio()

    def crear_servicio(self):
        tipo = self.tipo_servicio.get()
        clase, campos = CAMPOS_SERVICIO[tipo]
        datos = {
            "nombre": texto_o_none(self.entradas_servicio["nombre"].get()),
            "descripcion": texto_o_none(self.entradas_servicio["descripcion"].get()),
            "precio_base": a_numero(self.entradas_servicio["precio_base"].get()),
        }
        for campo in campos:
            clave = campo[1]
            valor = self.entradas_especificas[clave].get()
            datos[clave] = texto_o_none(valor) if clave in CAMPOS_TEXTO else a_numero(valor)

        servicio = self._ejecutar(lambda: clase(**datos))
        if servicio:
            self.servicios[str(servicio.id)] = servicio
            self._refrescar_servicios()
            self._limpiar_servicio()
            self.tipo_servicio.set(tipo)
            self._dibujar_campos_servicio()
            self.entradas_servicio["nombre"].focus_set()
            self.avisar(f"Servicio «{servicio.nombre}» creado con código {servicio.id}. "
                        f"Costo: {pesos(servicio.calcular_costo())}")

    def cambiar_estado_servicio(self):
        codigo = self.tabla_servicios.seleccion()
        if not codigo:
            self.avisar("Seleccione un servicio de la lista.", "aviso")
            return
        servicio = self.servicios[codigo]
        nuevo = "NO_DISPONIBLE" if servicio.estado == "DISPONIBLE" else "DISPONIBLE"
        if self._ejecutar(lambda: servicio.cambiar_estado(nuevo),
                          exito=f"Servicio «{servicio.nombre}» ahora está {nuevo}."):
            self._refrescar_servicios()
            self._mostrar_detalle_servicio()

    def _mostrar_detalle_servicio(self, _evento=None):
        codigo = self.tabla_servicios.seleccion()
        if codigo and codigo in self.servicios:
            s = self.servicios[codigo]
            self.detalle_servicio.config(text=f"{s.descripcion}\n{s.describir_servicio()}",
                                         fg=COLORES["texto"])

    def _refrescar_servicios(self):
        filas = []
        for s in self.servicios.values():
            tipo = next((n for n, (c, _) in CAMPOS_SERVICIO.items() if isinstance(s, c)), "Servicio")
            filas.append((str(s.id), (s.id, tipo, s.nombre, pesos(s.calcular_costo()), s.estado)))
        self.tabla_servicios.cargar(
            filas, vacio="Aún no hay servicios.\nElija un tipo y complete el formulario de la izquierda.")

    # ------------------------------------------------------------------
    # Reservas
    # ------------------------------------------------------------------
    def _crear_vista_reservas(self):
        cuerpo = self._pagina("reservas", "Reservas",
                              "Una reserva une un cliente con un servicio en una fecha.")
        F = self.fuente

        izquierda = ttk.Frame(cuerpo, style="Fondo.TFrame")
        izquierda.pack(side="left", fill="y", padx=(0, 16))

        marco, formulario = self._tarjeta(izquierda, "Nueva reserva")
        marco.pack(fill="x")
        ttk.Label(formulario, text="Cliente", style="Etiqueta.TLabel").pack(anchor="w")
        self.combo_cliente = ttk.Combobox(formulario, state="readonly", width=26)
        self.combo_cliente.pack(fill="x", pady=(2, 0))
        self.combo_cliente.bind("<<ComboboxSelected>>", lambda e: self._revisar_seleccion_reserva())
        ttk.Label(formulario, text="Servicio", style="Etiqueta.TLabel").pack(anchor="w", pady=(10, 0))
        self.combo_servicio = ttk.Combobox(formulario, state="readonly", width=26)
        self.combo_servicio.pack(fill="x", pady=(2, 0))
        self.combo_servicio.bind("<<ComboboxSelected>>", lambda e: self._revisar_seleccion_reserva())
        self.aviso_reserva = tk.Label(formulario, text="", bg=COLORES["superficie"], fg=COLORES["aviso"],
                                      font=(F, 9), justify="left", anchor="w", wraplength=260)
        self.aviso_reserva.pack(fill="x", pady=(4, 0))

        ttk.Label(formulario, text="Fecha (AAAA-MM-DD)", style="Etiqueta.TLabel").pack(anchor="w", pady=(8, 0))
        fila_fecha = ttk.Frame(formulario)
        fila_fecha.pack(fill="x", pady=(2, 0))
        self.entrada_fecha = ttk.Entry(fila_fecha, width=12)
        self.entrada_fecha.insert(0, date.today().isoformat())
        self.entrada_fecha.pack(side="left", fill="x", expand=True)
        self.entrada_fecha.bind("<Return>", lambda e: self.registrar_reserva())
        ttk.Button(fila_fecha, text="Hoy", width=6,
                   command=lambda: self._poner_fecha(0)).pack(side="left", padx=(6, 0))
        ttk.Button(fila_fecha, text="Mañana", width=8,
                   command=lambda: self._poner_fecha(1)).pack(side="left", padx=(6, 0))
        ttk.Button(formulario, text="Registrar reserva", style="Primario.TButton",
                   command=self.registrar_reserva).pack(fill="x", pady=(18, 0))

        marco, confirmar = self._tarjeta(izquierda, "Al confirmar")
        marco.pack(fill="x", pady=(16, 0))
        self.con_iva = tk.BooleanVar(value=True)
        ttk.Checkbutton(confirmar, text="Incluir IVA", variable=self.con_iva).pack(anchor="w")
        ttk.Label(confirmar, text="Descuento (%)", style="Etiqueta.TLabel").pack(anchor="w", pady=(10, 2))
        self.entrada_descuento = ttk.Entry(confirmar)
        self.entrada_descuento.insert(0, "0")
        self.entrada_descuento.pack(fill="x")
        ttk.Label(confirmar, text="Se aplica sobre el costo de la reserva",
                  style="Pista.TLabel").pack(anchor="w")

        marco, lista = self._tarjeta(cuerpo, "Reservas registradas")
        marco.pack(side="left", fill="both", expand=True)
        self.tabla_reservas = Tabla(lista, [
            ("ID", 70), ("Cliente", 130), ("Servicio", 130), ("Duración", 90),
            ("Fecha", 95), ("Costo", 105), ("Estado", 100)])
        self.tabla_reservas.pack(fill="both", expand=True)
        self.tabla_reservas.arbol.bind("<<TreeviewSelect>>", lambda e: self._actualizar_botones_reserva())
        self.tabla_reservas.menu_contextual([("Confirmar", self.confirmar_reserva),
                                             ("Cancelar…", self.cancelar_reserva)])

        self.detalle_reserva = ttk.Label(lista, text="Seleccione una reserva para confirmarla o cancelarla.",
                                         style="Suave.TLabel", wraplength=560)
        self.detalle_reserva.pack(anchor="w", pady=(10, 0))
        botones = ttk.Frame(lista)
        botones.pack(fill="x", pady=(8, 0))
        self.boton_cancelar = ttk.Button(botones, text="✖  Cancelar", style="Peligro.TButton",
                                         command=self.cancelar_reserva)
        self.boton_cancelar.pack(side="right", padx=(8, 0))
        self.boton_confirmar = ttk.Button(botones, text="✔  Confirmar", style="Primario.TButton",
                                          command=self.confirmar_reserva)
        self.boton_confirmar.pack(side="right")
        self._refrescar_reservas()

    def _poner_fecha(self, dias):
        self.entrada_fecha.delete(0, "end")
        self.entrada_fecha.insert(0, (date.today() + timedelta(days=dias)).isoformat())

    def _actualizar_combos_reserva(self):
        self.combo_cliente["values"] = [f"{c.id} - {c.nombre} ({c.estado})" for c in self.clientes.values()]
        self.combo_servicio["values"] = [f"{s.id} - {s.nombre} ({s.estado})" for s in self.servicios.values()]
        # Si un elemento elegido cambió de estado, se actualiza el texto mostrado.
        for combo, datos in ((self.combo_cliente, self.clientes), (self.combo_servicio, self.servicios)):
            elegido = combo.get().split(" - ")[0]
            if elegido in datos:
                e = datos[elegido]
                combo.set(f"{e.id} - {e.nombre} ({e.estado})")
            elif combo.get():
                combo.set("")
        if not self.clientes or not self.servicios:
            faltan = " y ".join(n for n, d in (("clientes", self.clientes), ("servicios", self.servicios)) if not d)
            self.aviso_reserva.config(text=f"Primero registre {faltan} en su sección.")
        else:
            self._revisar_seleccion_reserva()

    def _revisar_seleccion_reserva(self):
        """Avisa antes de reservar si el cliente está inactivo o el servicio no disponible."""
        avisos = []
        cliente = self.clientes.get(self.combo_cliente.get().split(" - ")[0])
        servicio = self.servicios.get(self.combo_servicio.get().split(" - ")[0])
        if cliente and cliente.estado != "ACTIVO":
            avisos.append("Este cliente está INACTIVO y no podrá reservar.")
        if servicio and servicio.estado != "DISPONIBLE":
            avisos.append("Este servicio no está disponible.")
        self.aviso_reserva.config(text="\n".join(avisos))

    def registrar_reserva(self):
        if not self.combo_cliente.get() or not self.combo_servicio.get():
            self.avisar("Elija un cliente y un servicio antes de registrar la reserva.", "aviso")
            return
        cliente = self.clientes[self.combo_cliente.get().split(" - ")[0]]
        servicio = self.servicios[self.combo_servicio.get().split(" - ")[0]]
        fecha = texto_o_none(self.entrada_fecha.get())

        reserva = self._ejecutar(lambda: self.gestor_reservas.registrar_reserva(
            cliente, servicio, fecha_realizacion=fecha))
        if reserva:
            self._refrescar_reservas()
            self.tabla_reservas.arbol.selection_set(str(reserva.id))
            self.tabla_reservas.arbol.see(str(reserva.id))
            self.avisar(f"Reserva {reserva.id} registrada como PENDIENTE. "
                        f"Costo básico: {pesos(reserva.costo_total)}")

    def confirmar_reserva(self):
        id_reserva = self.tabla_reservas.seleccion()
        if not id_reserva:
            self.avisar("Seleccione una reserva de la lista.", "aviso")
            return
        descuento = a_numero(self.entrada_descuento.get()) or 0
        if self._ejecutar(lambda: self.gestor_reservas.confirmar_reserva(
                id_reserva, incluir_impuesto=self.con_iva.get(), descuento=descuento)):
            self._refrescar_reservas()
            reserva = self.gestor_reservas.buscar_reserva(id_reserva)
            self.avisar(f"Reserva {id_reserva} confirmada. Costo final: {pesos(reserva.costo_total)}")

    def cancelar_reserva(self):
        id_reserva = self.tabla_reservas.seleccion()
        if not id_reserva:
            self.avisar("Seleccione una reserva de la lista.", "aviso")
            return
        motivo = simpledialog.askstring("Cancelar reserva",
                                        f"Motivo de la cancelación de la reserva {id_reserva}:", parent=self)
        if motivo is None:
            return
        if self._ejecutar(lambda: self.gestor_reservas.cancelar_reserva(id_reserva, motivo or None),
                          exito=f"Reserva {id_reserva} cancelada."):
            self._refrescar_reservas()

    def _actualizar_botones_reserva(self):
        id_reserva = self.tabla_reservas.seleccion()
        reserva = self.gestor_reservas.buscar_reserva(id_reserva) if id_reserva else None
        if reserva is None:
            self.boton_confirmar.state(["disabled"])
            self.boton_cancelar.state(["disabled"])
            self.detalle_reserva.config(text="Seleccione una reserva para confirmarla o cancelarla.")
            return
        self.boton_confirmar.state(["!disabled"] if reserva.estado == "PENDIENTE" else ["disabled"])
        self.boton_cancelar.state(["!disabled"] if reserva.estado != "CANCELADA" else ["disabled"])
        self.detalle_reserva.config(
            text=f"{reserva.cliente.nombre} reservó «{reserva.servicio.nombre}» para el "
                 f"{reserva.fecha_realizacion}.")

    def _refrescar_reservas(self):
        self.tabla_reservas.cargar(
            [(str(r.id), (r.id, r.cliente.nombre, r.servicio.nombre, f"{r.duracion} {r.unidad_duracion}",
                          r.fecha_realizacion, pesos(r.costo_total), r.estado))
             for r in self.gestor_reservas.listar_reservas()],
            vacio="Aún no hay reservas.\nElija cliente, servicio y fecha en el formulario.")
        self._actualizar_botones_reserva()

    # ------------------------------------------------------------------
    # Registro de eventos (log)
    # ------------------------------------------------------------------
    def _crear_vista_registro(self):
        cuerpo = self._pagina("registro", "Registro de eventos",
                              "Contenido del archivo sistema.log: operaciones, cambios de estado y errores.")
        marco, interior = self._tarjeta(cuerpo)
        marco.pack(fill="both", expand=True)

        barra = ttk.Frame(interior)
        barra.pack(fill="x", pady=(0, 10))
        ttk.Label(barra, text="Nivel:", style="Suave.TLabel").pack(side="left")
        self.filtro_log = ttk.Combobox(barra, state="readonly", width=12,
                                       values=("TODOS", "INFO", "WARNING", "ERROR"))
        self.filtro_log.current(0)
        self.filtro_log.pack(side="left", padx=(6, 16))
        self.filtro_log.bind("<<ComboboxSelected>>", lambda e: self._cargar_log())
        ttk.Label(barra, text="Buscar:", style="Suave.TLabel").pack(side="left")
        self.buscar_log = tk.StringVar()
        ttk.Entry(barra, textvariable=self.buscar_log, width=28).pack(side="left", padx=6)
        self.buscar_log.trace_add("write", lambda *_: self._cargar_log())
        ttk.Button(barra, text="↻  Actualizar", command=self._cargar_log).pack(side="left", padx=(6, 0))
        self.contador_log = ttk.Label(barra, style="Suave.TLabel")
        self.contador_log.pack(side="right")

        marco_texto = ttk.Frame(interior)
        marco_texto.pack(fill="both", expand=True)
        familias = set(tkfont.families(self))
        mono = next((f for f in ("Consolas", "Menlo", "DejaVu Sans Mono") if f in familias), "Courier")
        self.texto_log = tk.Text(marco_texto, wrap="none", font=(mono, 9), bg=COLORES["cebra"],
                                 fg=COLORES["texto"], relief="flat", padx=10, pady=8,
                                 highlightthickness=1, highlightbackground=COLORES["borde"])
        barra_y = ttk.Scrollbar(marco_texto, orient="vertical", command=self.texto_log.yview)
        barra_x = ttk.Scrollbar(marco_texto, orient="horizontal", command=self.texto_log.xview)
        self.texto_log.configure(yscrollcommand=barra_y.set, xscrollcommand=barra_x.set)
        barra_y.pack(side="right", fill="y")
        barra_x.pack(side="bottom", fill="x")
        self.texto_log.pack(side="left", fill="both", expand=True)
        self.texto_log.tag_configure("ERROR", foreground=COLORES["error"])
        self.texto_log.tag_configure("WARNING", foreground=COLORES["aviso"])
        self.texto_log.tag_configure("coincidencia", background="#fff2b3")

    def _cargar_log(self):
        nivel = self.filtro_log.get()
        buscado = self.buscar_log.get().strip().lower()
        lineas = self.log.leer_registros(None if nivel == "TODOS" else nivel)
        if buscado:
            lineas = [l for l in lineas if buscado in l.lower()]

        self.texto_log.config(state="normal")
        self.texto_log.delete("1.0", "end")
        for linea in lineas:
            etiqueta = "ERROR" if "ERROR" in linea else "WARNING" if "WARNING" in linea else ""
            self.texto_log.insert("end", linea + "\n", etiqueta)
        if not lineas:
            self.texto_log.insert("end", "No hay eventos que coincidan con el filtro." if buscado or nivel != "TODOS"
                                  else "El registro está vacío.")
        if buscado:  # resalta el texto buscado
            inicio = "1.0"
            while True:
                pos = self.texto_log.search(buscado, inicio, "end", nocase=True)
                if not pos:
                    break
                fin = f"{pos}+{len(buscado)}c"
                self.texto_log.tag_add("coincidencia", pos, fin)
                inicio = fin
        self.texto_log.see("end")
        self.texto_log.config(state="disabled")
        self.contador_log.config(text=f"{len(lineas)} eventos")

    # ------------------------------------------------------------------
    # Ventana de ayuda
    # ------------------------------------------------------------------
    def mostrar_ayuda(self):
        if getattr(self, "_ventana_ayuda", None) and self._ventana_ayuda.winfo_exists():
            self._ventana_ayuda.lift()
            return
        C, F = COLORES, self.fuente
        ventana = tk.Toplevel(self, bg=C["fondo"])
        self._ventana_ayuda = ventana
        ventana.title("Ayuda - ¿Para qué sirve cada módulo?")
        ventana.geometry("800x460")
        ventana.transient(self)
        ventana.bind("<Escape>", lambda e: ventana.destroy())

        ttk.Label(ventana, text="Ayuda", style="TitPagina.TLabel").pack(anchor="w", padx=20, pady=(16, 0))
        ttk.Label(ventana, text="Elija un tema para ver su explicación.",
                  style="SubPagina.TLabel").pack(anchor="w", padx=20, pady=(0, 10))
        cuerpo = ttk.Frame(ventana, style="Fondo.TFrame", padding=(20, 0, 20, 12))
        cuerpo.pack(fill="both", expand=True)

        lista = tk.Listbox(cuerpo, width=32, font=(F, 10), activestyle="none", relief="flat",
                           highlightthickness=1, highlightbackground=C["borde"], bg=C["superficie"],
                           selectbackground=C["acento"], selectforeground="white", exportselection=False)
        for titulo in AYUDA:
            lista.insert("end", "  " + titulo)
        lista.pack(side="left", fill="y")

        texto = tk.Text(cuerpo, wrap="word", font=(F, 10), padx=16, pady=12, relief="flat",
                        bg=C["superficie"], fg=C["texto"], spacing2=2,
                        highlightthickness=1, highlightbackground=C["borde"])
        texto.pack(side="left", fill="both", expand=True, padx=(12, 0))
        texto.tag_configure("titulo", font=(F, 13, "bold"), foreground=C["lateral"])

        def mostrar(_evento=None):
            seleccion = lista.curselection()
            if not seleccion:
                return
            titulo = lista.get(seleccion[0]).strip()
            texto.config(state="normal")
            texto.delete("1.0", "end")
            texto.insert("end", titulo + "\n\n", "titulo")
            texto.insert("end", AYUDA[titulo])
            texto.config(state="disabled")

        lista.bind("<<ListboxSelect>>", mostrar)
        lista.selection_set(0)
        mostrar()
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(anchor="e", padx=20, pady=(0, 14))


if __name__ == "__main__":
    # Texto nítido en pantallas de alta resolución (Windows)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    AplicacionFJ().mainloop()