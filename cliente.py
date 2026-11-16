"""
Módulo: cliente.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 2 - Módulo de Gestión de Clientes

Descripción:
    Define la clase ``Cliente``, que hereda de ``EntidadBase`` y guarda los datos
    personales de un cliente de Software FJ con encapsulación y validaciones
    estrictas:

    * Identificación: obligatoria, solo dígitos, entre 6 y 12 caracteres.
      Es el ID de la entidad, por lo que NO se puede modificar después.
    * Nombre completo: obligatorio, solo letras, espacios, tildes, ', . y -.
    * Correo electrónico: obligatorio, formato usuario@dominio.ext.
    * Teléfono: obligatorio, solo dígitos, espacios, +, -, ( y ), con 7 a 15 dígitos.
    * Dirección: obligatoria, al menos 5 caracteres.

    Reglas comunes a todos los textos:
    * Si el dato es None -> ParametroFaltante.
    * Si no es texto, está vacío o tiene un formato incorrecto -> DatosClienteInvalidos.
    * Se quitan los espacios del inicio y del final (y los dobles espacios internos).

Ejemplo de uso:
    from cliente import Cliente
    from excepciones import ErrorValidacion

    try:
        cliente = Cliente("1032456789", "Ana Pérez", "ana@correo.com",
                          "300 123 4567", "Calle 10 # 5-20")
        cliente.correo = "ana.perez@correo.com"     # El setter vuelve a validar.
    except ErrorValidacion as error:
        print(error)
"""

# re permite validar los formatos de nombre, correo y teléfono con expresiones regulares.
import re

# Clase abstracta común de la que hereda Cliente (ID, estado, fechas).
from entidad_base import EntidadBase
# Excepciones personalizadas del módulo de clientes (definidas en el archivo centralizado).
from excepciones import DatosClienteInvalidos, ParametroFaltante
# Gestor de logs compartido para registrar la creación y las modificaciones.
from gestor_logs import GestorLogs


