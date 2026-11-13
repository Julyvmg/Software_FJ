"""
Módulo: entidad_base.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Autora: July Matabanchoy

Descripción:
    Define la clase abstracta ``EntidadBase``, raíz de todas las entidades del
    sistema (Cliente, Servicio y Reserva). Reúne lo que todas tienen en común:

    * Un identificador (ID) validado, de solo lectura, manual o automático.
    * Un estado controlado (solo valores permitidos por cada subclase).
    * Fechas de creación y de última modificación.
    * Comparación (==), hash y representación de texto uniformes.

    Y obliga a cada subclase a implementar ``validar()`` y ``describir()``.

Cómo debe heredar un compañero (ejemplo para Cliente):

    class Cliente(EntidadBase):
        ESTADOS_PERMITIDOS = ("ACTIVO", "INACTIVO")   # El primero es el estado inicial.
        PREFIJO_ID = "CLI"                            # Prefijo de los ID automáticos.

        def __init__(self, documento, nombre):
            super().__init__(id_entidad=documento)    # Inicializa ID, estado y fechas.
            self._nombre = nombre
            self.validar()                            # Valida los datos propios al final.

        def validar(self):
            if len(self._nombre.strip()) < 3:
                raise ErrorValidacion("Nombre demasiado corto", campo="nombre")

        def describir(self):
            return f"Cliente {self._nombre} [{self.id}] - {self.estado}"

Principios de POO aplicados:
    * Abstracción: define QUÉ debe hacer una entidad, no CÓMO.
    * Herencia: las subclases reutilizan ID, estado, fechas y comparación.
    * Polimorfismo: cada subclase implementa validar(), describir() y puede
      sobrescribir a_diccionario() y _validar_transicion().
    * Encapsulación: atributos protegidos expuestos solo mediante propiedades.
"""

# re permite validar el formato del identificador con una expresión regular.
import re
# ABC convierte la clase en abstracta y abstractmethod marca los métodos obligatorios.
from abc import ABC, abstractmethod
# datetime registra la fecha y hora de creación y de modificación.
from datetime import datetime

# Excepciones personalizadas que lanza esta clase.
from excepciones import EstadoInvalidoError, IdentificadorInvalidoError, OperacionNoPermitidaError
# Gestor de logs compartido para registrar los cambios de estado.
from gestor_logs import GestorLogs


