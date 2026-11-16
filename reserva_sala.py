"""
Módulo: reserva_sala.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 3 - Jerarquía y Polimorfismo de Servicios

Descripción:
    Define ``ReservaSala``, servicio especializado que hereda de ``Servicio``.

    Datos propios:
    * Nombre de la sala (mínimo 3 caracteres).
    * Horas reservadas: número mayor que 0 y máximo 12 (se permiten medias horas: 1.5).
    * Capacidad de personas: entero entre 1 y 100.
    * Costo por hora: número mayor que 0.

    Costo = precio base + horas * costo por hora.

Nota:
    No confundir con la clase ``Reserva`` (otro integrante), que une un cliente
    con un servicio. ``ReservaSala`` es el SERVICIO de alquilar una sala.
"""

# Clase abstracta padre de todos los servicios.
from servicio import Servicio


class ReservaSala(Servicio):
    """Servicio de reserva de salas por horas."""

    # Prefijo de los códigos automáticos (SAL-0001, SAL-0002...).
    PREFIJO_ID = "SAL"
    # Reglas del negocio para este servicio.
    MAX_HORAS = 12
    MAX_CAPACIDAD = 100

    def __init__(self, codigo=None, nombre=None, descripcion=None, precio_base=None,
                 nombre_sala=None, horas=None, capacidad=None, costo_hora=None, estado=None):
        """
        Crea una reserva de sala validando todos sus datos.

        Args:
            codigo, nombre, descripcion, precio_base, estado: Datos comunes (ver Servicio).
            nombre_sala (str): Nombre de la sala.
            horas (int | float): Horas reservadas (0 < horas <= 12).
            capacidad (int): Cantidad de personas (1 a 100).
            costo_hora (int | float): Valor de cada hora (> 0).

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        # HERENCIA: la clase padre inicializa y valida código, nombre, descripción, precio y estado.
        super().__init__(codigo, nombre, descripcion, precio_base, estado)
        # Datos propios, validados con los métodos heredados de Servicio (reutilización).
        self.__nombre_sala = self._validar_texto(nombre_sala, "nombre_sala", 3)
        self.__horas = self._validar_numero(horas, "horas", maximo=self.MAX_HORAS)
        self.__capacidad = self._validar_entero(capacidad, "capacidad", 1, self.MAX_CAPACIDAD)
        self.__costo_hora = self._validar_numero(costo_hora, "costo_hora")
        # Se registra la creación en el log (método heredado).
        self._registrar_creacion()

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def nombre_sala(self):
        """str: Nombre de la sala."""
        return self.__nombre_sala

    @property
    def horas(self):
        """float: Horas reservadas."""
        return self.__horas

    @property
    def capacidad(self):
        """int: Capacidad de personas."""
        return self.__capacidad

    @property
    def costo_hora(self):
        """float: Valor de cada hora."""
        return self.__costo_hora

    # ------------------------------------------------------------------
    # Sobrescritura de los métodos abstractos de Servicio
    # ------------------------------------------------------------------
    def calcular_costo(self):
        """
        Costo = precio base + horas reservadas * costo por hora.

        Returns:
            float: Costo redondeado a 2 decimales.
        """
        return round(self.precio_base + self.__horas * self.__costo_hora, 2)

    def describir_servicio(self):
        """
        Returns:
            str: Texto con la sala, horas, capacidad, costo y estado.
        """
        return (f"[{self.codigo}] Reserva de sala '{self.__nombre_sala}' - {self.nombre}: "
                f"{self.__horas:g} h para {self.__capacidad} personas, "
                f"${self.__costo_hora:,.0f}/h - costo ${self.calcular_costo():,.2f} ({self.estado})")

    def validar_parametros(self):
        """
        Vuelve a validar los datos propios de la sala con las mismas reglas del constructor.

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        self._validar_texto(self.__nombre_sala, "nombre_sala", 3)
        self._validar_numero(self.__horas, "horas", maximo=self.MAX_HORAS)
        self._validar_entero(self.__capacidad, "capacidad", 1, self.MAX_CAPACIDAD)
        self._validar_numero(self.__costo_hora, "costo_hora")

    def a_diccionario(self):
        """Extiende el diccionario de Servicio con los datos de la sala."""
        datos = super().a_diccionario()
        datos.update({
            "nombre_sala": self.__nombre_sala,
            "horas": self.__horas,
            "capacidad": self.__capacidad,
            "costo_hora": self.__costo_hora,
        })
        return datos
