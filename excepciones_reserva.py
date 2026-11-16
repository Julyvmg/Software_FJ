"""
Módulo: excepciones_reserva.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 4 - Módulo de Reservas y Métodos Sobrecargados

Descripción:
    Excepciones personalizadas del módulo de reservas. Se ubican en un archivo
    propio para no modificar ``excepciones.py`` de los demás integrantes, pero
    heredan de su jerarquía, así un ``except ErrorSistema`` también las captura.

    Jerarquía (se agrega a la del sistema):
        ErrorSistema                         (excepciones.py)
        ├── ErrorValidacion                  (excepciones.py)
        │   └── ReservaInvalidaError         RES-001  datos de la reserva incorrectos
        ├── ReservaNoEncontradaError         RES-002  no existe una reserva con ese ID
        ├── EstadoReservaError               RES-003  el estado actual no permite la acción
        ├── ErrorConfirmacionReserva         RES-004  falló el proceso de confirmación
        └── ErrorCancelacionReserva          RES-005  falló el proceso de cancelación

    ErrorConfirmacionReserva y ErrorCancelacionReserva se lanzan con
    ``raise ... from error`` (encadenamiento): el error original queda guardado
    en el atributo ``__cause__``.
"""

# Clases base de la jerarquía de excepciones del sistema (no se modifican).
from excepciones import ErrorSistema, ErrorValidacion


class ReservaInvalidaError(ErrorValidacion):
    """Un dato de la reserva (cliente, servicio, duración, fecha, tasas) no es válido."""

    def __init__(self, campo, motivo):
        """
        Crea el error indicando el campo que falló y el motivo.

        Args:
            campo (str): Dato de la reserva que no cumplió la regla.
            motivo (str): Explicación del problema.
        """
        # Se reutiliza ErrorValidacion, que guarda mensaje, campo y código.
        super().__init__(f"Reserva inválida en '{campo}': {motivo}.", campo=campo, codigo="RES-001")


class ReservaNoEncontradaError(ErrorSistema):
    """Se buscó una reserva con un ID que no está registrado."""

    def __init__(self, id_reserva):
        """
        Args:
            id_reserva (str): Identificador buscado.
        """
        super().__init__(f"No existe una reserva con el ID {id_reserva!r}.", codigo="RES-002")
        # Se conserva el ID buscado para consultarlo después.
        self.id_reserva = id_reserva


class EstadoReservaError(ErrorSistema):
    """El estado actual de la reserva no permite la operación solicitada."""

    def __init__(self, id_reserva, estado_actual, operacion):
        """
        Args:
            id_reserva (str): ID de la reserva.
            estado_actual (str): Estado en que se encuentra la reserva.
            operacion (str): Acción que se intentó (ej. "confirmar").
        """
        super().__init__(f"No se puede {operacion} la reserva {id_reserva}: "
                         f"su estado actual es {estado_actual}.", codigo="RES-003")
        # Se guardan los datos para poder consultarlos en las pruebas o en el log.
        self.estado_actual = estado_actual
        self.operacion = operacion


class ErrorConfirmacionReserva(ErrorSistema):
    """Error general del proceso de confirmación (envuelve la causa original)."""

    def __init__(self, id_reserva, detalle):
        """
        Args:
            id_reserva (str): ID de la reserva que no se pudo confirmar.
            detalle (str): Resumen de lo que falló.
        """
        super().__init__(f"No fue posible confirmar la reserva {id_reserva}: {detalle}", codigo="RES-004")


class ErrorCancelacionReserva(ErrorSistema):
    """Error general del proceso de cancelación (envuelve la causa original)."""

    def __init__(self, id_reserva, detalle):
        """
        Args:
            id_reserva (str): ID de la reserva que no se pudo cancelar.
            detalle (str): Resumen de lo que falló.
        """
        super().__init__(f"No fue posible cancelar la reserva {id_reserva}: {detalle}", codigo="RES-005")
