"""
Módulo: reserva.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 4 - Módulo de Reservas y Métodos Sobrecargados

Descripción:
    Define la clase ``Reserva``, que une a un ``Cliente`` con un ``Servicio``
    (ReservaSala, AlquilerEquipo o AsesoriaEspecializada), y la clase
    ``GestorReservas``, que guarda las reservas y permite buscarlas por ID.

        EntidadBase (abstracta, Estudiante 1)
        └── Reserva (este módulo)
                ├── cliente  -> Cliente  (Estudiante 2)   [asociación]
                └── servicio -> Servicio (Estudiante 3)   [asociación]

    Ciclo de vida de una reserva (estados):

        PENDIENTE ──confirmar()──> CONFIRMADA
            │                          │
            └──────cancelar()──────────┴──> CANCELADA   (estado final)

    Manejo de errores:
    * try/except ............. validación de cliente, servicio, duración y fecha.
    * try/except/else ........ confirmar(): el else solo corre si todo salió bien.
    * try/except/finally ..... cancelar(): el finally registra el intento siempre.
    * raise ... from error ... confirmar() y cancelar() envuelven la causa original.

    Sobrecarga simulada de ``calcular_costo``:

        reserva.calcular_costo()                                  # 1. Costo básico.
        reserva.calcular_costo(incluir_impuesto=True)             # 2. Con IVA (19 %).
        reserva.calcular_costo(incluir_impuesto=True,
                               porcentaje_impuesto=8)             #    Con otro impuesto.
        reserva.calcular_costo(descuento=10)                      # 3. Con 10 % de descuento.
        reserva.calcular_costo(incluir_impuesto=True, descuento=10)  # 4. Ambos.

    Fórmula (primero el descuento, luego el impuesto):

        costo_final = costo_basico * (1 - descuento/100) * (1 + impuesto/100)

    donde costo_basico = servicio.calcular_costo() = precio base + duración * tarifa.
"""

# math.isfinite descarta infinito y NaN al validar números.
import math
# date y datetime para manejar la fecha de realización.
from datetime import date, datetime

# Clase raíz del sistema (ID automático, estados, fechas, logs de cambios de estado).
from entidad_base import EntidadBase
# Clases de los compañeros con las que se relaciona la reserva (no se modifican).
from cliente import Cliente
from servicio import Servicio
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
# Excepciones del sistema que pueden llegar desde Servicio.
from excepciones import CalculoInconsistenteError, ErrorValidacion, ServicioNoDisponibleError
# Excepciones propias del módulo de reservas.
from excepciones_reserva import (ErrorCancelacionReserva, ErrorConfirmacionReserva, EstadoReservaError,
                                 ReservaInvalidaError, ReservaNoEncontradaError)
# Gestor de logs compartido.
from gestor_logs import GestorLogs


