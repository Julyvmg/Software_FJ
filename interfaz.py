"""
Módulo: interfaz.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4

Descripción:
    Interfaz gráfica sencilla (Tkinter) para usar el sistema sin escribir código.
    Está organizada en pestañas, una por cada módulo principal:

    * Clientes  -> registrar clientes y activarlos / inactivarlos.
    * Servicios -> crear salas, alquileres de equipo y asesorías.
    * Reservas  -> reservar un servicio para un cliente, confirmarla o cancelarla.
    * Registro  -> ver el archivo sistema.log (eventos y errores).

    El botón "Ayuda" explica para qué sirve cada módulo.
    Todos los errores se muestran en una ventana de aviso y quedan en el log;
    la aplicación nunca se cierra por un dato mal escrito.

Ejecución:
    python interfaz.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

from cliente import Cliente
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
from reserva import GestorReservas
from excepciones import ErrorSistema
from gestor_logs import GestorLogs


# ----------------------------------------------------------------------
# Textos de ayuda: uno por módulo
# ----------------------------------------------------------------------
AYUDA = {
    "Cómo usar esta aplicación": (
        "Software FJ permite gestionar CLIENTES, SERVICIOS y RESERVAS.\n\n"
        "Orden recomendado:\n"
        "  1. Pestaña Clientes: registre al menos un cliente.\n"
        "  2. Pestaña Servicios: cree al menos un servicio.\n"
        "  3. Pestaña Reservas: elija cliente y servicio y registre la reserva.\n"
        "  4. Confirme o cancele la reserva.\n"
        "  5. Pestaña Registro: revise qué quedó guardado en el log.\n\n"
        "Si algún dato es incorrecto, aparecerá un mensaje explicando el error. "
        "Corríjalo y vuelva a intentar: el programa no se cierra."
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
        "La fecha se escribe como AAAA-MM-DD y no puede ser una fecha pasada."
    ),
    "Registro de eventos (gestor_logs.py)": (
        "Todo lo que pasa en el sistema (registros, cambios de estado y errores) "
        "se guarda en el archivo sistema.log.\n\n"
        "En esta pestaña puede leer ese archivo y filtrar por nivel:\n"
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

# Campos propios de cada tipo de servicio: (etiqueta, nombre del parámetro)
CAMPOS_SERVICIO = {
    "Reserva de sala": (ReservaSala, [
        ("Nombre de la sala", "nombre_sala"),
        ("Horas", "horas"),
        ("Capacidad (personas)", "capacidad"),
        ("Costo por hora", "costo_hora"),
    ]),
    "Alquiler de equipo": (AlquilerEquipo, [
        ("Tipo de equipo", "tipo_equipo"),
        ("Cantidad", "cantidad"),
        ("Días", "dias"),
        ("Tarifa diaria", "tarifa_diaria"),
    ]),
    "Asesoría especializada": (AsesoriaEspecializada, [
        ("Tipo de asesoría", "tipo_asesoria"),
        ("Especialista", "especialista"),
        ("Horas", "horas"),
        ("Tarifa por hora", "tarifa_hora"),
    ]),
}


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


class AplicacionFJ(tk.Tk):
    """Ventana principal de Software FJ."""

    def __init__(self):
        super().__init__()
        self.title("Software FJ - Gestión de Clientes, Servicios y Reservas")
        self.geometry("980x640")
        self.minsize(860, 560)

        self.log = GestorLogs.obtener_instancia()
        self.clientes = {}          # id -> Cliente
        self.servicios = {}         # código -> Servicio
        self.gestor_reservas = GestorReservas()

        self._configurar_estilos()
        self._crear_encabezado()

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._crear_pestana_clientes()
        self._crear_pestana_servicios()
        self._crear_pestana_reservas()
        self._crear_pestana_registro()
        self.pestanas.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

        self.log.info("Interfaz gráfica iniciada", origen="Interfaz")

    # ------------------------------------------------------------------
    # Apariencia general
    # ------------------------------------------------------------------
    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        self.configure(bg="#f4f6f8")
        estilo.configure(".", font=("Segoe UI", 10))
        estilo.configure("TNotebook.Tab", padding=(16, 6), font=("Segoe UI", 10, "bold"))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("Treeview", rowheight=24)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 16, "bold"),
                         background="#1f4e79", foreground="white")
        estilo.configure("Sub.TLabel", font=("Segoe UI", 10),
                         background="#1f4e79", foreground="#dbe7f3")
        estilo.configure("Accion.TButton", font=("Segoe UI", 10, "bold"))
        estilo.configure("Ayuda.TButton", font=("Segoe UI", 10, "bold"))

    def _crear_encabezado(self):
        barra = tk.Frame(self, bg="#1f4e79")
        barra.pack(fill="x", pady=(0, 10))
        textos = tk.Frame(barra, bg="#1f4e79")
        textos.pack(side="left", padx=16, pady=10)
        ttk.Label(textos, text="Software FJ", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(textos, text="Sistema de gestión de clientes, servicios y reservas",
                  style="Sub.TLabel").pack(anchor="w")
        ttk.Button(barra, text="❓  Ayuda", style="Ayuda.TButton",
                   command=self.mostrar_ayuda).pack(side="right", padx=16)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _ejecutar(self, accion, exito=None):
        """Ejecuta una acción mostrando cualquier error en pantalla (sin cerrar el programa)."""
        try:
            resultado = accion()
        except ErrorSistema as error:
            messagebox.showerror("Dato no válido", str(error), parent=self)
            return None
        except Exception as error:  # Error inesperado: se registra y se informa.
            self.log.error("Error inesperado en la interfaz", error, origen="Interfaz")
            messagebox.showerror("Error inesperado", f"{type(error).__name__}: {error}", parent=self)
            return None
        if exito:
            messagebox.showinfo("Listo", exito, parent=self)
        return resultado if resultado is not None else True

    @staticmethod
    def _formulario(padre, campos, ancho=30):
        """Crea etiquetas + cajas de texto en dos columnas y devuelve {clave: Entry}."""
        entradas = {}
        for fila, (etiqueta, clave) in enumerate(campos):
            ttk.Label(padre, text=etiqueta + ":").grid(row=fila, column=0, sticky="w", pady=3, padx=(0, 8))
            caja = ttk.Entry(padre, width=ancho)
            caja.grid(row=fila, column=1, sticky="ew", pady=3)
            entradas[clave] = caja
        padre.columnconfigure(1, weight=1)
        return entradas

    @staticmethod
    def _tabla(padre, columnas):
        """Crea una tabla (Treeview) con barra de desplazamiento."""
        marco = ttk.Frame(padre)
        tabla = ttk.Treeview(marco, columns=[c for c, _ in columnas], show="headings", selectmode="browse")
        for nombre, ancho in columnas:
            tabla.heading(nombre, text=nombre)
            tabla.column(nombre, width=ancho, anchor="w")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return marco, tabla

    @staticmethod
    def _seleccion(tabla):
        seleccion = tabla.selection()
        return seleccion[0] if seleccion else None

    @staticmethod
    def _limpiar(entradas):
        for caja in entradas.values():
            caja.delete(0, "end")

    def _al_cambiar_pestana(self, _evento=None):
        actual = self.pestanas.tab(self.pestanas.select(), "text")
        if "Reservas" in actual:
            self._actualizar_combos_reserva()
        elif "Registro" in actual:
            self._cargar_log()

    # ------------------------------------------------------------------
    # Pestaña 1: Clientes
    # ------------------------------------------------------------------
    def _crear_pestana_clientes(self):
        pestana = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(pestana, text="👤 Clientes")

        formulario = ttk.LabelFrame(pestana, text=" Nuevo cliente ", padding=10)
        formulario.pack(side="left", fill="y", padx=(0, 12))
        self.entradas_cliente = self._formulario(formulario, [
            ("Identificación", "identificacion"),
            ("Nombre completo", "nombre"),
            ("Correo", "correo"),
            ("Teléfono", "telefono"),
            ("Dirección", "direccion"),
        ], ancho=26)
        botones = ttk.Frame(formulario)
        botones.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky="ew")
        ttk.Button(botones, text="Registrar cliente", style="Accion.TButton",
                   command=self.registrar_cliente).pack(fill="x", pady=2)
        ttk.Button(botones, text="Limpiar campos",
                   command=lambda: self._limpiar(self.entradas_cliente)).pack(fill="x", pady=2)

        lista = ttk.LabelFrame(pestana, text=" Clientes registrados ", padding=10)
        lista.pack(side="left", fill="both", expand=True)
        marco, self.tabla_clientes = self._tabla(lista, [
            ("ID", 90), ("Nombre", 160), ("Correo", 170), ("Teléfono", 100), ("Estado", 80)])
        marco.pack(fill="both", expand=True)
        ttk.Button(lista, text="Activar / Inactivar seleccionado",
                   command=self.cambiar_estado_cliente).pack(anchor="e", pady=(8, 0))

    def registrar_cliente(self):
        datos = {clave: texto_o_none(caja.get()) for clave, caja in self.entradas_cliente.items()}

        def accion():
            if datos["identificacion"] in self.clientes:
                raise ErrorSistema(f"Ya existe un cliente con identificación {datos['identificacion']}.", "CLI-DUP")
            cliente = Cliente(**datos)
            self.clientes[cliente.id] = cliente
            return cliente

        cliente = self._ejecutar(accion)
        if cliente:
            self._refrescar_clientes()
            self._limpiar(self.entradas_cliente)
            messagebox.showinfo("Listo", f"Cliente '{cliente.nombre}' registrado.", parent=self)

    def cambiar_estado_cliente(self):
        id_cliente = self._seleccion(self.tabla_clientes)
        if not id_cliente:
            messagebox.showwarning("Atención", "Seleccione un cliente de la lista.", parent=self)
            return
        cliente = self.clientes[id_cliente]
        nuevo = "INACTIVO" if cliente.estado == "ACTIVO" else "ACTIVO"
        if self._ejecutar(lambda: cliente.cambiar_estado(nuevo)):
            self._refrescar_clientes()

    def _refrescar_clientes(self):
        self.tabla_clientes.delete(*self.tabla_clientes.get_children())
        for c in self.clientes.values():
            self.tabla_clientes.insert("", "end", iid=c.id,
                                       values=(c.id, c.nombre, c.correo, c.telefono, c.estado))

    # ------------------------------------------------------------------
    # Pestaña 2: Servicios
    # ------------------------------------------------------------------
    def _crear_pestana_servicios(self):
        pestana = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(pestana, text="🛠 Servicios")

        formulario = ttk.LabelFrame(pestana, text=" Nuevo servicio ", padding=10)
        formulario.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(formulario, text="Tipo de servicio:").pack(anchor="w")
        self.tipo_servicio = ttk.Combobox(formulario, state="readonly", values=list(CAMPOS_SERVICIO))
        self.tipo_servicio.current(0)
        self.tipo_servicio.pack(fill="x", pady=(2, 8))
        self.tipo_servicio.bind("<<ComboboxSelected>>", lambda e: self._dibujar_campos_servicio())

        comunes = ttk.Frame(formulario)
        comunes.pack(fill="x")
        self.entradas_servicio = self._formulario(comunes, [
            ("Nombre", "nombre"), ("Descripción", "descripcion"), ("Precio base", "precio_base")], ancho=24)

        ttk.Separator(formulario).pack(fill="x", pady=8)
        self.marco_especificos = ttk.Frame(formulario)
        self.marco_especificos.pack(fill="x")
        self.entradas_especificas = {}
        self._dibujar_campos_servicio()

        ttk.Button(formulario, text="Crear servicio", style="Accion.TButton",
                   command=self.crear_servicio).pack(fill="x", pady=(12, 2))
        ttk.Button(formulario, text="Limpiar campos", command=self._limpiar_servicio).pack(fill="x", pady=2)

        lista = ttk.LabelFrame(pestana, text=" Servicios creados ", padding=10)
        lista.pack(side="left", fill="both", expand=True)
        marco, self.tabla_servicios = self._tabla(lista, [
            ("Código", 80), ("Tipo", 140), ("Nombre", 140), ("Costo", 100), ("Estado", 110)])
        marco.pack(fill="both", expand=True)
        self.tabla_servicios.bind("<<TreeviewSelect>>", self._mostrar_detalle_servicio)
        self.detalle_servicio = ttk.Label(lista, text="Seleccione un servicio para ver su detalle.",
                                          wraplength=480, foreground="#555")
        self.detalle_servicio.pack(anchor="w", pady=(8, 0))
        ttk.Button(lista, text="Disponible / No disponible",
                   command=self.cambiar_estado_servicio).pack(anchor="e", pady=(8, 0))

    def _dibujar_campos_servicio(self):
        for widget in self.marco_especificos.winfo_children():
            widget.destroy()
        _, campos = CAMPOS_SERVICIO[self.tipo_servicio.get()]
        self.entradas_especificas = self._formulario(self.marco_especificos, campos, ancho=24)
        # El tipo de asesoría se elige de una lista para evitar errores de escritura.
        if "tipo_asesoria" in self.entradas_especificas:
            self.entradas_especificas["tipo_asesoria"].destroy()
            combo = ttk.Combobox(self.marco_especificos, state="readonly", width=22,
                                 values=AsesoriaEspecializada.TIPOS_ASESORIA)
            combo.current(0)
            combo.grid(row=0, column=1, sticky="ew", pady=3)
            self.entradas_especificas["tipo_asesoria"] = combo

    def _limpiar_servicio(self):
        self._limpiar(self.entradas_servicio)
        self._dibujar_campos_servicio()

    def crear_servicio(self):
        clase, campos = CAMPOS_SERVICIO[self.tipo_servicio.get()]
        datos = {
            "nombre": texto_o_none(self.entradas_servicio["nombre"].get()),
            "descripcion": texto_o_none(self.entradas_servicio["descripcion"].get()),
            "precio_base": a_numero(self.entradas_servicio["precio_base"].get()),
        }
        for _, clave in campos:
            valor = self.entradas_especificas[clave].get()
            datos[clave] = texto_o_none(valor) if clave in ("nombre_sala", "tipo_equipo",
                                                            "tipo_asesoria", "especialista") else a_numero(valor)

        servicio = self._ejecutar(lambda: clase(**datos))
        if servicio:
            self.servicios[servicio.id] = servicio
            self._refrescar_servicios()
            self._limpiar_servicio()
            messagebox.showinfo("Listo", f"Servicio '{servicio.nombre}' creado con código {servicio.id}.\n"
                                         f"Costo: {pesos(servicio.calcular_costo())}", parent=self)

    def cambiar_estado_servicio(self):
        codigo = self._seleccion(self.tabla_servicios)
        if not codigo:
            messagebox.showwarning("Atención", "Seleccione un servicio de la lista.", parent=self)
            return
        servicio = self.servicios[codigo]
        nuevo = "NO_DISPONIBLE" if servicio.estado == "DISPONIBLE" else "DISPONIBLE"
        if self._ejecutar(lambda: servicio.cambiar_estado(nuevo)):
            self._refrescar_servicios()

    def _mostrar_detalle_servicio(self, _evento=None):
        codigo = self._seleccion(self.tabla_servicios)
        if codigo:
            s = self.servicios[codigo]
            self.detalle_servicio.config(text=f"{s.descripcion}\n{s.describir_servicio()}")

    def _refrescar_servicios(self):
        self.tabla_servicios.delete(*self.tabla_servicios.get_children())
        for s in self.servicios.values():
            tipo = next(n for n, (c, _) in CAMPOS_SERVICIO.items() if isinstance(s, c))
            self.tabla_servicios.insert("", "end", iid=s.id,
                                        values=(s.id, tipo, s.nombre, pesos(s.calcular_costo()), s.estado))

    # ------------------------------------------------------------------
    # Pestaña 3: Reservas
    # ------------------------------------------------------------------
    def _crear_pestana_reservas(self):
        pestana = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(pestana, text="📅 Reservas")

        formulario = ttk.LabelFrame(pestana, text=" Nueva reserva ", padding=10)
        formulario.pack(side="left", fill="y", padx=(0, 12))

        ttk.Label(formulario, text="Cliente:").pack(anchor="w")
        self.combo_cliente = ttk.Combobox(formulario, state="readonly", width=32)
        self.combo_cliente.pack(fill="x", pady=(2, 8))
        ttk.Label(formulario, text="Servicio:").pack(anchor="w")
        self.combo_servicio = ttk.Combobox(formulario, state="readonly", width=32)
        self.combo_servicio.pack(fill="x", pady=(2, 8))
        ttk.Label(formulario, text="Fecha (AAAA-MM-DD):").pack(anchor="w")
        self.entrada_fecha = ttk.Entry(formulario)
        self.entrada_fecha.insert(0, date.today().isoformat())
        self.entrada_fecha.pack(fill="x", pady=(2, 8))
        ttk.Button(formulario, text="Registrar reserva", style="Accion.TButton",
                   command=self.registrar_reserva).pack(fill="x", pady=(4, 12))

        confirmar = ttk.LabelFrame(formulario, text=" Al confirmar ", padding=8)
        confirmar.pack(fill="x")
        self.con_iva = tk.BooleanVar(value=True)
        ttk.Checkbutton(confirmar, text="Incluir IVA", variable=self.con_iva).pack(anchor="w")
        ttk.Label(confirmar, text="Descuento (%):").pack(anchor="w", pady=(6, 0))
        self.entrada_descuento = ttk.Entry(confirmar)
        self.entrada_descuento.insert(0, "0")
        self.entrada_descuento.pack(fill="x")

        lista = ttk.LabelFrame(pestana, text=" Reservas registradas ", padding=10)
        lista.pack(side="left", fill="both", expand=True)
        marco, self.tabla_reservas = self._tabla(lista, [
            ("ID", 80), ("Cliente", 130), ("Servicio", 130), ("Duración", 80),
            ("Fecha", 90), ("Costo", 100), ("Estado", 95)])
        marco.pack(fill="both", expand=True)
        botones = ttk.Frame(lista)
        botones.pack(anchor="e", pady=(8, 0))
        ttk.Button(botones, text="✔ Confirmar seleccionada", command=self.confirmar_reserva).pack(side="left", padx=4)
        ttk.Button(botones, text="✖ Cancelar seleccionada", command=self.cancelar_reserva).pack(side="left", padx=4)

    def _actualizar_combos_reserva(self):
        self.combo_cliente["values"] = [f"{c.id} - {c.nombre} ({c.estado})" for c in self.clientes.values()]
        self.combo_servicio["values"] = [f"{s.id} - {s.nombre} ({s.estado})" for s in self.servicios.values()]

    def registrar_reserva(self):
        if not self.combo_cliente.get() or not self.combo_servicio.get():
            messagebox.showwarning("Atención", "Elija un cliente y un servicio.\n"
                                               "(Si la lista está vacía, primero regístrelos en sus pestañas.)",
                                   parent=self)
            return
        cliente = self.clientes[self.combo_cliente.get().split(" - ")[0]]
        servicio = self.servicios[self.combo_servicio.get().split(" - ")[0]]
        fecha = texto_o_none(self.entrada_fecha.get())

        reserva = self._ejecutar(lambda: self.gestor_reservas.registrar_reserva(
            cliente, servicio, fecha_realizacion=fecha))
        if reserva:
            self._refrescar_reservas()
            messagebox.showinfo("Listo", f"Reserva {reserva.id} registrada (PENDIENTE).\n"
                                         f"Costo básico: {pesos(reserva.costo_total)}", parent=self)

    def confirmar_reserva(self):
        id_reserva = self._seleccion(self.tabla_reservas)
        if not id_reserva:
            messagebox.showwarning("Atención", "Seleccione una reserva de la lista.", parent=self)
            return
        descuento = a_numero(self.entrada_descuento.get()) or 0
        if self._ejecutar(lambda: self.gestor_reservas.confirmar_reserva(
                id_reserva, incluir_impuesto=self.con_iva.get(), descuento=descuento)):
            self._refrescar_reservas()
            reserva = self.gestor_reservas.buscar_reserva(id_reserva)
            messagebox.showinfo("Listo", f"Reserva {id_reserva} confirmada.\n"
                                         f"Costo final: {pesos(reserva.costo_total)}", parent=self)

    def cancelar_reserva(self):
        id_reserva = self._seleccion(self.tabla_reservas)
        if not id_reserva:
            messagebox.showwarning("Atención", "Seleccione una reserva de la lista.", parent=self)
            return
        motivo = simpledialog.askstring("Cancelar reserva", "Motivo de la cancelación:", parent=self)
        if motivo is None:
            return
        if self._ejecutar(lambda: self.gestor_reservas.cancelar_reserva(id_reserva, motivo or None),
                          exito=f"Reserva {id_reserva} cancelada."):
            self._refrescar_reservas()

    def _refrescar_reservas(self):
        self.tabla_reservas.delete(*self.tabla_reservas.get_children())
        for r in self.gestor_reservas.listar_reservas():
            self.tabla_reservas.insert("", "end", iid=r.id, values=(
                r.id, r.cliente.nombre, r.servicio.nombre, f"{r.duracion} {r.unidad_duracion}",
                r.fecha_realizacion, pesos(r.costo_total), r.estado))

    # ------------------------------------------------------------------
    # Pestaña 4: Registro de eventos (log)
    # ------------------------------------------------------------------
    def _crear_pestana_registro(self):
        pestana = ttk.Frame(self.pestanas, padding=12)
        self.pestanas.add(pestana, text="📄 Registro")

        barra = ttk.Frame(pestana)
        barra.pack(fill="x", pady=(0, 8))
        ttk.Label(barra, text="Mostrar:").pack(side="left")
        self.filtro_log = ttk.Combobox(barra, state="readonly", width=12,
                                       values=("TODOS", "INFO", "WARNING", "ERROR"))
        self.filtro_log.current(0)
        self.filtro_log.pack(side="left", padx=6)
        self.filtro_log.bind("<<ComboboxSelected>>", lambda e: self._cargar_log())
        ttk.Button(barra, text="↻ Actualizar", command=self._cargar_log).pack(side="left")

        marco = ttk.Frame(pestana)
        marco.pack(fill="both", expand=True)
        self.texto_log = tk.Text(marco, wrap="none", font=("Consolas", 9), bg="#fbfbfb")
        barra_y = ttk.Scrollbar(marco, orient="vertical", command=self.texto_log.yview)
        self.texto_log.configure(yscrollcommand=barra_y.set)
        self.texto_log.pack(side="left", fill="both", expand=True)
        barra_y.pack(side="right", fill="y")
        self.texto_log.tag_configure("ERROR", foreground="#b00020")
        self.texto_log.tag_configure("WARNING", foreground="#b26a00")

    def _cargar_log(self):
        nivel = self.filtro_log.get()
        lineas = self.log.leer_registros(None if nivel == "TODOS" else nivel)
        self.texto_log.config(state="normal")
        self.texto_log.delete("1.0", "end")
        for linea in lineas:
            etiqueta = "ERROR" if "ERROR" in linea else "WARNING" if "WARNING" in linea else ""
            self.texto_log.insert("end", linea + "\n", etiqueta)
        self.texto_log.see("end")
        self.texto_log.config(state="disabled")

    # ------------------------------------------------------------------
    # Ventana de ayuda
    # ------------------------------------------------------------------
    def mostrar_ayuda(self):
        ventana = tk.Toplevel(self)
        ventana.title("Ayuda - ¿Para qué sirve cada módulo?")
        ventana.geometry("760x440")
        ventana.transient(self)

        ttk.Label(ventana, text="Elija un módulo para ver su explicación",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        cuerpo = ttk.Frame(ventana, padding=(12, 0, 12, 12))
        cuerpo.pack(fill="both", expand=True)

        lista = tk.Listbox(cuerpo, width=34, font=("Segoe UI", 10), activestyle="none",
                           selectbackground="#1f4e79", exportselection=False)
        for titulo in AYUDA:
            lista.insert("end", titulo)
        lista.pack(side="left", fill="y")

        texto = tk.Text(cuerpo, wrap="word", font=("Segoe UI", 10), padx=12, pady=10, bg="#fbfbfb")
        texto.pack(side="left", fill="both", expand=True, padx=(10, 0))
        texto.tag_configure("titulo", font=("Segoe UI", 12, "bold"), foreground="#1f4e79")

        def mostrar(_evento=None):
            seleccion = lista.curselection()
            if not seleccion:
                return
            titulo = lista.get(seleccion[0])
            texto.config(state="normal")
            texto.delete("1.0", "end")
            texto.insert("end", titulo + "\n\n", "titulo")
            texto.insert("end", AYUDA[titulo])
            texto.config(state="disabled")

        lista.bind("<<ListboxSelect>>", mostrar)
        lista.selection_set(0)
        mostrar()
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(anchor="e", padx=12, pady=(0, 10))


if __name__ == "__main__":
    AplicacionFJ().mainloop()