class Cliente(EntidadBase):
    """
    Cliente de Software FJ con datos personales encapsulados y validados.

    Atributos privados (solo accesibles mediante propiedades):
        __nombre (str): Nombre completo.
        __correo (str): Correo electrónico (se guarda en minúsculas).
        __telefono (str): Número de teléfono.
        __direccion (str): Dirección de residencia o contacto.

    La identificación se guarda como el ID heredado de ``EntidadBase`` y se
    consulta con la propiedad ``identificacion`` (solo lectura).
    """

    # Estados que puede tener un cliente; el primero (ACTIVO) es el inicial.
    ESTADOS_PERMITIDOS = ("ACTIVO", "INACTIVO")
    # Prefijo de ID de la clase (se define por convención del equipo).
    PREFIJO_ID = "CLI"

    # Identificación: solo dígitos, entre 6 y 12 (cédula, NIT sin dígito de verificación, etc.).
    _PATRON_IDENTIFICACION = re.compile(r"^[0-9]{6,12}$")
    # Nombre: letras (incluye tildes y ñ), espacios, apóstrofo, punto y guion.
    _PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")
    # Correo: texto@dominio.extensión (extensión de al menos 2 letras).
    _PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
    # Teléfono: un + opcional al inicio y luego dígitos, espacios, guiones o paréntesis.
    _PATRON_TELEFONO = re.compile(r"^\+?[0-9 ()-]+$")

    # Longitudes mínimas de los textos.
    MIN_NOMBRE = 3
    MIN_DIRECCION = 5
    # Cantidad permitida de dígitos en el teléfono.
    MIN_DIGITOS_TELEFONO = 7
    MAX_DIGITOS_TELEFONO = 15

    def __init__(self, identificacion=None, nombre=None, correo=None, telefono=None,
                 direccion=None, estado=None):
        """
        Crea un cliente validando todos sus datos.

        Los parámetros tienen valor por defecto None para que, si falta alguno,
        se lance ``ParametroFaltante`` (mensaje claro) en lugar de un TypeError.

        Args:
            identificacion (str | int): Documento del cliente (será su ID).
            nombre (str): Nombre completo.
            correo (str): Correo electrónico.
            telefono (str): Teléfono de contacto.
            direccion (str): Dirección.
            estado (str, opcional): ACTIVO (por defecto) o INACTIVO.

        Raises:
            ParametroFaltante: Si algún dato obligatorio es None.
            DatosClienteInvalidos: Si algún dato no cumple su formato.
            EstadoInvalidoError: Si el estado no es ACTIVO ni INACTIVO.
        """
        # Se valida la identificación ANTES de llamar a la base: si fuera None, EntidadBase generaría un ID automático.
        identificacion_limpia = self._validar_identificacion(identificacion)
        # Se inicializan ID, estado y fechas en la clase base usando la identificación como ID.
        super().__init__(id_entidad=identificacion_limpia, estado=estado)
        # Se valida y guarda cada dato en su atributo privado (doble guion bajo).
        self.__nombre = self._validar_nombre(nombre)
        # Correo validado y en minúsculas.
        self.__correo = self._validar_correo(correo)
        # Teléfono validado.
        self.__telefono = self._validar_telefono(telefono)
        # Dirección validada.
        self.__direccion = self._validar_direccion(direccion)
        # Se deja constancia en el log de que el cliente se registró correctamente.
        GestorLogs.obtener_instancia().info(f"Cliente registrado: {self.describir()}", origen="Cliente")

    # ------------------------------------------------------------------
    # Validaciones (métodos de clase: se pueden usar sin crear un cliente)
    # ------------------------------------------------------------------
    @staticmethod
    def _limpiar_texto(valor, campo):
        """
        Validación común a todos los campos: obligatorio, de tipo texto y no vacío.

        Evita repetir el mismo código en cada validación.

        Args:
            valor: Dato recibido.
            campo (str): Nombre del campo (para el mensaje de error).

        Returns:
            str: Texto sin espacios al inicio y al final, y sin espacios dobles internos.

        Raises:
            ParametroFaltante: Si el valor es None.
            DatosClienteInvalidos: Si no es texto o queda vacío al quitar los espacios.
        """
        # None significa que el dato no se entregó.
        if valor is None:
            # Se lanza el error de dato faltante.
            raise ParametroFaltante(campo, "Cliente")
        # Solo se aceptan cadenas de texto (un número o una lista no son un nombre válido).
        if not isinstance(valor, str):
            # Se informa el tipo recibido.
            raise DatosClienteInvalidos(campo, valor, f"debe ser texto, se recibió {type(valor).__name__}")
        # split() separa por cualquier espacio y join los une con uno solo: quita extremos y espacios dobles.
        texto = " ".join(valor.split())
        # Si no queda nada, el texto estaba vacío o solo tenía espacios.
        if not texto:
            # Se lanza el error de dato vacío.
            raise DatosClienteInvalidos(campo, valor, "no puede estar vacío")
        # Se devuelve el texto limpio.
        return texto

    @classmethod
    def _validar_identificacion(cls, identificacion):
        """
        Valida la identificación: solo dígitos, entre 6 y 12.

        Se acepta un entero (ej. 1032456789) y se convierte a texto.

        Returns:
            str: Identificación limpia.

        Raises:
            ParametroFaltante: Si es None.
            DatosClienteInvalidos: Si está vacía o no cumple el formato.
        """
        # bool es un tipo de entero en Python, pero True/False no es un documento válido.
        if isinstance(identificacion, int) and not isinstance(identificacion, bool):
            # Un entero se convierte a texto para validarlo igual que los demás.
            identificacion = str(identificacion)
        # Se aplica la validación común (None, tipo y vacío).
        texto = cls._limpiar_texto(identificacion, "identificacion")
        # Se comprueba que solo tenga dígitos y la longitud permitida.
        if not cls._PATRON_IDENTIFICACION.match(texto):
            # Se explica el formato esperado.
            raise DatosClienteInvalidos("identificacion", identificacion,
                                        "debe contener solo dígitos (entre 6 y 12)")
        # Se devuelve la identificación limpia.
        return texto

    @classmethod
    def _validar_nombre(cls, nombre):
        """
        Valida el nombre completo: mínimo 3 caracteres y solo letras y signos de nombre.

        Returns:
            str: Nombre limpio.

        Raises:
            ParametroFaltante, DatosClienteInvalidos.
        """
        # Validación común (None, tipo y vacío).
        texto = cls._limpiar_texto(nombre, "nombre")
        # Se exige una longitud mínima.
        if len(texto) < cls.MIN_NOMBRE:
            # Se informa el mínimo requerido.
            raise DatosClienteInvalidos("nombre", nombre, f"debe tener al menos {cls.MIN_NOMBRE} caracteres")
        # Se comprueba que no tenga números ni símbolos extraños.
        if not cls._PATRON_NOMBRE.match(texto):
            # Se indican los caracteres permitidos.
            raise DatosClienteInvalidos("nombre", nombre, "solo se permiten letras, espacios, ', . y -")
        # Se devuelve el nombre limpio.
        return texto

    @classmethod
    def _validar_correo(cls, correo):
        """
        Valida el formato del correo electrónico y lo devuelve en minúsculas.

        Returns:
            str: Correo limpio y en minúsculas.

        Raises:
            ParametroFaltante, DatosClienteInvalidos.
        """
        # Validación común (None, tipo y vacío).
        texto = cls._limpiar_texto(correo, "correo")
        # Un correo no puede tener espacios internos ni dos puntos seguidos.
        if " " in texto or ".." in texto or not cls._PATRON_CORREO.match(texto):
            # Se muestra un ejemplo del formato correcto.
            raise DatosClienteInvalidos("correo", correo, "formato inválido, ejemplo: usuario@dominio.com")
        # Se guarda en minúsculas para que "Ana@Correo.com" y "ana@correo.com" sean el mismo correo.
        return texto.lower()

    @classmethod
    def _validar_telefono(cls, telefono):
        """
        Valida el teléfono: caracteres permitidos y cantidad de dígitos.

        Returns:
            str: Teléfono limpio.

        Raises:
            ParametroFaltante, DatosClienteInvalidos.
        """
        # Validación común (None, tipo y vacío).
        texto = cls._limpiar_texto(telefono, "telefono")
        # Solo se permiten dígitos, espacios, guiones, paréntesis y un + al inicio.
        if not cls._PATRON_TELEFONO.match(texto):
            # Se indican los caracteres válidos.
            raise DatosClienteInvalidos("telefono", telefono,
                                        "solo se permiten dígitos, espacios, '-', '(', ')' y '+' al inicio")
        # Se cuentan únicamente los dígitos para validar la longitud real del número.
        cantidad_digitos = sum(1 for caracter in texto if caracter.isdigit())
        # El número debe tener entre 7 y 15 dígitos.
        if not cls.MIN_DIGITOS_TELEFONO <= cantidad_digitos <= cls.MAX_DIGITOS_TELEFONO:
            # Se informa el rango permitido.
            raise DatosClienteInvalidos(
                "telefono", telefono,
                f"debe tener entre {cls.MIN_DIGITOS_TELEFONO} y {cls.MAX_DIGITOS_TELEFONO} dígitos")
        # Se devuelve el teléfono limpio.
        return texto

    @classmethod
    def _validar_direccion(cls, direccion):
        """
        Valida la dirección: obligatoria y con al menos 5 caracteres.

        Returns:
            str: Dirección limpia.

        Raises:
            ParametroFaltante, DatosClienteInvalidos.
        """
        # Validación común (None, tipo y vacío).
        texto = cls._limpiar_texto(direccion, "direccion")
        # Se exige una longitud mínima para que sea una dirección útil.
        if len(texto) < cls.MIN_DIRECCION:
            # Se informa el mínimo requerido.
            raise DatosClienteInvalidos("direccion", direccion,
                                        f"debe tener al menos {cls.MIN_DIRECCION} caracteres")
        # Se devuelve la dirección limpia.
        return texto

    # ------------------------------------------------------------------
    # Getters y setters (encapsulación)
    # ------------------------------------------------------------------
    @property
    def identificacion(self):
        """str: Documento del cliente. Es su ID, por eso no tiene setter."""
        # Se reutiliza el ID guardado por EntidadBase.
        return self.id

    @property
    def nombre(self):
        """str: Nombre completo del cliente."""
        # Getter: devuelve el atributo privado.
        return self.__nombre

    @nombre.setter
    def nombre(self, nuevo_nombre):
        """Setter: valida el nuevo nombre antes de reemplazar el actual."""
        # Si la validación falla se lanza la excepción y el valor anterior se conserva.
        self.__nombre = self._validar_nombre(nuevo_nombre)
        # Se registra la modificación.
        self._registrar_modificacion("nombre")

    @property
    def correo(self):
        """str: Correo electrónico del cliente."""
        # Getter: devuelve el atributo privado.
        return self.__correo

    @correo.setter
    def correo(self, nuevo_correo):
        """Setter: valida el nuevo correo antes de reemplazar el actual."""
        # Se valida y se asigna solo si es correcto.
        self.__correo = self._validar_correo(nuevo_correo)
        # Se registra la modificación.
        self._registrar_modificacion("correo")

    @property
    def telefono(self):
        """str: Teléfono del cliente."""
        # Getter: devuelve el atributo privado.
        return self.__telefono

    @telefono.setter
    def telefono(self, nuevo_telefono):
        """Setter: valida el nuevo teléfono antes de reemplazar el actual."""
        # Se valida y se asigna solo si es correcto.
        self.__telefono = self._validar_telefono(nuevo_telefono)
        # Se registra la modificación.
        self._registrar_modificacion("telefono")

    @property
    def direccion(self):
        """str: Dirección del cliente."""
        # Getter: devuelve el atributo privado.
        return self.__direccion

    @direccion.setter
    def direccion(self, nueva_direccion):
        """Setter: valida la nueva dirección antes de reemplazar la actual."""
        # Se valida y se asigna solo si es correcta.
        self.__direccion = self._validar_direccion(nueva_direccion)
        # Se registra la modificación.
        self._registrar_modificacion("direccion")

    def _registrar_modificacion(self, campo):
        """
        Deja constancia en el log de que un dato del cliente cambió.

        Args:
            campo (str): Nombre del dato modificado.
        """
        # Se escribe un evento INFO indicando el cliente y el campo modificado.
        GestorLogs.obtener_instancia().info(f"Cliente {self.id}: se modificó '{campo}'", origen="Cliente")

    # ------------------------------------------------------------------
    # Métodos abstractos de EntidadBase (polimorfismo)
    # ------------------------------------------------------------------
    def validar(self):
        """
        Vuelve a validar todos los datos actuales del cliente.

        Raises:
            ParametroFaltante, DatosClienteInvalidos: Si algún dato quedó inválido.
        """
        # Se validan los cinco datos con las mismas reglas usadas al crear el cliente.
        self._validar_identificacion(self.id)
        # Nombre.
        self._validar_nombre(self.__nombre)
        # Correo.
        self._validar_correo(self.__correo)
        # Teléfono.
        self._validar_telefono(self.__telefono)
        # Dirección.
        self._validar_direccion(self.__direccion)

    def describir(self):
        """
        Devuelve una descripción legible del cliente.

        Returns:
            str: Texto con nombre, identificación, correo y estado.
        """
        # Se arma el texto con los datos principales.
        return f"Cliente {self.__nombre} [{self.id}] - {self.__correo} - {self.estado}"

    def a_diccionario(self):
        """
        Extiende el diccionario de EntidadBase con los datos personales.

        Returns:
            dict: Datos comunes más nombre, correo, teléfono y dirección.
        """
        # Se obtienen los datos comunes (id, tipo, estado, fechas).
        datos = super().a_diccionario()
        # Se agregan los datos propios del cliente.
        datos.update({
            "nombre": self.__nombre,        # Nombre completo.
            "correo": self.__correo,        # Correo electrónico.
            "telefono": self.__telefono,    # Teléfono.
            "direccion": self.__direccion,  # Dirección.
        })
        # Se devuelve el diccionario completo.
        return datos
