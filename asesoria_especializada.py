"""
Módulo: asesoria_especializada.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 3 - Jerarquía y Polimorfismo de Servicios

Descripción:
    Define ``AsesoriaEspecializada``, servicio especializado que hereda de ``Servicio``.

    Datos propios:
    * Tipo de asesoría: uno de TIPOS_ASESORIA (no distingue mayúsculas).
    * Nombre del especialista: mínimo 3 caracteres, solo letras y signos de nombre.
    * Cantidad de horas: número mayor que 0 y máximo 40.
    * Tarifa por hora: número mayor que 0.

    Costo = precio base + horas * tarifa por hora.
"""

# re permite validar que el nombre del especialista solo tenga letras.
import re

# Clase abstracta padre de todos los servicios.
from servicio import Servicio
# Excepción para datos de servicio inválidos.
from excepciones import DatosServicioInvalidos


class AsesoriaEspecializada(Servicio):
    """Servicio de asesoría especializada por horas."""

    # Prefijo de los códigos automáticos (ASE-0001, ASE-0002...).
    PREFIJO_ID = "ASE"
    # Tipos de asesoría que ofrece Software FJ.
    TIPOS_ASESORIA = ("SOFTWARE", "REDES", "SEGURIDAD", "BASES DE DATOS", "NUBE")
    # Reglas del negocio para este servicio.
    MAX_HORAS = 40
    # Nombre del especialista: letras (con tildes y ñ), espacios, apóstrofo, punto y guion.
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")

    def __init__(self, codigo=None, nombre=None, descripcion=None, precio_base=None,
                 tipo_asesoria=None, especialista=None, horas=None, tarifa_hora=None, estado=None):
        """
        Crea una asesoría validando todos sus datos.

        Args:
            codigo, nombre, descripcion, precio_base, estado: Datos comunes (ver Servicio).
            tipo_asesoria (str): Uno de TIPOS_ASESORIA.
            especialista (str): Nombre del especialista.
            horas (int | float): Horas de asesoría (0 < horas <= 40).
            tarifa_hora (int | float): Valor de cada hora (> 0).

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        # HERENCIA: la clase padre se encarga de los datos comunes.
        super().__init__(codigo, nombre, descripcion, precio_base, estado)
        # Datos propios: dos con validación especial de esta clase y dos con validadores heredados.
        self.__tipo_asesoria = self._validar_tipo(tipo_asesoria)
        self.__especialista = self._validar_especialista(especialista)
        self.__horas = self._validar_numero(horas, "horas", maximo=self.MAX_HORAS)
        self.__tarifa_hora = self._validar_numero(tarifa_hora, "tarifa_hora")
        # Se registra la creación en el log.
        self._registrar_creacion()

    # ------------------------------------------------------------------
    # Validaciones propias de esta clase
    # ------------------------------------------------------------------
    @classmethod
    def _validar_tipo(cls, tipo_asesoria):
        """
        Valida que el tipo de asesoría sea uno de los ofrecidos.

        Returns:
            str: Tipo en mayúsculas.

        Raises:
            ParametroFaltante, DatosServicioInvalidos.
        """
        # Validación común de texto (heredada) y normalización a mayúsculas.
        tipo = cls._validar_texto(tipo_asesoria, "tipo_asesoria").upper()
        # Debe pertenecer a la lista de tipos ofrecidos.
        if tipo not in cls.TIPOS_ASESORIA:
            raise DatosServicioInvalidos("tipo_asesoria", tipo_asesoria,
                                         f"valores válidos: {', '.join(cls.TIPOS_ASESORIA)}")
        return tipo

    @classmethod
    def _validar_especialista(cls, especialista):
        """
        Valida el nombre del especialista: mínimo 3 caracteres y sin números ni símbolos.

        Returns:
            str: Nombre limpio.

        Raises:
            ParametroFaltante, DatosServicioInvalidos.
        """
        # Validación común de texto (heredada).
        nombre = cls._validar_texto(especialista, "especialista", 3)
        # Solo se permiten letras y signos propios de un nombre.
        if not cls._PATRON_NOMBRE.match(nombre):
            raise DatosServicioInvalidos("especialista", especialista,
                                         "solo se permiten letras, espacios, ', . y -")
        return nombre

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def tipo_asesoria(self):
        """str: Tipo de asesoría."""
        return self.__tipo_asesoria

    @property
    def especialista(self):
        """str: Nombre del especialista."""
        return self.__especialista

    @property
    def horas(self):
        """float: Horas de asesoría."""
        return self.__horas

    @property
    def tarifa_hora(self):
        """float: Valor de cada hora."""
        return self.__tarifa_hora

    # ------------------------------------------------------------------
    # Sobrescritura de los métodos abstractos de Servicio
    # ------------------------------------------------------------------
    def calcular_costo(self):
        """
        Costo = precio base + horas de asesoría * tarifa por hora.

        Returns:
            float: Costo redondeado a 2 decimales.
        """
        return round(self.precio_base + self.__horas * self.__tarifa_hora, 2)

    def describir_servicio(self):
        """
        Returns:
            str: Texto con el tipo, especialista, horas, costo y estado.
        """
        return (f"[{self.codigo}] Asesoría en {self.__tipo_asesoria} - {self.nombre}: "
                f"{self.__horas:g} h con {self.__especialista}, ${self.__tarifa_hora:,.0f}/h - "
                f"costo ${self.calcular_costo():,.2f} ({self.estado})")

    def validar_parametros(self):
        """
        Vuelve a validar los datos propios de la asesoría.

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        self._validar_tipo(self.__tipo_asesoria)
        self._validar_especialista(self.__especialista)
        self._validar_numero(self.__horas, "horas", maximo=self.MAX_HORAS)
        self._validar_numero(self.__tarifa_hora, "tarifa_hora")

    def a_diccionario(self):
        """Extiende el diccionario de Servicio con los datos de la asesoría."""
        datos = super().a_diccionario()
        datos.update({
            "tipo_asesoria": self.__tipo_asesoria,
            "especialista": self.__especialista,
            "horas": self.__horas,
            "tarifa_hora": self.__tarifa_hora,
        })
        return datos
