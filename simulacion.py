"""
Módulo: simulacion.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 5 - Simulación de operaciones e integración

Descripción:
    Simula operaciones completas del sistema usando las clases reales de todo
    el equipo (Cliente, Servicio y sus subclases, Reserva y GestorReservas).

    Incluye, como exige el Anexo 3:
    * Registros válidos e inválidos de clientes.
    * Creación correcta e incorrecta de servicios.
    * Reservas exitosas y fallidas (cliente inactivo, servicio no disponible,
      duración inválida, confirmar una cancelada, cancelar dos veces...).
    * Un error inesperado de Python, para demostrar que el programa no se detiene.

    Cada operación declara el resultado ESPERADO ("EXITO" o "ERROR"). Al final
    se compara con el OBTENIDO: si todos coinciden, el sistema se comportó como
    se diseñó, incluso ante los errores.

    No se usa base de datos: los datos viven en listas y diccionarios en
    memoria, y los eventos y errores se escriben en ``sistema.log``.

Ejecución:
    python simulacion.py
"""

# sys: consola en UTF-8 (tildes y ñ en Windows).
import sys
# date y timedelta: fecha de realización de las reservas (dentro de unos días).
from datetime import date, timedelta

# Clases de los integrantes del equipo.
from cliente import Cliente
from servicio import Servicio, procesar_servicios
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
from reserva import GestorReservas
# Excepción raíz de todos los errores controlados del sistema.
from excepciones import ErrorSistema
# Gestor de logs compartido.
from gestor_logs import GestorLogs

# Resultados posibles de una operación.
EXITO = "EXITO"
ERROR = "ERROR"