class Reserva(EntidadBase):
    """
    Reserva de un servicio de Software FJ hecha por un cliente.

    Atributos heredados de EntidadBase:
        id (str): Identificador único automático (RES-0001, RES-0002...).
        estado (str): PENDIENTE, CONFIRMADA o CANCELADA.
        fecha_creacion (datetime): Momento en que se registró la reserva.

    Atributos privados propios (solo lectura mediante propiedades):
        __cliente (Cliente): Cliente que hace la reserva.
        __servicio (Servicio): Servicio reservado.
        __duracion (float): Duración reservada (horas o días, según el servicio).
        __unidad_duracion (str): "horas" o "días".
        __fecha_realizacion (date): Día en que se prestará el servicio.
        __costo_total (float): Costo de la reserva (básico al crearla, final al confirmarla).
    """

    # Estados de una reserva; el primero (PENDIENTE) es el estado inicial.
    ESTADOS_PERMITIDOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA")
    # Prefijo de los ID automáticos.
    PREFIJO_ID = "RES"
    # Cambios de estado permitidos: estado actual -> estados a los que puede pasar.
    TRANSICIONES = {
        "PENDIENTE": ("CONFIRMADA", "CANCELADA"),
        "CONFIRMADA": ("CANCELADA",),
        "CANCELADA": (),                       # Estado final: ya no cambia.
    }
    # IVA expresado en porcentaje (se toma de Servicio para no repetir el valor: 0.19 -> 19).
    IVA_PORCENTAJE = Servicio.IVA * 100
    # Formato aceptado para la fecha de realización cuando llega como texto.
    FORMATO_FECHA_REALIZACION = "%Y-%m-%d"

    def __init__(self, cliente=None, servicio=None, duracion=None, fecha_realizacion=None):
        """
        Registra una reserva nueva en estado PENDIENTE.

        Primero se validan todos los datos y solo después se llama a EntidadBase,
        así una reserva inválida no gasta un número de ID.

        Args:
            cliente (Cliente): Cliente ACTIVO que hace la reserva.
            servicio (Servicio): Servicio DISPONIBLE que se reserva.
            duracion (int | float, opcional): Duración en la unidad del servicio
                (horas para salas y asesorías, días para alquiler de equipos).
                Si es None se toma la duración del servicio; si se entrega, debe
                coincidir con ella.
            fecha_realizacion (date | str, opcional): Fecha "AAAA-MM-DD" en que se
                presta el servicio. Por defecto, hoy. No puede ser una fecha pasada.

        Raises:
            ReservaInvalidaError: Si algún dato no es válido.
        """
        # 1. Validaciones (si alguna falla, la reserva no se crea).
        cliente_valido = self._validar_cliente(cliente)
        servicio_valido = self._validar_servicio(servicio)
        duracion_valida, unidad = self._validar_duracion(duracion, servicio_valido)
        fecha_valida = self._validar_fecha(fecha_realizacion)
        # 2. EntidadBase asigna el ID automático, el estado PENDIENTE y las fechas.
        super().__init__()
        # 3. Se guardan los datos en atributos privados (encapsulamiento).
        self.__cliente = cliente_valido
        self.__servicio = servicio_valido
        self.__duracion = duracion_valida
        self.__unidad_duracion = unidad
        self.__fecha_realizacion = fecha_valida
        # 4. Costo inicial: el costo básico (sin impuestos ni descuentos).
        self.__costo_total = self.calcular_costo()
        # 5. Se deja constancia en el log.
        GestorLogs.obtener_instancia().info(f"Reserva registrada: {self.describir()}", origen="Reserva")

    # ------------------------------------------------------------------
    # Validaciones (try/except: se capturan errores concretos y se traducen)
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_cliente(cliente):
        """
        Comprueba que el cliente sea un objeto Cliente y que esté ACTIVO.

        Returns:
            Cliente: El mismo cliente, ya validado.

        Raises:
            ReservaInvalidaError: Si falta, no es un Cliente o está INACTIVO.
        """
        # El cliente es obligatorio.
        if cliente is None:
            raise ReservaInvalidaError("cliente", "es obligatorio")
        # Debe ser un objeto de la clase Cliente (no un texto con el nombre, por ejemplo).
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("cliente", f"debe ser un Cliente, se recibió {type(cliente).__name__}")
        # Un cliente inactivo no puede hacer reservas.
        if cliente.estado != "ACTIVO":
            raise ReservaInvalidaError("cliente", f"el cliente {cliente.identificacion} está {cliente.estado}")
        # Se devuelve el cliente validado.
        return cliente

    @staticmethod
    def _validar_servicio(servicio):
        """
        Comprueba que el servicio sea un Servicio con datos válidos y DISPONIBLE.

        Reutiliza ``validar()`` y ``verificar_disponibilidad()`` de la clase Servicio.

        Returns:
            Servicio: El mismo servicio, ya validado.

        Raises:
            ReservaInvalidaError: Si falta, no es un Servicio, tiene datos inválidos
                o no está disponible (la causa original queda en ``__cause__``).
        """
        # El servicio es obligatorio.
        if servicio is None:
            raise ReservaInvalidaError("servicio", "es obligatorio")
        # Debe ser un objeto de alguna subclase de Servicio.
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("servicio", f"debe ser un Servicio, se recibió {type(servicio).__name__}")
        try:
            # Validación propia del servicio (polimorfismo: cada subclase valida lo suyo).
            servicio.validar()
            # El servicio debe estar DISPONIBLE.
            servicio.verificar_disponibilidad()
        except ServicioNoDisponibleError as error:
            # Se traduce al error de la reserva conservando la causa original.
            # rstrip(".") evita el doble punto final en el mensaje.
            raise ReservaInvalidaError("servicio", error.mensaje.rstrip(".")) from error
        except ErrorValidacion as error:
            # Datos del servicio inválidos (ParametroFaltante, DatosServicioInvalidos).
            raise ReservaInvalidaError("servicio", f"datos inválidos: {error.mensaje.rstrip('.')}") from error
        # Se devuelve el servicio validado.
        return servicio

    @staticmethod
    def _duracion_del_servicio(servicio):
        """
        Obtiene la duración y la unidad que ya trae el servicio.

        Se usan las propiedades reales de cada clase del Estudiante 3:
        ReservaSala.horas, AsesoriaEspecializada.horas y AlquilerEquipo.dias.

        Returns:
            tuple: (duración, unidad). Si el tipo de servicio no se conoce: (None, "unidades").
        """
        # El alquiler de equipos se mide en días.
        if isinstance(servicio, AlquilerEquipo):
            return servicio.dias, "días"
        # La sala y la asesoría se miden en horas.
        if isinstance(servicio, (ReservaSala, AsesoriaEspecializada)):
            return servicio.horas, "horas"
        # Un servicio nuevo que aún no se conoce: la duración debe entregarse a mano.
        return None, "unidades"

    @classmethod
    def _validar_duracion(cls, duracion, servicio):
        """
        Valida la duración de la reserva.

        Args:
            duracion: Duración recibida (o None para tomar la del servicio).
            servicio (Servicio): Servicio ya validado.

        Returns:
            tuple: (duración como float, unidad).

        Raises:
            ReservaInvalidaError: Si no es numérica, es cero o negativa, o no
                coincide con la duración del servicio.
        """
        # Duración y unidad que ya tiene el servicio.
        esperada, unidad = cls._duracion_del_servicio(servicio)
        # Sin duración: se usa la del servicio (si se conoce).
        if duracion is None:
            if esperada is None:
                raise ReservaInvalidaError("duracion", "es obligatoria para este tipo de servicio")
            return float(esperada), unidad
        # True/False son enteros en Python, pero no son una duración.
        if isinstance(duracion, bool):
            raise ReservaInvalidaError("duracion", "debe ser un número, no un valor lógico")
        try:
            # Se acepta 3, 2.5 o "3".
            valor = float(duracion)
        except (TypeError, ValueError) as error:
            # Solo se capturan los errores de conversión, no cualquier excepción.
            raise ReservaInvalidaError("duracion", f"debe ser un número, se recibió {duracion!r}") from error
        # Se descartan infinito, NaN, cero y negativos.
        if not math.isfinite(valor) or valor <= 0:
            raise ReservaInvalidaError("duracion", f"debe ser mayor que cero, se recibió {duracion!r}")
        # Debe coincidir con la duración contratada en el servicio (de ella depende el costo).
        if esperada is not None and valor != esperada:
            raise ReservaInvalidaError("duracion",
                                       f"{valor:g} {unidad} no coincide con la del servicio ({esperada:g} {unidad})")
        return valor, unidad

    @classmethod
    def _validar_fecha(cls, fecha):
        """
        Valida la fecha de realización.

        Args:
            fecha (date | datetime | str | None): Fecha recibida.

        Returns:
            date: La fecha validada.

        Raises:
            ReservaInvalidaError: Si el formato es incorrecto o la fecha ya pasó.
        """
        # Sin fecha: se asume el día de hoy.
        if fecha is None:
            return date.today()
        # datetime es una subclase de date: se deja solo la parte de la fecha.
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        # Texto: se convierte con el formato AAAA-MM-DD.
        elif isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha.strip(), cls.FORMATO_FECHA_REALIZACION).date()
            except ValueError as error:
                raise ReservaInvalidaError("fecha_realizacion",
                                           f"{fecha!r} no tiene el formato AAAA-MM-DD") from error
        # Cualquier otro tipo no es una fecha.
        elif not isinstance(fecha, date):
            raise ReservaInvalidaError("fecha_realizacion", f"tipo no válido: {type(fecha).__name__}")
        # No se reserva para una fecha que ya pasó.
        if fecha < date.today():
            raise ReservaInvalidaError("fecha_realizacion", f"{fecha} es una fecha pasada")
        return fecha

    @staticmethod
    def _validar_porcentaje(valor, campo, maximo):
        """
        Valida un porcentaje (0 a ``maximo``) y lo convierte en tasa (0 a 1).

        Ejemplo: 19 -> 0.19, 10 -> 0.10.

        Raises:
            ReservaInvalidaError: Si no es un número o está fuera de rango.
        """
        # True/False no son porcentajes.
        if isinstance(valor, bool):
            raise ReservaInvalidaError(campo, "debe ser un número, no un valor lógico")
        try:
            numero = float(valor)
        except (TypeError, ValueError) as error:
            raise ReservaInvalidaError(campo, f"debe ser un número, se recibió {valor!r}") from error
        # Debe estar entre 0 y el máximo permitido.
        if not math.isfinite(numero) or not 0 <= numero <= maximo:
            raise ReservaInvalidaError(campo, f"debe estar entre 0 y {maximo}, se recibió {valor!r}")
        # Se convierte el porcentaje en tasa.
        return numero / 100

    # ------------------------------------------------------------------
    # Propiedades de solo lectura (encapsulamiento)
    # ------------------------------------------------------------------
    @property
    def cliente(self):
        """Cliente: Cliente que hizo la reserva."""
        return self.__cliente

    @property
    def servicio(self):
        """Servicio: Servicio reservado."""
        return self.__servicio

    @property
    def duracion(self):
        """float: Duración reservada."""
        return self.__duracion

    @property
    def unidad_duracion(self):
        """str: Unidad de la duración ("horas" o "días")."""
        return self.__unidad_duracion

    @property
    def fecha_realizacion(self):
        """date: Día en que se presta el servicio."""
        return self.__fecha_realizacion

    @property
    def costo_total(self):
        """float: Costo de la reserva (básico al crearla; final al confirmarla)."""
        return self.__costo_total

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def consultar_estado(self):
        """
        Returns:
            str: Estado actual (PENDIENTE, CONFIRMADA o CANCELADA).
        """
        return self.estado

    def consultar_datos(self):
        """
        Devuelve todos los datos de la reserva.

        Returns:
            dict: Datos de la reserva (ver ``a_diccionario``).
        """
        return self.a_diccionario()

    # ------------------------------------------------------------------
    # Sobrecarga simulada: calcular_costo con parámetros opcionales
    # ------------------------------------------------------------------
    def calcular_costo(self, incluir_impuesto=False, descuento=0, porcentaje_impuesto=IVA_PORCENTAJE):
        """
        Calcula el costo de la reserva. Una sola implementación cubre las 4 variantes.

        Python no admite varios métodos con el mismo nombre y distinta firma
        (si se definen dos, el segundo reemplaza al primero). Por eso la
        "sobrecarga" se simula con parámetros opcionales y valores por defecto:

            calcular_costo()                                   -> costo básico
            calcular_costo(incluir_impuesto=True)              -> con IVA 19 %
            calcular_costo(True, porcentaje_impuesto=8)        -> con impuesto configurable
            calcular_costo(descuento=10)                       -> con 10 % de descuento
            calcular_costo(incluir_impuesto=True, descuento=10)-> descuento + impuesto

        Fórmula (primero el descuento y después el impuesto, el mismo orden que
        usa Servicio.calcular_costo_total):

            costo_basico = servicio.calcular_costo()      (precio base + duración * tarifa)
            costo_final  = costo_basico * (1 - descuento/100) * (1 + impuesto/100)

        Args:
            incluir_impuesto (bool): True para sumar el impuesto.
            descuento (int | float): Porcentaje de descuento, de 0 a 99.
            porcentaje_impuesto (int | float): Porcentaje de impuesto, de 0 a 100
                (por defecto el IVA: 19). Solo se usa si incluir_impuesto es True.

        Returns:
            float: Costo redondeado a 2 decimales.

        Raises:
            ReservaInvalidaError: Si algún parámetro está fuera de rango o el
                servicio devuelve un costo inconsistente.
        """
        # incluir_impuesto debe ser un valor lógico (evita llamadas ambiguas como calcular_costo(19)).
        if not isinstance(incluir_impuesto, bool):
            raise ReservaInvalidaError("incluir_impuesto", "debe ser True o False")
        # Se validan los porcentajes y se convierten en tasas (10 -> 0.10).
        tasa_descuento = self._validar_porcentaje(descuento, "descuento", maximo=99)
        tasa_impuesto = self._validar_porcentaje(porcentaje_impuesto, "porcentaje_impuesto", maximo=100)
        # Si no se pidió impuesto, la tasa que se aplica es 0.
        if not incluir_impuesto:
            tasa_impuesto = 0.0
        try:
            # Se reutiliza el cálculo del Estudiante 3: costo del servicio * (1 - d) * (1 + i).
            return self.__servicio.calcular_costo_total(impuesto=tasa_impuesto, descuento=tasa_descuento)
        except CalculoInconsistenteError as error:
            raise ReservaInvalidaError("costo", "el servicio devolvió un costo inconsistente") from error

    # ------------------------------------------------------------------
    # Confirmación: try / except / else  +  encadenamiento
    # ------------------------------------------------------------------
    def confirmar(self, incluir_impuesto=True, descuento=0):
        """
        Confirma una reserva PENDIENTE y fija su costo final.

        * try:    se comprueba todo lo necesario y se cambia el estado.
        * except: se captura la causa concreta y se lanza ErrorConfirmacionReserva
                  con ``raise ... from error`` (encadenamiento).
        * else:   SOLO si no hubo errores: se guarda el costo final y se registra el éxito.

        Args:
            incluir_impuesto (bool): Si el costo final incluye IVA (por defecto sí).
            descuento (int | float): Porcentaje de descuento (por defecto 0).

        Returns:
            float: Costo final de la reserva confirmada.

        Raises:
            ErrorConfirmacionReserva: Si no se pudo confirmar. La causa original
                (EstadoReservaError, ServicioNoDisponibleError o ReservaInvalidaError)
                queda en ``__cause__``.
        """
        log = GestorLogs.obtener_instancia()
        try:
            # Solo una reserva PENDIENTE se puede confirmar.
            if self.estado != "PENDIENTE":
                raise EstadoReservaError(self.id, self.estado, "confirmar")
            # El servicio pudo dejar de estar disponible después de registrar la reserva.
            self.__servicio.verificar_disponibilidad()
            # El cliente pudo quedar INACTIVO después de registrar la reserva.
            self._validar_cliente(self.__cliente)
            # Se calcula el costo final ANTES de cambiar el estado (si falla, nada cambia).
            costo_final = self.calcular_costo(incluir_impuesto=incluir_impuesto, descuento=descuento)
            # Cambio de estado (método heredado: valida la transición y deja log).
            self.cambiar_estado("CONFIRMADA", motivo="confirmación de la reserva")
        except (EstadoReservaError, ServicioNoDisponibleError, ReservaInvalidaError) as error:
            # Se registra el error original y se lanza el error de confirmación encadenado.
            log.error(f"Falló la confirmación de la reserva {self.id}", error, origen="Reserva")
            raise ErrorConfirmacionReserva(self.id, error.mensaje) from error
        else:
            # Este bloque solo se ejecuta si el try terminó sin excepciones.
            self.__costo_total = costo_final
            log.info(f"Reserva {self.id} confirmada. Costo final ${costo_final:,.2f}", origen="Reserva")
            return costo_final

    # ------------------------------------------------------------------
    # Cancelación: try / except / finally  +  encadenamiento
    # ------------------------------------------------------------------
    def cancelar(self, motivo=None):
        """
        Cancela una reserva PENDIENTE o CONFIRMADA.

        * try:     se verifica el estado y se cambia a CANCELADA.
        * except:  se lanza ErrorCancelacionReserva encadenado a la causa original.
        * finally: se ejecuta SIEMPRE (con o sin error) y registra el intento en el log.

        Args:
            motivo (str, opcional): Razón de la cancelación.

        Returns:
            str: El estado que tenía la reserva antes de cancelarse.

        Raises:
            ErrorCancelacionReserva: Si la reserva ya estaba cancelada
                (la causa EstadoReservaError queda en ``__cause__``).
        """
        log = GestorLogs.obtener_instancia()
        # Se guardan los datos de seguimiento antes de intentar la operación.
        estado_inicial = self.estado
        cancelada = False
        try:
            # Una reserva cancelada no se puede volver a cancelar.
            if self.estado == "CANCELADA":
                raise EstadoReservaError(self.id, self.estado, "cancelar")
            # Cambio de estado (método heredado).
            self.cambiar_estado("CANCELADA", motivo=motivo or "cancelación solicitada")
            cancelada = True
        except EstadoReservaError as error:
            # Se conserva la causa original con "from error".
            raise ErrorCancelacionReserva(self.id, error.mensaje) from error
        finally:
            # Se ejecuta siempre: tanto si se canceló como si se lanzó el error.
            resultado = "EXITOSA" if cancelada else "RECHAZADA"
            log.info(f"Seguimiento: cancelación de la reserva {self.id} (estado previo {estado_inicial}) "
                     f"-> {resultado}", origen="Reserva")
        return estado_inicial

    # ------------------------------------------------------------------
    # Sobrescritura de métodos de EntidadBase (polimorfismo)
    # ------------------------------------------------------------------
    def _validar_transicion(self, estado_actual, estado_nuevo):
        """
        Restringe los cambios de estado según ``TRANSICIONES``.

        Es una segunda barrera: aunque alguien llame directamente a
        ``cambiar_estado("CONFIRMADA")`` sobre una reserva cancelada, se impide.

        Raises:
            EstadoReservaError: Si la transición no está permitida.
        """
        if estado_nuevo not in self.TRANSICIONES[estado_actual]:
            raise EstadoReservaError(self.id, estado_actual, f"pasar a {estado_nuevo}")

    def validar(self):
        """
        Comprueba que los datos guardados de la reserva sigan siendo coherentes.

        Raises:
            ReservaInvalidaError: Si algún dato no es válido.
        """
        if not isinstance(self.__cliente, Cliente):
            raise ReservaInvalidaError("cliente", "no es un Cliente")
        if not isinstance(self.__servicio, Servicio):
            raise ReservaInvalidaError("servicio", "no es un Servicio")
        if self.__duracion <= 0:
            raise ReservaInvalidaError("duracion", "debe ser mayor que cero")

    def describir(self):
        """
        Returns:
            str: Resumen legible de la reserva.
        """
        return (f"Reserva {self.id} - {self.__cliente.nombre} [{self.__cliente.identificacion}] - "
                f"{self.__servicio.nombre} ({self.__servicio.codigo}) - "
                f"{self.__duracion:g} {self.__unidad_duracion} - {self.__fecha_realizacion} - "
                f"${self.__costo_total:,.2f} - {self.estado}")

    def a_diccionario(self):
        """
        Extiende el diccionario de EntidadBase con los datos de la reserva.

        Returns:
            dict: Datos comunes más cliente, servicio, duración, fecha y costo.
        """
        datos = super().a_diccionario()
        datos.update({
            "cliente": self.__cliente.identificacion,
            "nombre_cliente": self.__cliente.nombre,
            "servicio": self.__servicio.codigo,
            "nombre_servicio": self.__servicio.nombre,
            "tipo_servicio": self.__servicio.tipo,
            "duracion": self.__duracion,
            "unidad_duracion": self.__unidad_duracion,
            "fecha_realizacion": self.__fecha_realizacion.isoformat(),
            "costo_total": self.__costo_total,
        })
        return datos


