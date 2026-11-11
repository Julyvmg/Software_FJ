"""
Módulo: excepciones.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4

Descripción:
    Excepciones personalizadas del sistema. Todas heredan de ``ErrorSistema``,
    de modo que un solo ``except ErrorSistema`` captura cualquier error propio
    del programa sin ocultar los errores inesperados de Python.

    Jerarquía:
        ErrorSistema
        ├── ErrorValidacion
        │   ├── IdentificadorInvalidoError
<<<<<<< Updated upstream
        │   └── EstadoInvalidoError
        └── OperacionNoPermitidaError
=======
        │   ├── EstadoInvalidoError
        │   ├── ParametroFaltante          (dato obligatorio no entregado)
        │   ├── DatosClienteInvalidos      (dato de un cliente con formato incorrecto)
        │   └── DatosServicioInvalidos     (dato de un servicio con valor incorrecto)
        ├── OperacionNoPermitidaError
        ├── ServicioNoDisponibleError      (se intentó usar un servicio NO_DISPONIBLE)
        └── CalculoInconsistenteError      (el cálculo de un costo dio un resultado imposible)
>>>>>>> Stashed changes

    Cómo extenderla (para las clases Cliente, Servicio y Reserva):
        class ServicioNoDisponibleError(ErrorSistema):
            def __init__(self, nombre):
                super().__init__(f"El servicio '{nombre}' no está disponible.", codigo="SER-001")
"""


class ErrorSistema(Exception):
    """
    Excepción base de todos los errores controlados del sistema.

    Atributos:
        mensaje (str): Descripción del error para el usuario y el log.
        codigo (str): Código corto que identifica el tipo de error (ej. "VAL-001").
    """

    def __init__(self, mensaje, codigo="ERR-000"):
        """
        Crea la excepción con su mensaje y su código.

        Args:
            mensaje (str): Descripción del error.
            codigo (str): Código identificador del error.
        """
        # Se inicializa la clase Exception para que el mensaje aparezca en el traceback.
        super().__init__(mensaje)
        # Se guarda el mensaje como atributo para poder consultarlo sin formato.
        self.mensaje = mensaje
        # Se guarda el código para clasificar el error en el archivo de logs.
        self.codigo = codigo

    def __str__(self):
        """
        Texto del error con su código al inicio.

        Returns:
            str: Mensaje con la forma "[CÓDIGO] mensaje".
        """
        # Se antepone el código entre corchetes para identificar rápidamente el error.
        return f"[{self.codigo}] {self.mensaje}"


class ErrorValidacion(ErrorSistema):
    """Error producido cuando un dato no cumple las reglas del sistema."""

    def __init__(self, mensaje, campo=None, codigo="VAL-000"):
        """
        Crea el error de validación.

        Args:
            mensaje (str): Descripción del problema.
            campo (str, opcional): Nombre del campo que falló la validación.
            codigo (str): Código identificador del error.
        """
        # Se delega en ErrorSistema el almacenamiento del mensaje y el código.
        super().__init__(mensaje, codigo)
        # Se guarda el campo afectado para que la interfaz pueda resaltarlo.
        self.campo = campo


class IdentificadorInvalidoError(ErrorValidacion):
    """El identificador (ID) de una entidad está vacío o tiene un formato no permitido."""

    def __init__(self, valor, motivo):
        """
        Crea el error indicando el valor recibido y el motivo del rechazo.

        Args:
            valor: Identificador que se intentó usar.
            motivo (str): Explicación de por qué no es válido.
        """
        # Se construye un mensaje descriptivo y se fija el campo "id" y su código.
        super().__init__(f"Identificador inválido ({valor!r}): {motivo}.", campo="id", codigo="VAL-001")
        # Se conserva el valor rechazado para depuración.
        self.valor = valor


class EstadoInvalidoError(ErrorValidacion):
    """Se intentó asignar un estado que la entidad no admite."""

    def __init__(self, estado, permitidos):
        """
        Crea el error mostrando los estados que sí son válidos.

        Args:
            estado: Estado que se intentó asignar.
            permitidos (tuple[str]): Estados aceptados por la entidad.
        """
        # Se arma el mensaje listando los valores válidos separados por comas.
        super().__init__(f"Estado {estado!r} no permitido. Valores válidos: {', '.join(permitidos)}.",
                         campo="estado", codigo="VAL-002")
        # Se conserva el estado rechazado para depuración.
        self.estado = estado


