"""
Módulo: servicio.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 3 - Jerarquía y Polimorfismo de Servicios

Descripción:
    Define la clase abstracta ``Servicio``, que hereda de ``EntidadBase`` y es la
    clase padre de todos los servicios que ofrece Software FJ:

        EntidadBase (abstracta, Estudiante 1)
        └── Servicio (abstracta, este módulo)
            ├── ReservaSala            (reserva_sala.py)
            ├── AlquilerEquipo         (alquiler_equipo.py)
            └── AsesoriaEspecializada  (asesoria_especializada.py)

    ``Servicio`` reúne lo que todos los servicios tienen en común:

    * Código (es el ID heredado de EntidadBase), nombre, descripción y precio base.
    * Estado: DISPONIBLE o NO_DISPONIBLE (se cambia con ``cambiar_estado()``).
    * Validadores reutilizables de texto y números para que las subclases no
      repitan código.
    * ``calcular_costo_total()``: costo con impuestos y descuentos opcionales.

    Y obliga a cada servicio concreto a implementar:

    * ``calcular_costo()``       -> cuánto cuesta el servicio.
    * ``describir_servicio()``   -> texto con la información del servicio.
    * ``validar_parametros()``   -> reglas propias de sus datos.

    Al final del módulo está ``procesar_servicios()``, la función que demuestra
    el polimorfismo: recibe una lista con servicios de cualquier tipo y los
    trata a todos igual.

Ejemplo de uso:
    from reserva_sala import ReservaSala

    sala = ReservaSala("SAL-100", "Sala de juntas", "Sala con proyector", 20000,
                       nombre_sala="Sala Andes", horas=3, capacidad=12, costo_hora=50000)
    print(sala.calcular_costo())                    # 20000 + 3 * 50000 = 170000.0
    print(sala.calcular_costo_total(impuesto=0.19)) # 170000 * 1.19 = 202300.0
"""

# ABC y abstractmethod permiten declarar la clase y sus métodos como abstractos.
from abc import abstractmethod
# math.isfinite detecta valores imposibles como infinito o NaN en los cálculos.
import math

# Clase abstracta común del sistema (ID, estado, fechas, logs de cambios de estado).
from entidad_base import EntidadBase
# Excepciones personalizadas del sistema.
from excepciones import (CalculoInconsistenteError, DatosServicioInvalidos, ErrorSistema,
                         ParametroFaltante, ServicioNoDisponibleError)
# Gestor de logs compartido para registrar eventos y errores.
from gestor_logs import GestorLogs