class GestorReservas:
    """
    Guarda las reservas registradas y permite buscarlas, confirmarlas y cancelarlas por ID.

    Atributo privado:
        __reservas (dict): ID de la reserva -> objeto Reserva.
    """

    def __init__(self):
        """Crea un gestor sin reservas."""
        self.__reservas = {}

    def registrar_reserva(self, cliente, servicio, duracion=None, fecha_realizacion=None):
        """
        Crea una reserva y la guarda.

        Args:
            cliente, servicio, duracion, fecha_realizacion: Ver ``Reserva.__init__``.

        Returns:
            Reserva: La reserva registrada (estado PENDIENTE).

        Raises:
            ReservaInvalidaError: Si los datos no son válidos (también queda en el log).
        """
        try:
            reserva = Reserva(cliente, servicio, duracion, fecha_realizacion)
        except ReservaInvalidaError as error:
            # Se captura SOLO el error de reserva inválida: se registra y se informa al llamador.
            GestorLogs.obtener_instancia().error("No se pudo registrar la reserva", error, origen="GestorReservas")
            raise
        # Si no hubo error, se guarda la reserva usando su ID como clave.
        self.__reservas[reserva.id] = reserva
        return reserva

    def buscar_reserva(self, id_reserva):
        """
        Returns:
            Reserva: La reserva con ese ID.

        Raises:
            ReservaNoEncontradaError: Si el ID no está registrado.
        """
        if id_reserva not in self.__reservas:
            raise ReservaNoEncontradaError(id_reserva)
        return self.__reservas[id_reserva]

    def confirmar_reserva(self, id_reserva, incluir_impuesto=True, descuento=0):
        """Busca la reserva y la confirma (ver ``Reserva.confirmar``)."""
        return self.buscar_reserva(id_reserva).confirmar(incluir_impuesto, descuento)

    def cancelar_reserva(self, id_reserva, motivo=None):
        """Busca la reserva y la cancela (ver ``Reserva.cancelar``)."""
        return self.buscar_reserva(id_reserva).cancelar(motivo)

    def listar_reservas(self, estado=None):
        """
        Args:
            estado (str, opcional): Filtra por estado (PENDIENTE, CONFIRMADA, CANCELADA).

        Returns:
            list[Reserva]: Reservas registradas (filtradas si se indicó un estado).
        """
        if estado is None:
            return list(self.__reservas.values())
        return [reserva for reserva in self.__reservas.values() if reserva.estado == estado.upper()]

    def __len__(self):
        """Cantidad de reservas registradas (permite usar len(gestor))."""
        return len(self.__reservas)
