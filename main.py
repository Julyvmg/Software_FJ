"""
Módulo: main.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4

Descripción:
    Programa principal de prueba de la primera parte del sistema. Demuestra:

    * Que ``EntidadBase`` es abstracta (no se puede instanciar directamente).
    * La creación de entidades válidas e inválidas (ID, estado y datos propios).
    * Los cambios de estado permitidos y no permitidos.
    * El registro de eventos y errores en ``sistema.log`` con ``GestorLogs``.
    * Bloques try/except, try/except/else, try/except/finally y el
      encadenamiento de excepciones (``raise ... from ...``).

    El programa nunca se detiene por un error: cada operación se ejecuta
    protegida, se registra en el log y se continúa con la siguiente.

Ejecución:
    python main.py
"""

# sys se usa para configurar la consola en UTF-8 (tildes y ñ en Windows).
import sys

# Clase abstracta raíz de las entidades del sistema.
from entidad_base import EntidadBase
# Excepciones personalizadas que se capturan en la demostración.
from excepciones import ErrorSistema, ErrorValidacion, OperacionNoPermitidaError
# Gestor de logs compartido por todo el sistema.
from gestor_logs import GestorLogs


class EntidadPrueba(EntidadBase):
    """
    Entidad concreta mínima usada SOLO para probar ``EntidadBase``.

    Será reemplazada por las clases reales Cliente, Servicio y Reserva, pero
    muestra exactamente cómo deben heredar de la clase abstracta.
    """

    # Estados propios de esta entidad; el primero (ACTIVO) es el estado inicial.
    ESTADOS_PERMITIDOS = ("ACTIVO", "INACTIVO", "ELIMINADO")
    # Prefijo de los ID automáticos de esta clase (PRB-0001, PRB-0002...).
    PREFIJO_ID = "PRB"

    def __init__(self, nombre, id_entidad=None, estado=None):
        """
        Crea la entidad de prueba.

        Args:
            nombre (str): Nombre de la entidad (mínimo 3 caracteres).
            id_entidad (str, opcional): ID manual; si se omite se genera uno.
            estado (str, opcional): Estado inicial.

        Raises:
            IdentificadorInvalidoError, EstadoInvalidoError: Desde EntidadBase.
            ErrorValidacion: Si el nombre no es válido.
        """
        # Se inicializan ID, estado y fechas mediante la clase base.
        super().__init__(id_entidad, estado)
        # Se guarda el nombre recibido en un atributo protegido.
        self._nombre = nombre
        # Se validan los datos propios al final del constructor, como indica EntidadBase.
        self.validar()

    @property
    def nombre(self):
        """str: Nombre de la entidad (solo lectura)."""
        # Se expone el nombre sin permitir modificarlo directamente.
        return self._nombre

    def validar(self):
        """
        Implementa el método abstracto: valida que el nombre sea texto de 3 o más caracteres.

        Raises:
            ErrorValidacion: Si el nombre no es texto o es demasiado corto.
        """
        # El nombre debe ser texto y tener al menos 3 caracteres sin contar espacios externos.
        if not isinstance(self._nombre, str) or len(self._nombre.strip()) < 3:
            # Se lanza el error de validación indicando el campo afectado.
            raise ErrorValidacion(f"El nombre {self._nombre!r} debe tener al menos 3 caracteres.",
                                  campo="nombre")
        # Si es válido, se guarda sin espacios sobrantes.
        self._nombre = self._nombre.strip()

    def describir(self):
        """
        Implementa el método abstracto: describe la entidad.

        Returns:
            str: Texto con nombre, ID y estado.
        """
        # Se arma la descripción con los datos principales.
        return f"Entidad de prueba '{self._nombre}' [{self.id}] - {self.estado}"

    def a_diccionario(self):
        """
        Extiende el diccionario de la clase base agregando el nombre.

        Returns:
            dict: Datos comunes más el nombre.
        """
        # Se obtienen los datos comunes desde EntidadBase.
        datos = super().a_diccionario()
        # Se agrega el dato propio de esta subclase.
        datos["nombre"] = self._nombre
        # Se devuelve el diccionario completo.
        return datos

    def _validar_transicion(self, estado_actual, estado_nuevo):
        """
        Sobrescribe la regla de transición: una entidad ELIMINADA no puede cambiar de estado.

        Args:
            estado_actual (str): Estado actual.
            estado_nuevo (str): Estado de destino.

        Raises:
            OperacionNoPermitidaError: Si la entidad ya fue eliminada.
        """
        # Si la entidad ya está eliminada, cualquier cambio queda prohibido.
        if estado_actual == "ELIMINADO":
            # Se informa la operación rechazada.
            raise OperacionNoPermitidaError(
                f"{self.tipo} {self.id} está ELIMINADO y no puede pasar a {estado_nuevo}.")


