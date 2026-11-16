"""
Módulo: alquiler_equipo.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 3 - Jerarquía y Polimorfismo de Servicios

Descripción:
    Define ``AlquilerEquipo``, servicio especializado que hereda de ``Servicio``.

    Datos propios:
    * Tipo de equipo (mínimo 3 caracteres): "Portátil", "Video beam"...
    * Cantidad de equipos: entero entre 1 y 50.
    * Días de alquiler: entero entre 1 y 30.
    * Tarifa diaria por equipo: número mayor que 0.

    Costo = precio base + cantidad * días * tarifa diaria.
"""

# Clase abstracta padre de todos los servicios.
from servicio import Servicio


class AlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos por días."""

    # Prefijo de los códigos automáticos (EQU-0001, EQU-0002...).
    PREFIJO_ID = "EQU"
    # Reglas del negocio para este servicio.
    MAX_CANTIDAD = 50
    MAX_DIAS = 30

    def __init__(self, codigo=None, nombre=None, descripcion=None, precio_base=None,
                 tipo_equipo=None, cantidad=None, dias=None, tarifa_diaria=None, estado=None):
        """
        Crea un alquiler de equipos validando todos sus datos.

        Args:
            codigo, nombre, descripcion, precio_base, estado: Datos comunes (ver Servicio).
            tipo_equipo (str): Tipo de equipo alquilado.
            cantidad (int): Número de equipos (1 a 50).
            dias (int): Días de alquiler (1 a 30).
            tarifa_diaria (int | float): Valor por equipo por día (> 0).

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        # HERENCIA: la clase padre se encarga de los datos comunes.
        super().__init__(codigo, nombre, descripcion, precio_base, estado)
        # Datos propios validados con los métodos heredados.
        self.__tipo_equipo = self._validar_texto(tipo_equipo, "tipo_equipo", 3)
        self.__cantidad = self._validar_entero(cantidad, "cantidad", 1, self.MAX_CANTIDAD)
        self.__dias = self._validar_entero(dias, "dias", 1, self.MAX_DIAS)
        self.__tarifa_diaria = self._validar_numero(tarifa_diaria, "tarifa_diaria")
        # Se registra la creación en el log.
        self._registrar_creacion()

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def tipo_equipo(self):
        """str: Tipo de equipo."""
        return self.__tipo_equipo

    @property
    def cantidad(self):
        """int: Número de equipos."""
        return self.__cantidad

    @property
    def dias(self):
        """int: Días de alquiler."""
        return self.__dias

    @property
    def tarifa_diaria(self):
        """float: Valor por equipo por día."""
        return self.__tarifa_diaria

    # ------------------------------------------------------------------
    # Sobrescritura de los métodos abstractos de Servicio
    # ------------------------------------------------------------------
    def calcular_costo(self):
        """
        Costo = precio base + cantidad de equipos * días * tarifa diaria.

        Returns:
            float: Costo redondeado a 2 decimales.
        """
        return round(self.precio_base + self.__cantidad * self.__dias * self.__tarifa_diaria, 2)

    def describir_servicio(self):
        """
        Returns:
            str: Texto con el equipo, cantidad, días, costo y estado.
        """
        return (f"[{self.codigo}] Alquiler de {self.__cantidad} x '{self.__tipo_equipo}' - {self.nombre}: "
                f"{self.__dias} día(s), ${self.__tarifa_diaria:,.0f}/día por equipo - "
                f"costo ${self.calcular_costo():,.2f} ({self.estado})")

    def validar_parametros(self):
        """
        Vuelve a validar los datos propios del alquiler.

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        self._validar_texto(self.__tipo_equipo, "tipo_equipo", 3)
        self._validar_entero(self.__cantidad, "cantidad", 1, self.MAX_CANTIDAD)
        self._validar_entero(self.__dias, "dias", 1, self.MAX_DIAS)
        self._validar_numero(self.__tarifa_diaria, "tarifa_diaria")

    def a_diccionario(self):
        """Extiende el diccionario de Servicio con los datos del alquiler."""
        datos = super().a_diccionario()
        datos.update({
            "tipo_equipo": self.__tipo_equipo,
            "cantidad": self.__cantidad,
            "dias": self.__dias,
            "tarifa_diaria": self.__tarifa_diaria,
        })
        return datos