class Servicio(EntidadBase):
    """
    Clase abstracta base de todos los servicios de Software FJ.

    No hace falta volver a heredar de ABC: EntidadBase ya es abstracta, así que
    Servicio también lo es mientras tenga métodos abstractos sin implementar.

    Atributos privados (solo accesibles mediante propiedades):
        __nombre (str): Nombre comercial del servicio.
        __descripcion (str): Descripción breve.
        __precio_base (float): Cargo fijo del servicio (se suma al costo variable).

    El código del servicio es el ID heredado de EntidadBase (propiedad ``codigo``).
    """

    # Estados de un servicio; el primero (DISPONIBLE) es el estado inicial.
    ESTADOS_PERMITIDOS = ("DISPONIBLE", "NO_DISPONIBLE")
    # Prefijo por defecto de los códigos automáticos (cada subclase define el suyo).
    PREFIJO_ID = "SER"
    # Tarifa de IVA en Colombia, usada como impuesto de referencia.
    IVA = 0.19
    # Longitudes mínimas de los textos comunes.
    MIN_NOMBRE = 3
    MIN_DESCRIPCION = 5

    def __init__(self, codigo=None, nombre=None, descripcion=None, precio_base=None, estado=None):
        """
        Inicializa los datos comunes a todos los servicios.

        Args:
            codigo (str, opcional): Código del servicio. Si es None se genera uno
                automático con el prefijo de la subclase (ej. SAL-0001).
            nombre (str): Nombre del servicio.
            descripcion (str): Descripción del servicio.
            precio_base (int | float): Cargo fijo, mayor o igual a cero.
            estado (str, opcional): DISPONIBLE (por defecto) o NO_DISPONIBLE.

        Raises:
            ParametroFaltante: Si nombre, descripción o precio base son None.
            DatosServicioInvalidos: Si algún dato no cumple su regla.
            IdentificadorInvalidoError, EstadoInvalidoError: Desde EntidadBase.
        """
        # EntidadBase se encarga del código (ID), el estado y las fechas.
        super().__init__(id_entidad=codigo, estado=estado)
        # Se valida y guarda cada dato común en su atributo privado.
        self.__nombre = self._validar_texto(nombre, "nombre", self.MIN_NOMBRE)
        # Descripción validada.
        self.__descripcion = self._validar_texto(descripcion, "descripcion", self.MIN_DESCRIPCION)
        # El precio base puede ser 0 (servicio sin cargo fijo), pero nunca negativo.
        self.__precio_base = self._validar_numero(precio_base, "precio_base", permitir_cero=True)

    # ------------------------------------------------------------------
    # Validadores reutilizables (los usan Servicio y TODAS sus subclases)
    # ------------------------------------------------------------------
    @classmethod
    def _validar_texto(cls, valor, campo, minimo=1):
        """
        Valida un dato de texto: obligatorio, de tipo str y con longitud mínima.

        Args:
            valor: Dato recibido.
            campo (str): Nombre del campo (para el mensaje de error).
            minimo (int): Cantidad mínima de caracteres.

        Returns:
            str: Texto sin espacios en los extremos ni espacios dobles internos.

        Raises:
            ParametroFaltante: Si el valor es None.
            DatosServicioInvalidos: Si no es texto o es demasiado corto.
        """
        # None significa que el dato no se entregó.
        if valor is None:
            # cls.__name__ indica la clase concreta (ReservaSala, AlquilerEquipo...).
            raise ParametroFaltante(campo, cls.__name__)
        # Solo se aceptan cadenas de texto.
        if not isinstance(valor, str):
            raise DatosServicioInvalidos(campo, valor, f"debe ser texto, se recibió {type(valor).__name__}")
        # Se quitan espacios de los extremos y espacios dobles internos.
        texto = " ".join(valor.split())
        # Se exige la longitud mínima (un texto vacío también cae aquí).
        if len(texto) < minimo:
            raise DatosServicioInvalidos(campo, valor, f"debe tener al menos {minimo} caracteres")
        # Se devuelve el texto limpio.
        return texto

    @classmethod
    def _validar_numero(cls, valor, campo, permitir_cero=False, maximo=None):
        """
        Valida un número decimal (precios, tarifas, horas).

        Si llega como texto (por ejemplo, leído con input()) se intenta convertir.

        Args:
            valor: Dato recibido (int, float o texto numérico).
            campo (str): Nombre del campo.
            permitir_cero (bool): True si el valor 0 es aceptable.
            maximo (float, opcional): Valor máximo permitido.

        Returns:
            float: El número validado.

        Raises:
            ParametroFaltante: Si el valor es None.
            DatosServicioInvalidos: Si no es numérico o está fuera de rango.
        """
        # None significa que el dato no se entregó.
        if valor is None:
            raise ParametroFaltante(campo, cls.__name__)
        # True/False son enteros en Python, pero no son una cantidad válida.
        if isinstance(valor, bool):
            raise DatosServicioInvalidos(campo, valor, "debe ser un número, no un valor lógico")
        # Se intenta convertir a float (acepta 5, 5.5 y "5.5").
        try:
            numero = float(valor)
        except (TypeError, ValueError) as error:
            # Encadenamiento: el error propio guarda como causa el error original de Python.
            raise DatosServicioInvalidos(campo, valor, "debe ser un número") from error
        # Se descartan infinito y NaN ("not a number").
        if not math.isfinite(numero):
            raise DatosServicioInvalidos(campo, valor, "debe ser un número finito")
        # Se verifica el límite inferior según se permita o no el cero.
        if numero < 0 or (numero == 0 and not permitir_cero):
            # Mensaje según el caso.
            regla = "no puede ser negativo" if permitir_cero else "debe ser mayor que cero"
            raise DatosServicioInvalidos(campo, valor, regla)
        # Se verifica el límite superior, si la subclase definió uno.
        if maximo is not None and numero > maximo:
            raise DatosServicioInvalidos(campo, valor, f"no puede ser mayor que {maximo}")
        # Se devuelve el número validado.
        return numero

    @classmethod
    def _validar_entero(cls, valor, campo, minimo=1, maximo=None):
        """
        Valida una cantidad entera (personas, equipos, días).

        Args:
            valor: Dato recibido (int o texto con un entero).
            campo (str): Nombre del campo.
            minimo (int): Valor mínimo permitido.
            maximo (int, opcional): Valor máximo permitido.

        Returns:
            int: El entero validado.

        Raises:
            ParametroFaltante: Si el valor es None.
            DatosServicioInvalidos: Si no es entero o está fuera de rango.
        """
        # Primero se reutiliza la validación numérica (None, tipo, finito, negativo).
        numero = cls._validar_numero(valor, campo, permitir_cero=(minimo <= 0))
        # Un número con decimales (ej. 2.5 equipos) no es una cantidad válida.
        if not numero.is_integer():
            raise DatosServicioInvalidos(campo, valor, "debe ser un número entero")
        # Se convierte a int para trabajar con cantidades exactas.
        entero = int(numero)
        # Se verifica el rango permitido.
        if entero < minimo or (maximo is not None and entero > maximo):
            # Se arma el texto del rango para el mensaje.
            rango = f"entre {minimo} y {maximo}" if maximo is not None else f"mayor o igual a {minimo}"
            raise DatosServicioInvalidos(campo, valor, f"debe estar {rango}")
        # Se devuelve el entero validado.
        return entero

    # ------------------------------------------------------------------
    # Propiedades (encapsulación)
    # ------------------------------------------------------------------
    @property
    def codigo(self):
        """str: Código del servicio. Es su ID, por eso no tiene setter."""
        # Se reutiliza el ID guardado por EntidadBase.
        return self.id

    @property
    def nombre(self):
        """str: Nombre del servicio (solo lectura)."""
        return self.__nombre

    @property
    def descripcion(self):
        """str: Descripción del servicio (solo lectura)."""
        return self.__descripcion

    @property
    def precio_base(self):
        """float: Cargo fijo del servicio."""
        return self.__precio_base

    @precio_base.setter
    def precio_base(self, nuevo_precio):
        """Setter: valida el nuevo precio antes de reemplazar el actual."""
        # Si la validación falla se lanza la excepción y se conserva el precio anterior.
        self.__precio_base = self._validar_numero(nuevo_precio, "precio_base", permitir_cero=True)
        # Se deja constancia del cambio en el log.
        GestorLogs.obtener_instancia().info(
            f"{self.tipo} {self.id}: nuevo precio base {self.__precio_base:,.2f}", origen=self.tipo)

    @property
    def esta_disponible(self):
        """bool: True si el servicio se puede usar (estado DISPONIBLE)."""
        return self.estado == "DISPONIBLE"

    # ------------------------------------------------------------------
    # Métodos abstractos propios de Servicio (contrato de las subclases)
    # ------------------------------------------------------------------
    @abstractmethod
    def calcular_costo(self):
        """
        Calcula el costo del servicio SIN impuestos ni descuentos.

        Returns:
            float: Costo del servicio.
        """

    @abstractmethod
    def describir_servicio(self):
        """
        Presenta la información del servicio.

        Returns:
            str: Texto descriptivo con los datos propios del servicio.
        """

    @abstractmethod
    def validar_parametros(self):
        """
        Comprueba los datos específicos del servicio (horas, capacidad, días...).

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """

    # ------------------------------------------------------------------
    # Implementación de los métodos abstractos de EntidadBase
    # ------------------------------------------------------------------
    def validar(self):
        """
        Valida el servicio completo: datos comunes + parámetros específicos.

        Los datos comunes se validan aquí UNA sola vez y los específicos se
        delegan en ``validar_parametros()``, que cada subclase sobrescribe.

        Raises:
            ParametroFaltante, DatosServicioInvalidos: Si algún dato no es válido.
        """
        # Datos comunes a todos los servicios.
        self._validar_texto(self.__nombre, "nombre", self.MIN_NOMBRE)
        self._validar_texto(self.__descripcion, "descripcion", self.MIN_DESCRIPCION)
        self._validar_numero(self.__precio_base, "precio_base", permitir_cero=True)
        # Datos propios: Python ejecuta la versión de la subclase real (polimorfismo).
        self.validar_parametros()

    def describir(self):
        """
        Implementa ``describir()`` de EntidadBase reutilizando ``describir_servicio()``.

        Así print(servicio) muestra la descripción propia de cada tipo de servicio.

        Returns:
            str: La descripción del servicio.
        """
        return self.describir_servicio()

    # ------------------------------------------------------------------
    # Comportamiento común (se hereda sin cambios)
    # ------------------------------------------------------------------
    def calcular_costo_total(self, impuesto=0.0, descuento=0.0):
        """
        Calcula el costo final con impuesto y descuento OPCIONALES.

        Python no tiene sobrecarga de métodos como Java; se simula con
        parámetros opcionales. Formas de llamarlo:

            servicio.calcular_costo_total()                          # Igual que calcular_costo().
            servicio.calcular_costo_total(impuesto=Servicio.IVA)     # Con IVA.
            servicio.calcular_costo_total(descuento=0.10)            # Con 10 % de descuento.
            servicio.calcular_costo_total(Servicio.IVA, 0.10)        # Con ambos.

        Primero se aplica el descuento y luego el impuesto.

        Args:
            impuesto (float): Tasa entre 0 y 1 (0.19 = 19 %).
            descuento (float): Tasa entre 0 y 1 (0.10 = 10 %). Debe ser menor que 1.

        Returns:
            float: Costo final redondeado a 2 decimales.

        Raises:
            DatosServicioInvalidos: Si las tasas están fuera de rango.
            CalculoInconsistenteError: Si el resultado no es un valor válido.
        """
        # Se validan las tasas reutilizando el validador numérico.
        tasa_impuesto = self._validar_numero(impuesto, "impuesto", permitir_cero=True, maximo=1)
        tasa_descuento = self._validar_numero(descuento, "descuento", permitir_cero=True, maximo=0.99)
        # calcular_costo() es abstracto: se ejecuta la versión de la subclase (polimorfismo).
        subtotal = self.calcular_costo()
        # Se aplica primero el descuento y luego el impuesto.
        total = subtotal * (1 - tasa_descuento) * (1 + tasa_impuesto)
        # Control de seguridad: un costo negativo o infinito indica un error de cálculo.
        if not math.isfinite(total) or total < 0:
            raise CalculoInconsistenteError(f"Costo inválido ({total}) para {self.tipo} {self.id}.")
        # Se redondea a 2 decimales (centavos).
        return round(total, 2)

    def verificar_disponibilidad(self):
        """
        Comprueba que el servicio se pueda usar.

        Raises:
            ServicioNoDisponibleError: Si el estado es NO_DISPONIBLE.
        """
        # Si no está disponible se lanza el error correspondiente.
        if not self.esta_disponible:
            raise ServicioNoDisponibleError(self.id, self.__nombre)

    def _registrar_creacion(self):
        """Deja constancia en el log de que el servicio se creó correctamente."""
        # Las subclases lo llaman al final de su __init__, cuando ya tienen todos sus datos.
        GestorLogs.obtener_instancia().info(f"Servicio creado: {self.describir_servicio()}",
                                            origen=self.tipo)

    def a_diccionario(self):
        """
        Extiende el diccionario de EntidadBase con los datos comunes del servicio.

        Returns:
            dict: Datos comunes más nombre, descripción, precio base y costo.
        """
        # Se obtienen id, tipo, estado y fechas desde EntidadBase.
        datos = super().a_diccionario()
        # Se agregan los datos comunes de todo servicio.
        datos.update({
            "nombre": self.__nombre,
            "descripcion": self.__descripcion,
            "precio_base": self.__precio_base,
            "costo": self.calcular_costo(),     # Polimórfico: cada subclase calcula el suyo.
        })
        # Se devuelve el diccionario.
        return datos


