"""
Módulo: excepciones.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Autora: July Matabanchoy

Descripción:
    Excepciones personalizadas del sistema. Todas heredan de ``ErrorSistema``,
    de modo que un solo ``except ErrorSistema`` captura cualquier error propio
    del programa sin ocultar los errores inesperados de Python.

    Jerarquía:
        ErrorSistema
        ├── ErrorValidacion
        │   ├── IdentificadorInvalidoError
        │   └── EstadoInvalidoError
        └── OperacionNoPermitidaError

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