class SimuladorOperaciones:
    """
    Ejecuta una lista de operaciones protegidas y lleva el registro de resultados.

    Atributos privados:
        __log (GestorLogs): Gestor de logs compartido.
        __clientes (dict): Clientes registrados (identificación -> Cliente).
        __servicios (dict): Servicios creados (código -> Servicio).
        __reservas (GestorReservas): Reservas registradas.
        __resultados (list[dict]): Una fila por operación ejecutada.
    """

    def __init__(self, mostrar_en_consola=True):
        """
        Args:
            mostrar_en_consola (bool): False para ejecutar en silencio (lo usa la
                verificación global y el generador del informe).
        """
        self.__log = GestorLogs.obtener_instancia()
        self.__clientes = {}
        self.__servicios = {}
        self.__reservas = GestorReservas()
        self.__resultados = []
        self.__mostrar = mostrar_en_consola
        # Fecha de realización usada en las reservas (dentro de 3 días).
        self.__fecha_reserva = date.today() + timedelta(days=3)

    # ------------------------------------------------------------------
    # Motor: ejecuta una operación sin dejar que un error detenga el programa
    # ------------------------------------------------------------------
    def ejecutar(self, descripcion, esperado, operacion):
        """
        Ejecuta una operación con try/except/else/finally.

        * except ErrorSistema: error previsto por el sistema (validaciones, estados...).
        * except Exception:   error NO previsto de Python. Es la última barrera
                              para que la aplicación siga funcionando; se registra
                              en el log con su tipo para poder corregirlo.
        * else:               solo si la operación terminó bien.
        * finally:            siempre: guarda la fila de resultados.

        Args:
            descripcion (str): Qué hace la operación.
            esperado (str): EXITO o ERROR, según el diseño.
            operacion (callable): Función sin argumentos que realiza la operación.
        """
        numero = len(self.__resultados) + 1
        fila = {"numero": numero, "descripcion": descripcion, "esperado": esperado}
        self._imprimir(f"\n[{numero:02d}] {descripcion}")
        try:
            detalle = operacion()
        except ErrorSistema as error:
            fila.update(obtenido=ERROR, tipo_error=type(error).__name__, detalle=str(error))
            # Si el error fue encadenado (raise ... from), se muestra también la causa original.
            if error.__cause__ is not None:
                fila["causa"] = f"{type(error.__cause__).__name__}: {error.__cause__}"
            self.__log.error(f"Simulación {numero}: '{descripcion}' rechazada", error, origen="Simulacion")
        except Exception as error:
            fila.update(obtenido=ERROR, tipo_error=type(error).__name__,
                        detalle=f"Error inesperado controlado: {error}")
            self.__log.error(f"Simulación {numero}: error inesperado", error, origen="Simulacion")
        else:
            fila.update(obtenido=EXITO, tipo_error="", detalle=str(detalle))
            self.__log.info(f"Simulación {numero}: '{descripcion}' completada", origen="Simulacion")
        finally:
            fila["coincide"] = fila.get("obtenido") == esperado
            self.__resultados.append(fila)
            self._mostrar_fila(fila)

    def _imprimir(self, texto):
        """Imprime solo si la consola está activada."""
        if self.__mostrar:
            print(texto)

    def _mostrar_fila(self, fila):
        """Muestra el resultado de una operación."""
        marca = "OK" if fila["coincide"] else "!!"
        etiqueta = "EXITO" if fila["obtenido"] == EXITO else f"ERROR {fila['tipo_error']}"
        self._imprimir(f"     [{marca}] esperado {fila['esperado']} | obtenido {etiqueta}")
        self._imprimir(f"          {fila['detalle']}")
        if "causa" in fila:
            self._imprimir(f"          causa original -> {fila['causa']}")

    # ------------------------------------------------------------------
    # Pasos reutilizables
    # ------------------------------------------------------------------
    def _registrar_cliente(self, **datos):
        """Crea un cliente y lo guarda en el diccionario interno."""
        cliente = Cliente(**datos)
        self.__clientes[cliente.identificacion] = cliente
        return cliente.describir()

    def _crear_servicio(self, clase, **datos):
        """Crea un servicio de cualquier subclase y lo guarda."""
        servicio = clase(**datos)
        self.__servicios[servicio.codigo] = servicio
        return servicio.describir_servicio()

    def _reservar(self, identificacion, codigo_servicio, **opciones):
        """Registra una reserva para un cliente y un servicio ya creados."""
        reserva = self.__reservas.registrar_reserva(self.__clientes[identificacion],
                                                    self.__servicios[codigo_servicio],
                                                    fecha_realizacion=self.__fecha_reserva, **opciones)
        return reserva

    # ------------------------------------------------------------------
    # Operaciones completas (cada una combina varios pasos)
    # ------------------------------------------------------------------
    def _reserva_completa_exitosa(self):
        """Registra, cotiza las 4 variantes de costo y confirma con 10 % de descuento."""
        reserva = self._reservar("1032456789", "SAL-100")
        costos = (reserva.calcular_costo(), reserva.calcular_costo(incluir_impuesto=True),
                  reserva.calcular_costo(descuento=10), reserva.calcular_costo(True, descuento=10))
        final = reserva.confirmar(descuento=10)
        return (f"{reserva.id} CONFIRMADA. Costos: básico ${costos[0]:,.0f}, con IVA ${costos[1]:,.0f}, "
                f"con descuento ${costos[2]:,.0f}, ambos ${costos[3]:,.0f} -> final ${final:,.0f}")

    def _reserva_confirmada_y_cancelada(self):
        """Registra un alquiler, lo confirma con IVA y luego lo cancela."""
        reserva = self._reservar("52789456", "EQU-100")
        final = reserva.confirmar()
        anterior = reserva.cancelar("el cliente cambió la fecha del evento")
        return f"{reserva.id}: confirmada por ${final:,.0f} y cancelada (estado previo {anterior})"

    def _reserva_cliente_inactivo(self):
        """Un cliente que pasa a INACTIVO no puede reservar."""
        self.__clientes["79123456"].cambiar_estado("INACTIVO", "cartera vencida")
        return self._reservar("79123456", "SAL-100")

    def _reserva_servicio_no_disponible(self):
        """La asesoría sale de servicio y luego se intenta reservar."""
        self.__servicios["ASE-100"].cambiar_estado("NO_DISPONIBLE", "especialista en vacaciones")
        return self._reservar("1032456789", "ASE-100")

    def _confirmar_reserva_cancelada(self):
        """Confirmar la reserva cancelada en la operación anterior (encadenamiento)."""
        cancelada = self.__reservas.listar_reservas("CANCELADA")[0]
        return self.__reservas.confirmar_reserva(cancelada.id)

    def _cancelar_dos_veces(self):
        """Cancelar otra vez la misma reserva."""
        cancelada = self.__reservas.listar_reservas("CANCELADA")[0]
        return self.__reservas.cancelar_reserva(cancelada.id)

    def _procesar_polimorfico(self):
        """Procesa todos los servicios (incluido el no disponible) de forma polimórfica."""
        resumen = procesar_servicios(list(self.__servicios.values()), impuesto=Servicio.IVA)
        return (f"{len(resumen['procesados'])} servicios procesados, {len(resumen['errores'])} rechazado(s); "
                f"total con IVA ${resumen['total']:,.0f}")

    def _error_inesperado(self):
        """Pide una reserva por una posición que no existe: IndexError de Python."""
        return self.__reservas.listar_reservas()[50]

    # ------------------------------------------------------------------
    # Guion de la simulación
    # ------------------------------------------------------------------
    def simular(self):
        """
        Ejecuta todas las operaciones en orden.

        Returns:
            list[dict]: Resultados de cada operación.
        """
        self.__log.info("===== INICIO DE LA SIMULACIÓN DE OPERACIONES =====", origen="Simulacion")

        # --- Clientes -------------------------------------------------------
        self.ejecutar("Registrar cliente válido (Ana Pérez)", EXITO, lambda: self._registrar_cliente(
            identificacion="1032456789", nombre="Ana Pérez", correo="ana@correo.com",
            telefono="300 123 4567", direccion="Calle 10 # 5-20"))
        self.ejecutar("Registrar cliente válido (Laura Gómez)", EXITO, lambda: self._registrar_cliente(
            identificacion=52789456, nombre="Laura Gómez", correo="Laura.Gomez@Empresa.co",
            telefono="+57 (601) 555-1234", direccion="Carrera 7 # 45-10"))
        self.ejecutar("Registrar cliente válido (Pedro Ruiz)", EXITO, lambda: self._registrar_cliente(
            identificacion="79123456", nombre="Pedro Ruiz", correo="pedro@correo.com",
            telefono="310 987 6543", direccion="Avenida 68 # 20-30"))
        self.ejecutar("Registrar cliente con correo inválido", ERROR, lambda: self._registrar_cliente(
            identificacion="1098765432", nombre="Carlos Díaz", correo="carlos.correo.com",
            telefono="315 000 1111", direccion="Calle 50 # 10-10"))
        self.ejecutar("Registrar cliente sin teléfono (parámetro faltante)", ERROR,
                      lambda: self._registrar_cliente(identificacion="1012345678", nombre="María León",
                                                      correo="maria@correo.com", direccion="Calle 1 # 2-3"))

        # --- Servicios ------------------------------------------------------
        self.ejecutar("Crear servicio ReservaSala válido", EXITO, lambda: self._crear_servicio(
            ReservaSala, codigo="SAL-100", nombre="Sala de juntas", descripcion="Sala con proyector y tablero",
            precio_base=20000, nombre_sala="Sala Andes", horas=3, capacidad=12, costo_hora=50000))
        self.ejecutar("Crear servicio AlquilerEquipo válido", EXITO, lambda: self._crear_servicio(
            AlquilerEquipo, codigo="EQU-100", nombre="Portátiles para capacitación",
            descripcion="Equipos Core i7 con software de oficina", precio_base=10000,
            tipo_equipo="Portátil", cantidad=5, dias=2, tarifa_diaria=30000))
        self.ejecutar("Crear servicio AsesoriaEspecializada válido", EXITO, lambda: self._crear_servicio(
            AsesoriaEspecializada, codigo="ASE-100", nombre="Asesoría en redes",
            descripcion="Diseño de red empresarial", precio_base=50000, tipo_asesoria="Redes",
            especialista="Carlos Gómez", horas=4, tarifa_hora=80000))
        self.ejecutar("Crear sala con horas negativas", ERROR, lambda: self._crear_servicio(
            ReservaSala, codigo="SAL-200", nombre="Auditorio", descripcion="Auditorio principal",
            precio_base=0, nombre_sala="Auditorio", horas=-2, capacidad=80, costo_hora=90000))
        self.ejecutar("Crear asesoría de un tipo que no se ofrece", ERROR, lambda: self._crear_servicio(
            AsesoriaEspecializada, codigo="ASE-200", nombre="Asesoría contable",
            descripcion="Revisión de estados financieros", precio_base=0, tipo_asesoria="Contabilidad",
            especialista="Rosa Mejía", horas=2, tarifa_hora=70000))

        # --- Reservas -------------------------------------------------------
        self.ejecutar("Reserva completa: registrar, cotizar y confirmar con descuento", EXITO,
                      self._reserva_completa_exitosa)
        self.ejecutar("Reserva de equipos: confirmar y cancelar", EXITO, self._reserva_confirmada_y_cancelada)
        self.ejecutar("Reservar con una duración que no coincide con el servicio", ERROR,
                      lambda: self._reservar("1032456789", "SAL-100", duracion=8))
        self.ejecutar("Reservar con una fecha pasada", ERROR, lambda: self.__reservas.registrar_reserva(
            self.__clientes["1032456789"], self.__servicios["SAL-100"], fecha_realizacion="2020-05-01"))
        self.ejecutar("Reservar con un cliente inactivo", ERROR, self._reserva_cliente_inactivo)
        self.ejecutar("Reservar un servicio no disponible", ERROR, self._reserva_servicio_no_disponible)
        self.ejecutar("Confirmar una reserva cancelada", ERROR, self._confirmar_reserva_cancelada)
        self.ejecutar("Cancelar una reserva ya cancelada", ERROR, self._cancelar_dos_veces)
        self.ejecutar("Buscar una reserva inexistente", ERROR, lambda: self.__reservas.buscar_reserva("RES-9999"))

        # --- Robustez general ----------------------------------------------
        self.ejecutar("Procesar todos los servicios (polimorfismo)", EXITO, self._procesar_polimorfico)
        self.ejecutar("Error inesperado de Python (posición inexistente)", ERROR, self._error_inesperado)

        self.__log.info(f"===== FIN DE LA SIMULACIÓN: {len(self.__resultados)} operaciones =====",
                        origen="Simulacion")
        return self.__resultados

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------
    @property
    def resultados(self):
        """list[dict]: Copia de los resultados (no se puede alterar la lista interna)."""
        return list(self.__resultados)

    def resumen(self):
        """
        Returns:
            dict: total, exitosas, errores_controlados, coinciden, reservas registradas.
        """
        return {
            "total": len(self.__resultados),
            "exitosas": sum(1 for f in self.__resultados if f["obtenido"] == EXITO),
            "errores_controlados": sum(1 for f in self.__resultados if f["obtenido"] == ERROR),
            "coinciden": sum(1 for f in self.__resultados if f["coincide"]),
            "clientes": len(self.__clientes),
            "servicios": len(self.__servicios),
            "reservas": len(self.__reservas),
        }

    def mostrar_resumen(self):
        """Imprime la tabla final de la simulación."""
        datos = self.resumen()
        print("\n" + "=" * 78)
        print(" RESUMEN DE LA SIMULACIÓN")
        print("=" * 78)
        for fila in self.__resultados:
            marca = "OK" if fila["coincide"] else "!!"
            print(f" {fila['numero']:02d} [{marca}] {fila['descripcion']:<62} {fila['obtenido']:<5} "
                  f"{fila['tipo_error']}")
        print("-" * 78)
        print(f" Operaciones: {datos['total']} | Éxitos: {datos['exitosas']} | "
              f"Errores controlados: {datos['errores_controlados']} | "
              f"Según lo esperado: {datos['coinciden']}/{datos['total']}")
        print(f" En memoria: {datos['clientes']} clientes, {datos['servicios']} servicios, "
              f"{datos['reservas']} reservas")
        print(f" La aplicación terminó sin interrupciones. Log: {self.__log.ruta}")
        print("=" * 78)


def main():
    """Punto de entrada: ejecuta la simulación protegiendo el programa completo."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 78)
    print(" SOFTWARE FJ - Simulación de operaciones del sistema")
    print("=" * 78)
    simulador = SimuladorOperaciones()
    simulador.simular()
    simulador.mostrar_resumen()


if __name__ == "__main__":
    main()