# ----------------------------------------------------------------------
# Demostración de polimorfismo
# ----------------------------------------------------------------------
def procesar_servicios(servicios, impuesto=0.0, descuento=0.0):
    """
    Procesa una lista de servicios de CUALQUIER tipo de la misma forma.

    Esta función no sabe (ni necesita saber) si recibe una ReservaSala, un
    AlquilerEquipo o una AsesoriaEspecializada: solo llama a los métodos que
    todo Servicio garantiza tener. Cada objeto responde con su propia versión.
    Eso es el polimorfismo.

    Un servicio con errores NO detiene el proceso: el error se registra en el
    log y se continúa con el siguiente.

    Args:
        servicios (list[Servicio]): Servicios a procesar.
        impuesto (float): Tasa de impuesto opcional (ej. Servicio.IVA).
        descuento (float): Tasa de descuento opcional.

    Returns:
        dict: {"procesados": [...], "errores": [...], "total": float}
            - procesados: lista de diccionarios con código, tipo, descripción y costos.
            - errores: lista de textos con los servicios rechazados y el motivo.
            - total: suma de los costos finales de los servicios procesados.
    """
    # Gestor de logs compartido.
    log = GestorLogs.obtener_instancia()
    # Resultados del proceso.
    procesados = []
    errores = []
    total = 0.0

    # Se recorre la lista tratando a todos los servicios por igual.
    for servicio in servicios:
        try:
            # Si llega algo que no es un Servicio, no tiene los métodos necesarios.
            if not isinstance(servicio, Servicio):
                raise TypeError(f"se esperaba un Servicio y se recibió {type(servicio).__name__}")
            # 1. Validaciones particulares: cada clase ejecuta su validar_parametros().
            servicio.validar()
            # 2. Disponibilidad (común a todos).
            servicio.verificar_disponibilidad()
            # 3. Costos: cada clase ejecuta su propio calcular_costo().
            costo = servicio.calcular_costo()
            costo_final = servicio.calcular_costo_total(impuesto, descuento)
        except (ErrorSistema, TypeError) as error:
            # Error controlado: se registra y se continúa con el siguiente servicio.
            codigo = getattr(servicio, "id", "?")
            log.error(f"Servicio {codigo} rechazado", error, origen="procesar_servicios")
            errores.append(f"{codigo}: {error}")
        else:
            # Solo si no hubo errores: 4. Descripción propia de cada clase.
            procesados.append({
                "codigo": servicio.id,
                "tipo": servicio.tipo,
                "descripcion": servicio.describir_servicio(),
                "costo": costo,
                "costo_final": costo_final,
            })
            # Se acumula el total.
            total += costo_final
        finally:
            # Se ejecuta SIEMPRE, haya error o no: deja rastro de cada servicio revisado.
            log.info(f"Revisión de servicio terminada ({len(procesados)} ok, {len(errores)} con error)",
                     origen="procesar_servicios")

    # Se devuelve el resumen del proceso.
    return {"procesados": procesados, "errores": errores, "total": round(total, 2)}