class OperacionNoPermitidaError(ErrorSistema):
    """Se intentó realizar una acción que las reglas del sistema no permiten."""

    def __init__(self, mensaje):
        """
        Crea el error de operación no permitida.

        Args:
            mensaje (str): Descripción de la operación rechazada.
        """
        # Se reutiliza el constructor base con un código propio de operaciones.
        super().__init__(mensaje, codigo="OPE-001")
<<<<<<< Updated upstream
=======


class ParametroFaltante(ErrorValidacion):
    """
    No se entregó un dato obligatorio (su valor es None).

    Es general: la usa Cliente y también pueden usarla Servicio o Reserva.
    """

    def __init__(self, campo, entidad="Sistema"):
        """
        Crea el error indicando qué dato falta y en qué entidad.

        Args:
            campo (str): Nombre del dato obligatorio que no se entregó.
            entidad (str): Clase u operación que lo necesitaba (ej. "Cliente").
        """
        # Se arma un mensaje claro y se fija el campo afectado y su código.
        super().__init__(f"Falta el dato obligatorio '{campo}' en {entidad}.", campo=campo, codigo="VAL-003")
        # Se conserva la entidad para consultarla después si se necesita.
        self.entidad = entidad


class DatosClienteInvalidos(ErrorValidacion):
    """Un dato del cliente se entregó, pero no cumple las reglas de validación."""

    def __init__(self, campo, valor, motivo):
        """
        Crea el error con el campo, el valor rechazado y el motivo.

        Args:
            campo (str): Dato del cliente que falló (nombre, correo, telefono...).
            valor: Valor que se intentó asignar.
            motivo (str): Explicación de la regla que no se cumplió.
        """
        # Se construye un mensaje que dice qué campo falló, con qué valor y por qué.
        super().__init__(f"Dato de cliente inválido en '{campo}' ({valor!r}): {motivo}.",
                         campo=campo, codigo="CLI-001")
        # Se conserva el valor rechazado para depuración.
        self.valor = valor


# ----------------------------------------------------------------------
# Excepciones del módulo de Servicios (Estudiante 3)
# ----------------------------------------------------------------------
class ServicioNoDisponibleError(ErrorSistema):
    """Se intentó usar (cotizar o reservar) un servicio que no está disponible."""

    def __init__(self, codigo_servicio, nombre):
        """
        Crea el error indicando qué servicio no está disponible.

        Args:
            codigo_servicio (str): Código (ID) del servicio.
            nombre (str): Nombre del servicio.
        """
        # Se usa el código SER-001, tal como se propuso en el ejemplo de este módulo.
        super().__init__(f"El servicio '{nombre}' ({codigo_servicio}) no está disponible.", codigo="SER-001")
        # Se conserva el código del servicio para consultarlo después.
        self.codigo_servicio = codigo_servicio


class DatosServicioInvalidos(ErrorValidacion):
    """Un dato del servicio se entregó, pero no cumple las reglas de validación."""

    def __init__(self, campo, valor, motivo):
        """
        Crea el error con el campo, el valor rechazado y el motivo.

        Args:
            campo (str): Dato del servicio que falló (horas, capacidad, tarifa...).
            valor: Valor que se intentó asignar.
            motivo (str): Explicación de la regla que no se cumplió.
        """
        # Mismo formato que DatosClienteInvalidos para que los mensajes sean uniformes.
        super().__init__(f"Dato de servicio inválido en '{campo}' ({valor!r}): {motivo}.",
                         campo=campo, codigo="SER-002")
        # Se conserva el valor rechazado para depuración.
        self.valor = valor


class CalculoInconsistenteError(ErrorSistema):
    """El cálculo de un costo produjo un resultado imposible (negativo, infinito, etc.)."""

    def __init__(self, mensaje):
        """
        Crea el error de cálculo inconsistente.

        Args:
            mensaje (str): Descripción del cálculo que falló.
        """
        # Se reutiliza el constructor base con un código propio de cálculos.
        super().__init__(mensaje, codigo="SER-003")
>>>>>>> Stashed changes
