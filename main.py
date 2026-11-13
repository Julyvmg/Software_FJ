"""
Módulo: main.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Autora: July Matabanchoy

Descripción:
    Este es el archivo principal para probar que todo lo que hemos hecho 
    funcione bien. Aquí probamos:
    - Que la clase base funcione correctamente.
    - La creación de registros correctos y el manejo de errores si algo sale mal.
    - Los cambios de estado de cada cosa.
    - Que los eventos y errores se guarden solitos en el archivo de texto.

    El programa está armado para que, si ocurre un error, no se caiga ni se 
    cierre, sino que lo anote y siga con lo que sigue.
"""

# sys se usa para que la consola acepte tildes y la letra ñ sin problemas en Windows.
import sys

# Traemos la clase base que creamos antes.
from entidad_base import EntidadBase
# Traemos los errores personalizados para controlarlos mejor.
from excepciones import ErrorSistema, ErrorValidacion, OperacionNoPermitidaError
# Traemos el gestor para guardar el historial de eventos.
from gestor_logs import GestorLogs


class EntidadPrueba(EntidadBase):
    """
    Una entidad sencilla que usamos SOLO para probar la clase base.
    Más adelante tus compañeros la cambiarán por las clases reales 
    (como Cliente, Servicio o Reserva).
    """

    # Los estados que puede tener esta prueba.
    ESTADOS_PERMITIDOS = ("ACTIVO", "INACTIVO", "ELIMINADO")
    # El código que se usa para inventar IDs automáticos (ej: PRB-0001).
    PREFIJO_ID = "PRB"

    def __init__(self, nombre, id_entidad=None, estado=None):
        """Prepara nuestra entidad de prueba con su nombre y estado."""
        # Llamamos al constructor de la clase base para configurar el ID y fechas.
        super().__init__(id_entidad, estado)
        # Guardamos el nombre que nos pasan.
        self._nombre = nombre
        # Validamos que el nombre esté bien escrito al terminar.
        self.validar()

    @property
    def nombre(self):
        """Devuelve el nombre pero sin dejar que lo cambien por fuera."""
        return self._nombre

    def validar(self):
        """Revisa que el nombre tenga al menos 3 letras."""
        if not isinstance(self._nombre, str) or len(self._nombre.strip()) < 3:
            raise ErrorValidacion(f"El nombre {self._nombre!r} debe tener al menos 3 caracteres.",
                                  campo="nombre")
        self._nombre = self._nombre.strip()

    def describir(self):
        """Devuelve un texto bonito con la información principal de la entidad."""
        return f"Entidad de prueba '{self._nombre}' [{self.id}] - {self.estado}"

    def a_diccionario(self):
        """Convierte los datos de la entidad en un diccionario para manejarlos fácil."""
        datos = super().a_diccionario()
        datos["nombre"] = self._nombre
        return datos

    def _validar_transicion(self, estado_actual, estado_nuevo):
        """Si ya está eliminado, no permitimos que lo cambien a ningún otro estado."""
        if estado_actual == "ELIMINADO":
            raise OperacionNoPermitidaError(
                f"{self.tipo} {self.id} está ELIMINADO y no puede pasar a {estado_nuevo}.")


