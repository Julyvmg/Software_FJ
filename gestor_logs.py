"""
Módulo: gestor_logs.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4

Descripción:
    Contiene la clase ``GestorLogs``, encargada de registrar los eventos
    importantes y los errores del sistema en el archivo de texto ``sistema.log``.
    No se usa ninguna base de datos: cada evento se agrega como una línea al
    final del archivo.

Formato de cada línea (campos separados por " | "):

    FECHA Y HORA        | NIVEL   | ORIGEN               | MENSAJE
    2026-11-10 21:50:01 | INFO    | Cliente              | Cliente 1032456789 registrado
    2026-11-10 21:50:02 | ERROR   | Reserva              | Reserva rechazada -> EstadoInvalidoError: [VAL-002] ...

Uso desde cualquier módulo del proyecto:

    from gestor_logs import GestorLogs

    log = GestorLogs.obtener_instancia()      # Todos comparten el mismo gestor y archivo.
    log.info("Cliente registrado", origen="Cliente")
    log.warning("Cupo casi agotado", origen="Servicio")
    try:
        ...
    except ErrorSistema as error:
        log.error("No se pudo crear la reserva", error, origen="Reserva")

Garantía de robustez:
    Registrar un evento NUNCA detiene la aplicación. Si el archivo no se puede
    escribir (permisos, disco lleno), el evento se muestra en la consola de
    errores y el programa continúa.
"""

# os permite construir rutas de archivo válidas en Windows, Linux y macOS.
import os
# sys da acceso a la salida de errores (stderr), usada como respaldo si falla el archivo.
import sys
# datetime proporciona la fecha y hora exactas de cada evento (marca de tiempo).
from datetime import datetime