class DemostracionSistema:
    """
    Ejecuta una serie de operaciones de prueba, válidas e inválidas, y registra todo en el log.

    Atributos (protegidos):
        _log (GestorLogs): Gestor de logs compartido.
        _entidades (list[EntidadPrueba]): Entidades creadas correctamente (lista interna, sin BD).
        _exitosas (int): Operaciones que terminaron bien.
        _fallidas (int): Operaciones que terminaron con un error controlado.
        _total (int): Operaciones ejecutadas.
    """

    def __init__(self):
        """Prepara el gestor de logs, la lista interna y los contadores."""
        # Se obtiene el gestor de logs compartido (escribe en sistema.log).
        self._log = GestorLogs.obtener_instancia()
        # Lista en memoria donde se guardan las entidades creadas (no se usa base de datos).
        self._entidades = []
        # Contador de operaciones exitosas.
        self._exitosas = 0
        # Contador de operaciones con error controlado.
        self._fallidas = 0
        # Contador total de operaciones ejecutadas.
        self._total = 0

    # ------------------------------------------------------------------
    # Motor de ejecución protegida
    # ------------------------------------------------------------------
    def _ejecutar(self, descripcion, operacion):
        """
        Ejecuta una operación con try/except/else/finally sin detener el programa.

        Args:
            descripcion (str): Texto que identifica la operación.
            operacion (callable): Función sin argumentos que realiza la operación.
        """
        # Se calcula el número de la operación antes de ejecutarla.
        numero = self._total + 1
        # Se muestra en consola qué operación se va a ejecutar.
        print(f"\n[{numero:02d}] {descripcion}")
        # Bloque protegido: aquí puede ocurrir cualquier error.
        try:
            # Se ejecuta la operación y se guarda lo que devuelva.
            resultado = operacion()
        # Errores propios del sistema (validaciones, operaciones no permitidas...).
        except ErrorSistema as error:
            # Se cuenta como operación fallida pero controlada.
            self._fallidas += 1
            # Se registra el error en el log con su tipo, código y causa.
            self._log.error(f"Operación {numero} '{descripcion}' rechazada", error, origen="main")
            # Se informa en consola.
            print(f"     ERROR CONTROLADO -> {error}")
        # Cualquier otro error inesperado de Python también se captura para no cerrar el programa.
        except Exception as error:
            # Se cuenta como operación fallida.
            self._fallidas += 1
            # Se registra el error inesperado en el log.
            self._log.error(f"Error inesperado en la operación {numero}", error, origen="main")
            # Se informa en consola.
            print(f"     ERROR INESPERADO -> {type(error).__name__}: {error}")
        # El bloque else solo se ejecuta si NO hubo ninguna excepción.
        else:
            # Se cuenta como operación exitosa.
            self._exitosas += 1
            # Se registra el éxito en el log.
            self._log.info(f"Operación {numero} '{descripcion}' completada: {resultado}", origen="main")
            # Se informa en consola.
            print(f"     OK -> {resultado}")
        # El bloque finally se ejecuta SIEMPRE, haya o no error.
        finally:
            # Se actualiza el contador total de operaciones.
            self._total += 1

    # ------------------------------------------------------------------
    # Operaciones de prueba
    # ------------------------------------------------------------------
    def _crear_entidad(self, nombre, id_entidad=None, estado=None):
        """
        Crea una entidad de prueba y, si es válida, la guarda en la lista interna.

        Args:
            nombre (str): Nombre de la entidad.
            id_entidad (str, opcional): ID manual.
            estado (str, opcional): Estado inicial.

        Returns:
            str: Descripción de la entidad creada.
        """
        # Se construye la entidad (si algún dato es inválido se lanza la excepción aquí).
        entidad = EntidadPrueba(nombre, id_entidad, estado)
        # Solo si se construyó correctamente se agrega a la lista interna.
        self._entidades.append(entidad)
        # Se devuelve su descripción para mostrarla y registrarla.
        return entidad.describir()

    def _instanciar_clase_abstracta(self):
        """
        Intenta crear un objeto de la clase abstracta para demostrar que no es posible.

        Convierte el TypeError de Python en un error del sistema usando
        encadenamiento de excepciones (``raise ... from ...``).

        Raises:
            OperacionNoPermitidaError: Siempre, con el TypeError original como causa.
        """
        # Se intenta instanciar la clase abstracta directamente.
        try:
            # Python lanza TypeError porque EntidadBase tiene métodos abstractos sin implementar.
            EntidadBase("X-1")
        # Se captura el error de Python...
        except TypeError as error:
            # ...y se relanza como error del sistema conservando el original como causa.
            raise OperacionNoPermitidaError("EntidadBase es abstracta y no puede instanciarse.") from error

    def _cambiar_estado(self, posicion, nuevo_estado, motivo=None):
        """
        Cambia el estado de una entidad de la lista interna.

        Args:
            posicion (int): Índice de la entidad en la lista.
            nuevo_estado (str): Estado de destino.
            motivo (str, opcional): Razón del cambio.

        Returns:
            str: Texto con el estado anterior y el nuevo.
        """
        # Se toma la entidad (si la posición no existe se lanza IndexError, que también se controla).
        entidad = self._entidades[posicion]
        # Se cambia el estado y se recibe el estado anterior.
        anterior = entidad.cambiar_estado(nuevo_estado, motivo)
        # Se devuelve un resumen del cambio.
        return f"{entidad.id}: {anterior} -> {entidad.estado}"

    def _comparar_entidades(self):
        """
        Demuestra la igualdad por ID y el uso de entidades en un conjunto.

        Returns:
            str: Resultado de la comparación y del conjunto.
        """
        # Se crea una copia con el mismo ID que la segunda entidad, pero sin guardarla en la lista.
        copia = EntidadPrueba("Copia de prueba", id_entidad=self._entidades[1].id)
        # Dos entidades del mismo tipo y mismo ID son iguales.
        iguales = copia == self._entidades[1]
        # En un conjunto, los duplicados por ID se eliminan automáticamente.
        unicas = len(set(self._entidades + [copia]))
        # Se devuelve el resultado legible.
        return f"copia == original: {iguales}; entidades únicas en el conjunto: {unicas}"

    def _nivel_desconocido(self):
        """
        Demuestra que GestorLogs no falla ante un nivel inválido (lo registra como WARNING).

        Returns:
            str: La línea que se escribió en el log.
        """
        # Se registra con un nivel inexistente; el gestor lo convierte en advertencia.
        return self._log.registrar("DEBUGX", "Prueba de nivel no soportado", origen="main")

    # ------------------------------------------------------------------
    # Ejecución completa
    # ------------------------------------------------------------------
    def ejecutar(self):
        """Ejecuta todas las operaciones de prueba y muestra el resumen final."""
        # Se registra el inicio de la demostración.
        self._log.info("===== INICIO DE LA DEMOSTRACIÓN =====", origen="main")
        # 1. Creación válida con ID automático.
        self._ejecutar("Crear entidad válida con ID automático",
                       lambda: self._crear_entidad("Sala de juntas"))
        # 2. Creación válida con ID manual y estado inicial explícito.
        self._ejecutar("Crear entidad válida con ID manual",
                       lambda: self._crear_entidad("Proyector Epson", "PRB-100", "inactivo"))
        # 3. Intento de instanciar la clase abstracta (encadenamiento de excepciones).
        self._ejecutar("Instanciar directamente la clase abstracta",
                       self._instanciar_clase_abstracta)
        # 4. ID con caracteres no permitidos.
        self._ejecutar("Crear entidad con ID inválido",
                       lambda: self._crear_entidad("Asesoría", "id con espacios!"))
        # 5. Estado que no existe para la entidad.
        self._ejecutar("Crear entidad con estado inválido",
                       lambda: self._crear_entidad("Asesoría", estado="SUSPENDIDO"))
        # 6. Dato propio inválido (nombre demasiado corto).
        self._ejecutar("Crear entidad con nombre inválido",
                       lambda: self._crear_entidad("ab"))
        # 7. Cambio de estado permitido.
        self._ejecutar("Cambiar estado ACTIVO -> INACTIVO",
                       lambda: self._cambiar_estado(0, "INACTIVO", "mantenimiento"))
        # 8. Cambio al mismo estado (no permitido).
        self._ejecutar("Cambiar al mismo estado",
                       lambda: self._cambiar_estado(0, "INACTIVO"))
        # 9. Eliminar la entidad (permitido).
        self._ejecutar("Cambiar estado a ELIMINADO",
                       lambda: self._cambiar_estado(1, "ELIMINADO", "retirado del inventario"))
        # 10. Reactivar una entidad eliminada (prohibido por la subclase).
        self._ejecutar("Reactivar entidad eliminada",
                       lambda: self._cambiar_estado(1, "ACTIVO"))
        # 11. Acceso a una posición inexistente (error inesperado de Python, también controlado).
        self._ejecutar("Cambiar estado de una entidad inexistente",
                       lambda: self._cambiar_estado(99, "ACTIVO"))
        # 12. Igualdad por ID y conjuntos.
        self._ejecutar("Comparar entidades por ID", self._comparar_entidades)
        # 13. Conversión a diccionario (polimorfismo con super()).
        self._ejecutar("Convertir entidad a diccionario",
                       lambda: self._entidades[0].a_diccionario())
        # 14. Robustez del gestor de logs ante un nivel desconocido.
        self._ejecutar("Registrar con un nivel desconocido", self._nivel_desconocido)
        # Se registra el resumen final en el log.
        self._log.info(f"===== FIN: {self._total} operaciones, {self._exitosas} exitosas, "
                       f"{self._fallidas} con error controlado =====", origen="main")
        # Se muestra el resumen en consola.
        self._mostrar_resumen()

    def _mostrar_resumen(self):
        """Imprime el resumen de la demostración y los errores registrados en el log."""
        # Línea separadora para destacar el resumen.
        print("\n" + "=" * 70)
        # Totales de la ejecución.
        print(f"Operaciones: {self._total} | Exitosas: {self._exitosas} | Con error: {self._fallidas}")
        # Entidades que quedaron guardadas en la lista interna.
        print(f"Entidades en memoria: {[repr(e) for e in self._entidades]}")
        # Ubicación del archivo de logs.
        print(f"Archivo de logs: {self._log.ruta}")
        # Cantidad de errores que hay en el archivo (incluye ejecuciones anteriores).
        print(f"Líneas ERROR en el archivo: {len(self._log.leer_registros('ERROR'))}")
        # Línea separadora final.
        print("=" * 70)