class EntidadBase(ABC):
    """
    Clase abstracta base de todas las entidades de Software FJ.

    Atributos de clase (las subclases pueden sobrescribirlos):
        ESTADOS_PERMITIDOS (tuple[str]): Estados válidos; el primero es el inicial.
        PREFIJO_ID (str): Prefijo para los identificadores generados automáticamente.

    Atributos de instancia (protegidos):
        _id (str): Identificador único de la entidad.
        _estado (str): Estado actual de la entidad.
        _fecha_creacion (datetime): Momento de creación.
        _fecha_modificacion (datetime): Momento del último cambio de estado.
    """

    # Estados válidos por defecto; cada subclase define los suyos (ej. Reserva: PENDIENTE, CONFIRMADA...).
    ESTADOS_PERMITIDOS = ("ACTIVO", "INACTIVO")
    # Prefijo por defecto de los ID automáticos (ej. "ENT-0001").
    PREFIJO_ID = "ENT"
    # Formato de fecha usado al convertir la entidad en diccionario.
    FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
    # Patrón del ID: letras, números, guion o guion bajo, entre 1 y 30 caracteres.
    _PATRON_ID = re.compile(r"^[A-Za-z0-9_-]{1,30}$")
    # Contadores de ID automáticos, uno por cada subclase (clave: nombre de la clase).
    _contadores = {}

    def __init__(self, id_entidad=None, estado=None):
        """
        Inicializa los datos comunes de la entidad.

        Args:
            id_entidad (str, opcional): Identificador propio (ej. cédula del cliente).
                Si es None se genera uno automático con el prefijo de la clase.
            estado (str, opcional): Estado inicial. Si es None se usa el primero de
                ``ESTADOS_PERMITIDOS``.

        Raises:
            IdentificadorInvalidoError: Si el ID está vacío o tiene caracteres no permitidos.
            EstadoInvalidoError: Si el estado no pertenece a ``ESTADOS_PERMITIDOS``.
        """
        # Si no se entregó un ID se genera uno automático; si se entregó, se valida.
        self._id = self._generar_id() if id_entidad is None else self._validar_id(id_entidad)
        # Si no se entregó un estado se usa el inicial; si se entregó, se valida.
        self._estado = self.ESTADOS_PERMITIDOS[0] if estado is None else self._validar_estado(estado)
        # Se registra el momento exacto de creación.
        self._fecha_creacion = datetime.now()
        # Al crearse, la última modificación coincide con la creación.
        self._fecha_modificacion = self._fecha_creacion

    # ------------------------------------------------------------------
    # Validaciones comunes (métodos de clase: usan la configuración de cada subclase)
    # ------------------------------------------------------------------
    @classmethod
    def _generar_id(cls):
        """
        Genera un ID automático y consecutivo para la subclase que lo solicita.

        Cada subclase lleva su propio contador: CLI-0001, CLI-0002..., RES-0001...

        Returns:
            str: Identificador con la forma "PREFIJO-0001".
        """
        # Se obtiene el último número usado por esta subclase (0 si es la primera vez) y se suma uno.
        siguiente = EntidadBase._contadores.get(cls.__name__, 0) + 1
        # Se guarda el nuevo valor en el contador compartido.
        EntidadBase._contadores[cls.__name__] = siguiente
        # Se arma el ID con el prefijo de la subclase y el número con 4 dígitos.
        return f"{cls.PREFIJO_ID}-{siguiente:04d}"

    @classmethod
    def _validar_id(cls, id_entidad):
        """
        Comprueba que el ID no esté vacío y tenga un formato permitido.

        Args:
            id_entidad: Valor recibido como identificador.

        Returns:
            str: El ID convertido a texto y sin espacios externos.

        Raises:
            IdentificadorInvalidoError: Si el ID es vacío o no cumple el patrón.
        """
        # Se convierte a texto y se quitan los espacios de los extremos.
        texto = str(id_entidad).strip()
        # Un ID vacío no identifica a nadie.
        if not texto:
            # Se lanza el error personalizado con el motivo.
            raise IdentificadorInvalidoError(id_entidad, "no puede estar vacío")
        # Se comprueba que solo tenga caracteres permitidos y una longitud adecuada.
        if not cls._PATRON_ID.match(texto):
            # Se lanza el error explicando el formato esperado.
            raise IdentificadorInvalidoError(
                id_entidad, "solo se permiten letras, números, '-' y '_' (máximo 30 caracteres)")
        # Si pasó las validaciones, se devuelve el ID limpio.
        return texto

    @classmethod
    def _validar_estado(cls, estado):
        """
        Comprueba que el estado pertenezca a los permitidos por la subclase.

        Args:
            estado: Estado que se quiere asignar (no distingue mayúsculas).

        Returns:
            str: El estado normalizado en mayúsculas.

        Raises:
            EstadoInvalidoError: Si el estado no está en ``ESTADOS_PERMITIDOS``.
        """
        # Se normaliza a texto en mayúsculas y sin espacios para comparar de forma uniforme.
        normalizado = str(estado).strip().upper()
        # Se verifica que el estado esté entre los permitidos por esta clase.
        if normalizado not in cls.ESTADOS_PERMITIDOS:
            # Se lanza el error indicando cuáles son los valores válidos.
            raise EstadoInvalidoError(estado, cls.ESTADOS_PERMITIDOS)
        # Se devuelve el estado ya normalizado.
        return normalizado

    # ------------------------------------------------------------------
    # Propiedades de solo lectura (encapsulación)
    # ------------------------------------------------------------------
    @property
    def id(self):
        """str: Identificador único de la entidad (no se puede modificar)."""
        # Se expone el ID sin setter, por lo que nadie puede cambiarlo desde fuera.
        return self._id

    @property
    def estado(self):
        """str: Estado actual. Para cambiarlo se debe usar ``cambiar_estado()``."""
        # Se expone el estado en solo lectura para obligar a pasar por las validaciones.
        return self._estado

    @property
    def fecha_creacion(self):
        """datetime: Fecha y hora en que se creó la entidad."""
        # Se devuelve la fecha de creación (los datetime son inmutables).
        return self._fecha_creacion

    @property
    def fecha_modificacion(self):
        """datetime: Fecha y hora del último cambio de estado."""
        # Se devuelve la fecha de la última modificación.
        return self._fecha_modificacion

    @property
    def tipo(self):
        """str: Nombre de la clase concreta (Cliente, Servicio, Reserva...)."""
        # type(self) es la subclase real del objeto; __name__ es su nombre.
        return type(self).__name__

    # ------------------------------------------------------------------
    # Comportamiento común
    # ------------------------------------------------------------------
    def cambiar_estado(self, nuevo_estado, motivo=None):
        """
        Cambia el estado de la entidad validando el valor y la transición.

        El cambio queda registrado en el archivo de logs.

        Args:
            nuevo_estado (str): Estado de destino.
            motivo (str, opcional): Razón del cambio, se agrega al log.

        Returns:
            str: El estado anterior (útil para deshacer o informar).

        Raises:
            EstadoInvalidoError: Si el nuevo estado no es permitido.
            OperacionNoPermitidaError: Si la entidad ya está en ese estado o la
                transición no está permitida por la subclase.
        """
        # Primero se valida que el estado de destino exista para esta clase.
        nuevo = self._validar_estado(nuevo_estado)
        # No tiene sentido "cambiar" al mismo estado en que ya está.
        if nuevo == self._estado:
            # Se informa con un error de operación no permitida.
            raise OperacionNoPermitidaError(f"{self.tipo} {self._id} ya se encuentra en estado {nuevo}.")
        # Se consulta a la subclase si la transición es válida (por defecto todas lo son).
        self._validar_transicion(self._estado, nuevo)
        # Se guarda el estado actual antes de reemplazarlo.
        anterior = self._estado
        # Se asigna el nuevo estado.
        self._estado = nuevo
        # Se actualiza la fecha de la última modificación.
        self._fecha_modificacion = datetime.now()
        # Se arma el texto del motivo solo si se entregó uno.
        detalle = f" (motivo: {motivo})" if motivo else ""
        # Se deja constancia del cambio en el archivo de logs.
        GestorLogs.obtener_instancia().info(
            f"{self.tipo} {self._id}: estado {anterior} -> {nuevo}{detalle}", origen=self.tipo)
        # Se devuelve el estado anterior.
        return anterior

    def _validar_transicion(self, estado_actual, estado_nuevo):
        """
        Punto de extensión para que cada subclase restrinja los cambios de estado.

        Por defecto permite cualquier transición. Una Reserva, por ejemplo, puede
        sobrescribirlo para impedir pasar de CANCELADA a CONFIRMADA.

        Args:
            estado_actual (str): Estado que tiene la entidad.
            estado_nuevo (str): Estado al que se quiere pasar.

        Raises:
            OperacionNoPermitidaError: Lo lanzan las subclases si la transición no es válida.
        """
        # Implementación por defecto: no se impone ninguna restricción.
        return None

    def a_diccionario(self):
        """
        Devuelve los datos comunes de la entidad como diccionario.

        Las subclases deben extenderlo así::

            def a_diccionario(self):
                datos = super().a_diccionario()
                datos["nombre"] = self.nombre
                return datos

        Returns:
            dict: Claves id, tipo, estado, fecha_creacion y fecha_modificacion.
        """
        # Se construye y devuelve el diccionario con los datos comunes en formato de texto.
        return {
            "id": self._id,                                                          # Identificador.
            "tipo": self.tipo,                                                       # Clase concreta.
            "estado": self._estado,                                                  # Estado actual.
            "fecha_creacion": self._fecha_creacion.strftime(self.FORMATO_FECHA),         # Creación.
            "fecha_modificacion": self._fecha_modificacion.strftime(self.FORMATO_FECHA),  # Último cambio.
        }

    # ------------------------------------------------------------------
    # Métodos abstractos: contrato obligatorio para las subclases
    # ------------------------------------------------------------------
    @abstractmethod
    def validar(self):
        """
        Valida los datos propios de la subclase.

        Debe lanzar una excepción derivada de ``ErrorValidacion`` si algún dato
        no es válido. Se recomienda llamarlo al final del ``__init__`` de la subclase.

        Raises:
            ErrorValidacion: Si algún dato de la entidad no es válido.
        """
        # Método abstracto: cada subclase aporta su propia implementación.

    @abstractmethod
    def describir(self):
        """
        Devuelve una descripción legible de la entidad.

        Returns:
            str: Texto para mostrar al usuario o escribir en el log.
        """
        # Método abstracto: cada subclase decide cómo presentarse.

    # ------------------------------------------------------------------
    # Métodos especiales
    # ------------------------------------------------------------------
    def __eq__(self, otro):
        """
        Dos entidades son iguales si son del mismo tipo y tienen el mismo ID.

        Args:
            otro: Objeto con el que se compara.

        Returns:
            bool | NotImplemented: Resultado de la comparación.
        """
        # Si el otro objeto no es una entidad, se deja que Python resuelva la comparación.
        if not isinstance(otro, EntidadBase):
            # NotImplemented indica que esta clase no sabe compararse con ese tipo.
            return NotImplemented
        # Mismo tipo concreto y mismo ID: un Cliente "123" no es igual a un Servicio "123".
        return type(self) is type(otro) and self._id == otro._id

    def __hash__(self):
        """
        Hash coherente con ``__eq__`` para usar entidades en conjuntos y diccionarios.

        Returns:
            int: Valor hash calculado con el tipo y el ID.
        """
        # Se calcula el hash de la tupla (nombre de la clase, ID).
        return hash((type(self).__name__, self._id))

    def __str__(self):
        """
        Texto amigable de la entidad (lo usan print() y str()).

        Returns:
            str: El resultado de ``describir()``.
        """
        # Se delega en describir(), implementado por cada subclase.
        return self.describir()

    def __repr__(self):
        """
        Representación técnica para depuración.

        Returns:
            str: Texto con la forma Tipo(id='...', estado='...').
        """
        # Se muestran la clase, el ID y el estado actual.
        return f"{self.tipo}(id={self._id!r}, estado={self._estado!r})"