class GestorLogs:
    """
    Registra eventos y errores del sistema en un archivo de texto.

    Atributos de clase:
        INFO, WARNING, ERROR (str): Niveles de mensaje admitidos.
        NIVELES (tuple[str]): Conjunto de niveles válidos.
        FORMATO_FECHA (str): Formato de la marca de tiempo.
        SEPARADOR (str): Texto que separa los campos de cada línea.
        NOMBRE_ARCHIVO (str): Nombre por defecto del archivo de logs.

    Atributos de instancia (protegidos):
        _ruta (str): Ruta absoluta del archivo de logs.
        _fallos_escritura (int): Veces que no se pudo escribir en el archivo.
    """

    # Nivel para eventos normales del sistema (operaciones exitosas).
    INFO = "INFO"
    # Nivel para situaciones anómalas que no impiden continuar.
    WARNING = "WARNING"
    # Nivel para errores controlados (excepciones capturadas).
    ERROR = "ERROR"
    # Tupla con todos los niveles permitidos, usada para validar.
    NIVELES = (INFO, WARNING, ERROR)
    # Formato año-mes-día hora:minuto:segundo para la marca de tiempo.
    FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
    # Separador de campos; siempre el mismo para que el archivo sea fácil de leer y filtrar.
    SEPARADOR = " | "
    # Nombre del archivo de logs exigido para el proyecto.
    NOMBRE_ARCHIVO = "sistema.log"
    # Instancia compartida (se crea la primera vez que se pide con obtener_instancia()).
    _instancia = None

    def __init__(self, ruta_archivo=None):
        """
        Prepara el gestor de logs.

        Args:
            ruta_archivo (str, opcional): Ruta del archivo de logs. Si no se indica,
                se usa ``sistema.log`` en la misma carpeta de este módulo, sin importar
                desde dónde se ejecute el programa.
        """
        # Si no se entregó una ruta, se calcula la ruta por defecto.
        if ruta_archivo is None:
            # Carpeta donde está guardado este archivo .py.
            carpeta = os.path.dirname(os.path.abspath(__file__))
            # Ruta completa del archivo sistema.log dentro de esa carpeta.
            ruta_archivo = os.path.join(carpeta, self.NOMBRE_ARCHIVO)
        # Se guarda la ruta como absoluta para evitar ambigüedades.
        self._ruta = os.path.abspath(ruta_archivo)
        # Contador de errores de escritura, útil para diagnosticar problemas con el archivo.
        self._fallos_escritura = 0

    # ------------------------------------------------------------------
    # Instancia compartida
    # ------------------------------------------------------------------
    @classmethod
    def obtener_instancia(cls):
        """
        Devuelve el gestor de logs compartido por todo el sistema.

        Así Cliente, Servicio, Reserva y el programa principal escriben en el
        mismo archivo sin tener que pasarse el objeto entre ellos.

        Returns:
            GestorLogs: La instancia única del gestor.
        """
        # Solo se crea el gestor la primera vez que se solicita.
        if cls._instancia is None:
            # Se construye con la ruta por defecto (sistema.log).
            cls._instancia = cls()
        # Las siguientes llamadas devuelven siempre el mismo objeto.
        return cls._instancia

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def ruta(self):
        """str: Ruta absoluta del archivo de logs."""
        # Se expone la ruta sin permitir modificarla desde fuera.
        return self._ruta

    @property
    def fallos_escritura(self):
        """int: Cantidad de veces que no se pudo escribir en el archivo."""
        # Se expone el contador de fallos sin permitir modificarlo desde fuera.
        return self._fallos_escritura

    # ------------------------------------------------------------------
    # Métodos públicos de registro
    # ------------------------------------------------------------------
    def registrar(self, nivel, mensaje, origen="Sistema"):
        """
        Registra un mensaje con el nivel indicado.

        Si el nivel no es INFO, WARNING ni ERROR, el mensaje no se pierde: se
        registra como WARNING indicando el nivel desconocido.

        Args:
            nivel (str): Nivel del mensaje (INFO, WARNING o ERROR).
            mensaje (str): Texto descriptivo del evento.
            origen (str): Módulo o clase que genera el evento (ej. "Cliente").

        Returns:
            str: La línea exacta que se escribió en el archivo.
        """
        # Se normaliza el nivel: se convierte a texto, sin espacios y en mayúsculas.
        nivel_normalizado = str(nivel).strip().upper()
        # Se verifica que el nivel sea uno de los permitidos.
        if nivel_normalizado not in self.NIVELES:
            # Se deja constancia en el mensaje del nivel que no era válido.
            mensaje = f"(nivel desconocido {nivel!r}) {mensaje}"
            # El evento se degrada a advertencia en lugar de lanzar un error.
            nivel_normalizado = self.WARNING
        # Se construye la línea con marca de tiempo, nivel, origen y mensaje.
        linea = self._formatear(nivel_normalizado, mensaje, origen)
        # Se escribe la línea en el archivo (con respaldo en consola si falla).
        self._escribir(linea)
        # Se devuelve la línea para que quien llama pueda mostrarla si lo desea.
        return linea

    def info(self, mensaje, origen="Sistema"):
        """
        Registra un evento normal del sistema (nivel INFO).

        Args:
            mensaje (str): Descripción del evento.
            origen (str): Módulo o clase que genera el evento.

        Returns:
            str: La línea escrita en el archivo.
        """
        # Se delega en registrar() usando el nivel INFO.
        return self.registrar(self.INFO, mensaje, origen)

    def warning(self, mensaje, origen="Sistema"):
        """
        Registra una advertencia (nivel WARNING).

        Args:
            mensaje (str): Descripción de la advertencia.
            origen (str): Módulo o clase que genera el evento.

        Returns:
            str: La línea escrita en el archivo.
        """
        # Se delega en registrar() usando el nivel WARNING.
        return self.registrar(self.WARNING, mensaje, origen)

    def error(self, mensaje, excepcion=None, origen="Sistema"):
        """
        Registra un error (nivel ERROR), opcionalmente con la excepción capturada.

        Cuando se entrega la excepción se agregan su tipo, su mensaje y, si fue
        lanzada con ``raise ... from ...``, la causa original (encadenamiento).

        Args:
            mensaje (str): Contexto de la operación que falló.
            excepcion (BaseException, opcional): Excepción capturada en el except.
            origen (str): Módulo o clase que genera el evento.

        Returns:
            str: La línea escrita en el archivo.
        """
        # Solo si se entregó una excepción se enriquece el mensaje con sus detalles.
        if excepcion is not None:
            # Se agrega el tipo de error, su texto y su causa encadenada.
            mensaje = self._describir_excepcion(mensaje, excepcion)
        # Se delega en registrar() usando el nivel ERROR.
        return self.registrar(self.ERROR, mensaje, origen)

    def leer_registros(self, nivel=None):
        """
        Lee las líneas del archivo de logs, opcionalmente filtradas por nivel.

        Args:
            nivel (str, opcional): INFO, WARNING o ERROR. Si es None se devuelven todas.

        Returns:
            list[str]: Líneas del archivo (sin salto de línea final). Lista vacía si
            el archivo aún no existe o no se puede leer.
        """
        # Se intenta abrir el archivo en modo lectura.
        try:
            # errors="replace" evita fallar si alguna línea tiene caracteres dañados.
            with open(self._ruta, "r", encoding="utf-8", errors="replace") as archivo:
                # Se leen todas las líneas, quitando el salto final y descartando las vacías.
                lineas = [linea.rstrip("\n") for linea in archivo if linea.strip()]
        # Si el archivo todavía no existe, simplemente no hay registros.
        except FileNotFoundError:
            # Se devuelve una lista vacía en lugar de interrumpir el programa.
            return []
        # Cualquier otro problema de lectura (permisos, bloqueo) se informa en consola.
        except OSError as error:
            # Se avisa por la salida de errores sin detener la aplicación.
            print(f"[GestorLogs] No se pudo leer {self._ruta}: {error}", file=sys.stderr)
            # Se devuelve una lista vacía.
            return []
        # Si no se pidió filtro, se devuelven todas las líneas leídas.
        if nivel is None:
            # Retorno de todas las líneas.
            return lineas
        # Se normaliza el nivel buscado para compararlo sin importar mayúsculas.
        buscado = str(nivel).strip().upper()
        # Se conservan solo las líneas cuyo segundo campo (el nivel) coincide con el buscado.
        return [linea for linea in lineas if self._campo(linea, 1) == buscado]

    # ------------------------------------------------------------------
    # Métodos internos (auxiliares)
    # ------------------------------------------------------------------
    def _formatear(self, nivel, mensaje, origen):
        """
        Construye la línea estructurada que se escribirá en el archivo.

        Args:
            nivel (str): Nivel ya validado.
            mensaje (str): Texto del evento.
            origen (str): Módulo o clase que generó el evento.

        Returns:
            str: Línea con la forma "fecha | nivel | origen | mensaje".
        """
        # Se toma la fecha y hora actuales y se les da el formato definido.
        marca_tiempo = datetime.now().strftime(self.FORMATO_FECHA)
        # Se unen los cuatro campos; nivel y origen con ancho fijo para que las columnas queden alineadas.
        return self.SEPARADOR.join([
            marca_tiempo,                                 # Campo 0: marca de tiempo.
            f"{nivel:<7}",                                # Campo 1: nivel (7 caracteres).
            f"{self._una_linea(origen or 'Sistema'):<20}",  # Campo 2: origen (mínimo 20 caracteres).
            self._una_linea(mensaje),                     # Campo 3: mensaje en una sola línea.
        ])

    def _escribir(self, linea):
        """
        Agrega una línea al final del archivo de logs.

        Usa try/except/else: si la escritura falla, el evento se muestra en la
        consola de errores; si funciona, no se hace nada adicional.

        Args:
            linea (str): Línea ya formateada.
        """
        # Se intenta escribir en el archivo.
        try:
            # Modo "a" (append) agrega al final sin borrar lo anterior; UTF-8 conserva tildes y ñ.
            with open(self._ruta, "a", encoding="utf-8") as archivo:
                # Se escribe la línea seguida de un salto de línea.
                archivo.write(linea + "\n")
        # Si el sistema operativo impide escribir (permisos, disco lleno, ruta inválida)...
        except OSError as error:
            # ...se cuenta el fallo para poder diagnosticarlo después...
            self._fallos_escritura += 1
            # ...se avisa en la consola de errores del motivo...
            print(f"[GestorLogs] No se pudo escribir en {self._ruta}: {error}", file=sys.stderr)
            # ...y se muestra el evento para que no se pierda.
            print(linea, file=sys.stderr)

    @staticmethod
    def _una_linea(texto):
        """
        Convierte un texto en una sola línea para mantener la estructura del archivo.

        Args:
            texto: Valor a convertir (se acepta cualquier tipo).

        Returns:
            str: Texto sin saltos de línea ni espacios sobrantes en los extremos.
        """
        # Se pasa a texto, se reemplazan los saltos de línea por " / " y se recortan los extremos.
        return str(texto).replace("\r", "").replace("\n", " / ").strip()

    @staticmethod
    def _describir_excepcion(mensaje, excepcion):
        """
        Describe una excepción incluyendo su causa encadenada, si existe.

        Args:
            mensaje (str): Contexto de la operación que falló.
            excepcion (BaseException): Excepción capturada.

        Returns:
            str: Texto "contexto -> Tipo: detalle [causa: Tipo: detalle]".
        """
        # Se arma la parte principal: contexto, nombre de la clase del error y su mensaje.
        texto = f"{mensaje} -> {type(excepcion).__name__}: {excepcion}"
        # __cause__ guarda la excepción original cuando se usó "raise Nuevo(...) from original".
        causa = excepcion.__cause__
        # Solo se agrega la causa si realmente existe.
        if causa is not None:
            # Se añade entre corchetes para conservar la trazabilidad del error original.
            texto += f" [causa: {type(causa).__name__}: {causa}]"
        # Se devuelve la descripción completa.
        return texto

    def _campo(self, linea, posicion):
        """
        Extrae un campo de una línea del log.

        Args:
            linea (str): Línea leída del archivo.
            posicion (int): Índice del campo (0 fecha, 1 nivel, 2 origen, 3 mensaje).

        Returns:
            str: El campo sin espacios, o cadena vacía si la línea no tiene ese campo.
        """
        # Se divide la línea por el separador como máximo 3 veces (el mensaje puede contener " | ").
        partes = linea.split(self.SEPARADOR, 3)
        # Si la posición existe se devuelve limpia; si no, cadena vacía.
        return partes[posicion].strip() if posicion < len(partes) else ""