class Aplicacion:
    """Punto de entrada del programa: prepara la consola y lanza la demostración."""

    @staticmethod
    def _configurar_consola():
        """Configura la consola en UTF-8 para mostrar bien tildes y ñ en Windows."""
        # Se intenta cambiar la codificación de la salida estándar.
        try:
            # reconfigure existe desde Python 3.7 en los flujos de texto estándar.
            sys.stdout.reconfigure(encoding="utf-8")
        # Si la consola no lo permite (por ejemplo, salida redirigida especial), se ignora.
        except (AttributeError, ValueError):
            # No es un error grave: solo afecta la visualización de tildes.
            pass

    def iniciar(self):
        """
        Ejecuta la demostración protegiendo el programa de cualquier fallo general.

        Usa try/except/finally: el mensaje de cierre se registra siempre.
        """
        # Se configura la consola antes de imprimir cualquier texto.
        self._configurar_consola()
        # Se obtiene el gestor de logs compartido.
        log = GestorLogs.obtener_instancia()
        # Se protege toda la ejecución.
        try:
            # Se crea y ejecuta la demostración.
            DemostracionSistema().ejecutar()
        # Último recurso: cualquier error no previsto se registra en lugar de cerrar con traceback.
        except Exception as error:
            # Se registra el fallo general en el log.
            log.error("Fallo general de la aplicación", error, origen="main")
            # Se informa en consola.
            print(f"Fallo general: {error}")
        # Siempre se registra el cierre del programa.
        finally:
            # Evento de cierre en el log.
            log.info("Fin de la ejecución", origen="main")


# Solo se ejecuta la aplicación si este archivo se corre directamente (no al importarlo).
if __name__ == "__main__":
    # Se crea la aplicación y se inicia.
    Aplicacion().iniciar()