class DemostracionSistema:
    """Se encarga de correr varias pruebas (buenas y malas) y anotar todo en el registro."""

    def __init__(self):
        """Prepara las listas y contadores para ver cuántas cosas salieron bien o mal."""
        self._log = GestorLogs.obtener_instancia()
        self._entidades = []
        self._exitosas = 0
        self._fallidas = 0
        self._total = 0

    def _ejecutar(self, descripcion, operacion):
        """Ejecuta una acción protegiéndola con un try/except para que el programa no falle."""
        numero = self._total + 1
        print(f"\n[{numero:02d}] {descripcion}")
        
        try:
            # Intentamos hacer la operación
            resultado = operacion()
        except ErrorSistema as error:
            # Si es un error controlado nuestro
            self._fallidas += 1
            self._log.error(f"Operación {numero} '{descripcion}' rechazada", error, origen="main")
            print(f"     ERROR CONTROLADO -> {error}")
        except Exception as error:
            # Si ocurre cualquier otro error imprevisto
            self._fallidas += 1
            self._log.error(f"Error inesperado en la operación {numero}", error, origen="main")
            print(f"     ERROR INESPERADO -> {type(error).__name__}: {error}")
        else:
            # Si todo sale bien
            self._exitosas += 1
            self._log.info(f"Operación {numero} '{descripcion}' completada: {resultado}", origen="main")
            print(f"     OK -> {resultado}")
        finally:
            # Esto se ejecuta pase lo que pase para llevar la cuenta
            self._total += 1

    def _crear_entidad(self, nombre, id_entidad=None, estado=None):
        """Crea una entidad de prueba y la guarda si todo sale bien."""
        entidad = EntidadPrueba(nombre, id_entidad, estado)
        self._entidades.append(entidad)
        return entidad.describir()

    def _instanciar_clase_abstracta(self):
        """Prueba que no se pueda crear un objeto directamente de la clase base abstracta."""
        try:
            EntidadBase("X-1")
        except TypeError as error:
            raise OperacionNoPermitidaError("EntidadBase es abstracta y no puede instanciarse.") from error

    def _cambiar_estado(self, posicion, nuevo_estado, motivo=None):
        """Cambia el estado de una entidad que ya teníamos guardada."""
        entidad = self._entidades[posicion]
        anterior = entidad.cambiar_estado(nuevo_estado, motivo)
        return f"{entidad.id}: {anterior} -> {entidad.estado}"

    def _comparar_entidades(self):
        """Prueba que dos entidades con el mismo ID se consideren iguales."""
        copia = EntidadPrueba("Copia de prueba", id_entidad=self._entidades[1].id)
        iguales = copia == self._entidades[1]
        unicas = len(set(self._entidades + [copia]))
        return f"copia == original: {iguales}; entidades únicas en el conjunto: {unicas}"

    def _nivel_desconocido(self):
        """Prueba que el gestor de registros no falle si le mandamos un nivel extraño."""
        return self._log.registrar("DEBUGX", "Prueba de nivel no soportado", origen="main")

    def ejecutar(self):
        """Corre todas las pruebas una por una."""
        self._log.info("===== INICIO DE LA DEMOSTRACIÓN =====", origen="main")
        
        # 1. Crear con ID automático
        self._ejecutar("Crear entidad válida con ID automático",
                       lambda: self._crear_entidad("Sala de juntas"))
        # 2. Crear con ID manual
        self._ejecutar("Crear entidad válida con ID manual",
                       lambda: self._crear_entidad("Proyector Epson", "PRB-100", "inactivo"))
        # 3. Intentar crear la clase abstracta (debe fallar a propósito)
        self._ejecutar("Instanciar directamente la clase abstracta",
                       self._instanciar_clase_abstracta)
        # 4. ID con espacios prohibidos
        self._ejecutar("Crear entidad con ID inválido",
                       lambda: self._crear_entidad("Asesoría", "id con espacios!"))
        # 5. Estado que no existe
        self._ejecutar("Crear entidad con estado inválido",
                       lambda: self._crear_entidad("Asesoría", estado="SUSPENDIDO"))
        # 6. Nombre muy corto (debe fallar)
        self._ejecutar("Crear entidad con nombre inválido",
                       lambda: self._crear_entidad("ab"))
        # 7. Cambiar estado bien
        self._ejecutar("Cambiar estado ACTIVO -> INACTIVO",
                       lambda: self._cambiar_estado(0, "INACTIVO", "mantenimiento"))
        # 8. Cambiar al mismo estado (debe fallar)
        self._ejecutar("Cambiar al mismo estado",
                       lambda: self._cambiar_estado(0, "INACTIVO"))
        # 9. Eliminar entidad
        self._ejecutar("Cambiar estado a ELIMINADO",
                       lambda: self._cambiar_estado(1, "ELIMINADO", "retirado del inventario"))
        # 10. Intentar revivir una entidad eliminada (prohibido)
        self._ejecutar("Reactivar entidad eliminada",
                       lambda: self._cambiar_estado(1, "ACTIVO"))
        # 11. Buscar una posición que no existe
        self._ejecutar("Cambiar estado de una entidad inexistente",
                       lambda: self._cambiar_estado(99, "ACTIVO"))
        # 12. Comparar IDs
        self._ejecutar("Comparar entidades por ID", self._comparar_entidades)
        # 13. Convertir a diccionario
        self._ejecutar("Convertir entidad a diccionario",
                       lambda: self._entidades[0].a_diccionario())
        # 14. Nivel desconocido en el registro
        self._ejecutar("Registrar con un nivel desconocido", self._nivel_desconocido)
        
        self._log.info(f"===== FIN: {self._total} operaciones, {self._exitosas} exitosas, "
                       f"{self._fallidas} con error controlado =====", origen="main")
        self._mostrar_resumen()

    def _mostrar_resumen(self):
        """Muestra en pantalla el resultado final de las pruebas."""
        print("\n" + "=" * 70)
        print(f"Operaciones: {self._total} | Exitosas: {self._exitosas} | Con error: {self._fallidas}")
        print(f"Entidades en memoria: {[repr(e) for e in self._entidades]}")
        print(f"Archivo de logs: {self._log.ruta}")
        print(f"Líneas ERROR en el archivo: {len(self._log.leer_registros('ERROR'))}")
        print("=" * 70)


class Aplicacion:
    """Clase principal que arranca todo el programa."""

    @staticmethod
    def _configurar_consola():
        """Ajusta la consola para ver bien las tildes."""
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    def iniciar(self):
        """Inicia la aplicación completa de manera segura."""
        self._configurar_consola()
        log = GestorLogs.obtener_instancia()
        try:
            DemostracionSistema().ejecutar()
        except Exception as error:
            log.error("Fallo general de la aplicación", error, origen="main")
            print(f"Fallo general: {error}")
        finally:
            log.info("Fin de la ejecución", origen="main")


# Si corremos este archivo directamente, arranca la aplicación.
if __name__ == "__main__":
    Aplicacion().iniciar()
