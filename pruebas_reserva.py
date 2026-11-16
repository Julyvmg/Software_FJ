"""
Módulo: pruebas_reserva.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 4 - Módulo de Reservas y Métodos Sobrecargados

Descripción:
    Pruebas del módulo de reservas con ``unittest``. Usan las clases reales de
    los compañeros (Cliente, ReservaSala, AlquilerEquipo, AsesoriaEspecializada).

    Datos de prueba y resultados esperados:
        Sala:     precio base 20.000 + 3 h * 50.000        = 170.000  (costo básico)
                  con IVA 19 %:        170.000 * 1,19       = 202.300
                  con descuento 10 %:  170.000 * 0,90       = 153.000
                  descuento + IVA:     170.000 * 0,90 * 1,19 = 182.070
                  impuesto 8 %:        170.000 * 1,08       = 183.600
        Alquiler: 10.000 + 5 equipos * 2 días * 30.000     = 310.000
        Asesoría: 50.000 + 4 h * 80.000                    = 370.000

    Durante las pruebas el log se escribe en un archivo temporal.

Ejecución:
    python pruebas_reserva.py               -> demostración en consola + pruebas
    python -m unittest pruebas_reserva -v   -> solo las pruebas
"""

import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

from cliente import Cliente
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
from reserva import GestorReservas, Reserva
from excepciones import ErrorSistema, ErrorValidacion, ServicioNoDisponibleError
from excepciones_reserva import (ErrorCancelacionReserva, ErrorConfirmacionReserva, EstadoReservaError,
                                 ReservaInvalidaError, ReservaNoEncontradaError)
from gestor_logs import GestorLogs


# ----------------------------------------------------------------------
# Funciones de apoyo: crean objetos válidos de los compañeros.
# ----------------------------------------------------------------------
def crear_cliente(**cambios):
    """Cliente válido (Estudiante 2)."""
    datos = {"identificacion": "1032456789", "nombre": "Ana Pérez", "correo": "ana@correo.com",
             "telefono": "300 123 4567", "direccion": "Calle 10 # 5-20"}
    return Cliente(**{**datos, **cambios})


def crear_sala(**cambios):
    """ReservaSala válida (Estudiante 3). Costo básico: 170.000."""
    datos = {"codigo": "SAL-100", "nombre": "Sala de juntas", "descripcion": "Sala con proyector y tablero",
             "precio_base": 20000, "nombre_sala": "Sala Andes", "horas": 3, "capacidad": 12,
             "costo_hora": 50000}
    return ReservaSala(**{**datos, **cambios})


def crear_alquiler():
    """AlquilerEquipo válido. Costo básico: 310.000."""
    return AlquilerEquipo("EQU-100", "Portátiles para capacitación", "Equipos Core i7", 10000,
                          tipo_equipo="Portátil", cantidad=5, dias=2, tarifa_diaria=30000)


def crear_asesoria():
    """AsesoriaEspecializada válida. Costo básico: 370.000."""
    return AsesoriaEspecializada("ASE-100", "Asesoría en redes", "Diseño de red empresarial", 50000,
                                 tipo_asesoria="Redes", especialista="Carlos Gómez", horas=4,
                                 tarifa_hora=80000)


class PruebasReserva(unittest.TestCase):
    """Pruebas de la clase Reserva y de GestorReservas."""

    @classmethod
    def setUpClass(cls):
        """Antes de todas las pruebas: el log se redirige a un archivo temporal."""
        descriptor, cls.ruta_log = tempfile.mkstemp(suffix=".log")
        os.close(descriptor)
        cls.gestor_original = GestorLogs._instancia
        GestorLogs._instancia = GestorLogs(cls.ruta_log)

    @classmethod
    def tearDownClass(cls):
        """Después de todas las pruebas: se restaura el gestor y se borra el archivo temporal."""
        GestorLogs._instancia = cls.gestor_original
        os.remove(cls.ruta_log)

    def setUp(self):
        """Antes de cada prueba: un cliente, una sala y una reserva PENDIENTE nuevos."""
        self.cliente = crear_cliente()
        self.sala = crear_sala()
        self.reserva = Reserva(self.cliente, self.sala)

    # 1 ----------------------------------------------------------------
    def test_01_crear_reserva(self):
        """Se crea asociada al cliente y al servicio, en estado PENDIENTE."""
        self.assertIs(self.reserva.cliente, self.cliente)
        self.assertIs(self.reserva.servicio, self.sala)
        self.assertTrue(self.reserva.id.startswith("RES-"))
        self.assertEqual(self.reserva.consultar_estado(), "PENDIENTE")
        self.assertEqual(self.reserva.duracion, 3.0)              # Tomada de sala.horas.
        self.assertEqual(self.reserva.unidad_duracion, "horas")
        self.assertEqual(self.reserva.fecha_realizacion, date.today())
        self.assertEqual(self.reserva.costo_total, 170000.0)
        datos = self.reserva.consultar_datos()
        self.assertEqual(datos["cliente"], "1032456789")
        self.assertEqual(datos["servicio"], "SAL-100")

    def test_01b_reserva_con_otros_servicios(self):
        """Funciona con los tres tipos de servicio (polimorfismo)."""
        alquiler = Reserva(self.cliente, crear_alquiler(), duracion=2, fecha_realizacion="2099-12-31")
        asesoria = Reserva(self.cliente, crear_asesoria())
        self.assertEqual((alquiler.duracion, alquiler.unidad_duracion), (2.0, "días"))
        self.assertEqual(alquiler.calcular_costo(), 310000.0)
        self.assertEqual(asesoria.calcular_costo(), 370000.0)
        self.assertEqual(alquiler.fecha_realizacion, date(2099, 12, 31))

    # 2 ----------------------------------------------------------------
    def test_02_confirmar_pendiente(self):
        """Confirmar una PENDIENTE la deja CONFIRMADA y fija el costo final con IVA."""
        costo = self.reserva.confirmar()
        self.assertEqual(costo, 202300.0)
        self.assertEqual(self.reserva.estado, "CONFIRMADA")
        self.assertEqual(self.reserva.costo_total, 202300.0)

    # 3 ----------------------------------------------------------------
    def test_03_cancelar(self):
        """Se puede cancelar una reserva pendiente y una confirmada."""
        self.assertEqual(self.reserva.cancelar("cliente desistió"), "PENDIENTE")
        self.assertEqual(self.reserva.estado, "CANCELADA")
        otra = Reserva(self.cliente, self.sala)
        otra.confirmar()
        self.assertEqual(otra.cancelar(), "CONFIRMADA")
        self.assertEqual(otra.estado, "CANCELADA")

    # 4 ----------------------------------------------------------------
    def test_04_no_confirmar_cancelada(self):
        """Confirmar una cancelada lanza ErrorConfirmacionReserva y no cambia nada."""
        self.reserva.cancelar()
        with self.assertRaises(ErrorConfirmacionReserva):
            self.reserva.confirmar()
        self.assertEqual(self.reserva.estado, "CANCELADA")
        self.assertEqual(self.reserva.costo_total, 170000.0)

    def test_04b_no_confirmar_dos_veces(self):
        """Una reserva ya confirmada no se vuelve a confirmar."""
        self.reserva.confirmar()
        with self.assertRaises(ErrorConfirmacionReserva):
            self.reserva.confirmar()

    def test_04c_transicion_bloqueada_directamente(self):
        """Aunque se llame a cambiar_estado() directamente, CANCELADA -> CONFIRMADA se impide."""
        self.reserva.cancelar()
        with self.assertRaises(EstadoReservaError):
            self.reserva.cambiar_estado("CONFIRMADA")

    # 5 ----------------------------------------------------------------
    def test_05_no_cancelar_dos_veces(self):
        """Cancelar una reserva ya cancelada lanza ErrorCancelacionReserva."""
        self.reserva.cancelar()
        with self.assertRaises(ErrorCancelacionReserva):
            self.reserva.cancelar()

    # 6 a 9 ------------------------------------------------------------
    def test_06_costo_basico(self):
        """Variante 1: precio base + horas * costo hora = 20.000 + 3 * 50.000."""
        self.assertEqual(self.reserva.calcular_costo(), 170000.0)

    def test_07_costo_con_impuesto(self):
        """Variante 2: IVA por defecto (19 %) y un impuesto configurable (8 %)."""
        self.assertEqual(self.reserva.calcular_costo(incluir_impuesto=True), 202300.0)
        self.assertEqual(self.reserva.calcular_costo(incluir_impuesto=True, porcentaje_impuesto=8), 183600.0)
        # Si incluir_impuesto es False, el porcentaje no se aplica.
        self.assertEqual(self.reserva.calcular_costo(porcentaje_impuesto=8), 170000.0)

    def test_08_costo_con_descuento(self):
        """Variante 3: 10 % de descuento."""
        self.assertEqual(self.reserva.calcular_costo(descuento=10), 153000.0)

    def test_09_costo_con_impuesto_y_descuento(self):
        """Variante 4: primero el descuento y luego el impuesto: 170.000 * 0,90 * 1,19."""
        self.assertEqual(self.reserva.calcular_costo(incluir_impuesto=True, descuento=10), 182070.0)
        # Confirmar con descuento guarda ese mismo valor como costo final.
        self.assertEqual(self.reserva.confirmar(descuento=10), 182070.0)

    def test_09b_parametros_de_costo_invalidos(self):
        """Porcentajes fuera de rango o de tipo incorrecto."""
        for argumentos in ({"descuento": -5}, {"descuento": 100}, {"descuento": "diez"},
                           {"incluir_impuesto": True, "porcentaje_impuesto": 150},
                           {"incluir_impuesto": "si"}):
            with self.subTest(argumentos=argumentos):
                with self.assertRaises(ReservaInvalidaError):
                    self.reserva.calcular_costo(**argumentos)

    # 10 ---------------------------------------------------------------
    def test_10_errores_de_registro(self):
        """try/except: cada dato inválido se rechaza con ReservaInvalidaError."""
        casos = {
            "sin cliente": lambda: Reserva(None, self.sala),
            "cliente no es Cliente": lambda: Reserva("Ana Pérez", self.sala),
            "servicio no es Servicio": lambda: Reserva(self.cliente, "Sala de juntas"),
            "duración negativa": lambda: Reserva(self.cliente, self.sala, duracion=-2),
            "duración cero": lambda: Reserva(self.cliente, self.sala, duracion=0),
            "duración texto": lambda: Reserva(self.cliente, self.sala, duracion="tres"),
            "duración distinta al servicio": lambda: Reserva(self.cliente, self.sala, duracion=5),
            "fecha pasada": lambda: Reserva(self.cliente, self.sala, fecha_realizacion="2020-01-01"),
            "fecha mal escrita": lambda: Reserva(self.cliente, self.sala, fecha_realizacion="31/12/2099"),
        }
        for nombre, crear in casos.items():
            with self.subTest(caso=nombre):
                try:
                    crear()
                except ReservaInvalidaError as error:
                    # También es un ErrorValidacion y un ErrorSistema (jerarquía del proyecto).
                    self.assertIsInstance(error, ErrorValidacion)
                    self.assertEqual(error.codigo, "RES-001")
                else:
                    self.fail(f"No se rechazó: {nombre}")

    def test_10b_cliente_inactivo_y_servicio_no_disponible(self):
        """Cliente INACTIVO o servicio NO_DISPONIBLE impiden registrar."""
        inactivo = crear_cliente(identificacion="99887766")
        inactivo.cambiar_estado("INACTIVO")
        with self.assertRaises(ReservaInvalidaError):
            Reserva(inactivo, self.sala)
        sala_cerrada = crear_sala(codigo="SAL-200")
        sala_cerrada.cambiar_estado("NO_DISPONIBLE")
        with self.assertRaises(ReservaInvalidaError) as contexto:
            Reserva(self.cliente, sala_cerrada)
        self.assertIsInstance(contexto.exception.__cause__, ServicioNoDisponibleError)

    def test_10c_gestor_reservas(self):
        """GestorReservas registra, busca y lanza ReservaNoEncontradaError."""
        gestor = GestorReservas()
        reserva = gestor.registrar_reserva(self.cliente, self.sala)
        self.assertIs(gestor.buscar_reserva(reserva.id), reserva)
        self.assertEqual(gestor.confirmar_reserva(reserva.id), 202300.0)
        self.assertEqual(len(gestor.listar_reservas("confirmada")), 1)
        with self.assertRaises(ReservaNoEncontradaError):
            gestor.buscar_reserva("RES-9999")
        with self.assertRaises(ReservaInvalidaError):
            gestor.registrar_reserva(self.cliente, self.sala, duracion=-1)
        self.assertEqual(len(gestor), 1)              # La inválida no se guardó.

    # 11 ---------------------------------------------------------------
    def test_11_else_solo_si_hay_exito(self):
        """try/except/else: si la confirmación falla, el else NO guarda el costo final."""
        self.sala.cambiar_estado("NO_DISPONIBLE")    # El servicio se cierra después de reservar.
        with self.assertRaises(ErrorConfirmacionReserva):
            self.reserva.confirmar(descuento=10)
        self.assertEqual(self.reserva.estado, "PENDIENTE")
        self.assertEqual(self.reserva.costo_total, 170000.0)     # No se ejecutó el else.
        self.sala.cambiar_estado("DISPONIBLE")
        self.reserva.confirmar(descuento=10)                       # Ahora sí: el else guarda el costo.
        self.assertEqual(self.reserva.costo_total, 182070.0)

    def test_11b_finally_siempre_registra(self):
        """try/except/finally: el seguimiento se escribe en el log con éxito y con error."""
        log = GestorLogs.obtener_instancia()
        self.reserva.cancelar()
        with self.assertRaises(ErrorCancelacionReserva):
            self.reserva.cancelar()
        registros = [linea for linea in log.leer_registros("INFO")
                     if f"cancelación de la reserva {self.reserva.id} " in linea]
        self.assertEqual(len(registros), 2)
        self.assertIn("EXITOSA", registros[0])
        self.assertIn("RECHAZADA", registros[1])

    # 12 ---------------------------------------------------------------
    def test_12_encadenamiento(self):
        """raise ... from error: la causa original queda en __cause__."""
        self.reserva.cancelar()
        with self.assertRaises(ErrorConfirmacionReserva) as confirmar:
            self.reserva.confirmar()
        self.assertIsInstance(confirmar.exception.__cause__, EstadoReservaError)
        self.assertEqual(confirmar.exception.__cause__.estado_actual, "CANCELADA")

        with self.assertRaises(ErrorCancelacionReserva) as cancelar:
            self.reserva.cancelar()
        self.assertIsInstance(cancelar.exception.__cause__, EstadoReservaError)

        with self.assertRaises(ReservaInvalidaError) as duracion:
            Reserva(self.cliente, self.sala, duracion="tres")
        self.assertIsInstance(duracion.exception.__cause__, ValueError)

        # Todas pertenecen a la jerarquía del sistema.
        self.assertIsInstance(confirmar.exception, ErrorSistema)

    def test_13_encapsulamiento(self):
        """Los datos son de solo lectura."""
        with self.assertRaises(AttributeError):
            self.reserva.costo_total = 0
        with self.assertRaises(AttributeError):
            self.reserva.cliente = None


# ----------------------------------------------------------------------
# Demostración en consola (para la sustentación)
# ----------------------------------------------------------------------
def mostrar(titulo, esperado, obtenido):
    """Imprime una línea con el valor esperado, el obtenido y si coinciden."""
    marca = "OK" if esperado == obtenido else "X "
    print(f"   [{marca}] {titulo}: esperado {esperado!r} | obtenido {obtenido!r}")


def demostracion():
    """Recorre los escenarios principales mostrando los resultados."""
    print("=" * 78)
    print(" SOFTWARE FJ - Módulo de Reservas (Estudiante 4)")
    print("=" * 78)
    gestor = GestorReservas()
    cliente = crear_cliente()
    sala = crear_sala()

    print("\n1. Registro de reserva")
    reserva = gestor.registrar_reserva(cliente, sala, fecha_realizacion=date.today() + timedelta(days=7))
    print(f"   {reserva}")

    print("\n2. Sobrecarga simulada de calcular_costo()")
    mostrar("calcular_costo()                        ", 170000.0, reserva.calcular_costo())
    mostrar("calcular_costo(incluir_impuesto=True)   ", 202300.0, reserva.calcular_costo(incluir_impuesto=True))
    mostrar("calcular_costo(descuento=10)            ", 153000.0, reserva.calcular_costo(descuento=10))
    mostrar("calcular_costo(True, descuento=10)      ", 182070.0,
            reserva.calcular_costo(incluir_impuesto=True, descuento=10))

    print("\n3. try/except al registrar con datos inválidos")
    for etiqueta, duracion in (("duración -2", -2), ("duración 'tres'", "tres"), ("duración 5 (sala de 3 h)", 5)):
        try:
            gestor.registrar_reserva(cliente, sala, duracion=duracion)
        except ReservaInvalidaError as error:
            print(f"   [X] {etiqueta}: {error}")

    print("\n4. try/except/else: confirmación")
    costo = gestor.confirmar_reserva(reserva.id, descuento=10)
    print(f"   Confirmada. Estado: {reserva.consultar_estado()} | costo final: ${costo:,.2f}")

    print("\n5. try/except/finally: cancelación (el finally siempre deja rastro en el log)")
    gestor.cancelar_reserva(reserva.id, motivo="cambio de agenda")
    print(f"   Cancelada. Estado: {reserva.consultar_estado()}")
    try:
        gestor.cancelar_reserva(reserva.id)
    except ErrorCancelacionReserva as error:
        print(f"   [X] Segundo intento: {error}")

    print("\n6. Encadenamiento: confirmar una reserva cancelada")
    try:
        reserva.confirmar()
    except ErrorConfirmacionReserva as error:
        print(f"   Error lanzado : {type(error).__name__}: {error}")
        print(f"   Causa original: {type(error.__cause__).__name__}: {error.__cause__}")

    print("\n7. Reserva inexistente")
    try:
        gestor.buscar_reserva("RES-9999")
    except ReservaNoEncontradaError as error:
        print(f"   [X] {error}")

    print(f"\n   Eventos registrados en: {GestorLogs.obtener_instancia().ruta}")
    print("=" * 78)


if __name__ == "__main__":
    # Consola en UTF-8 para que se vean tildes y ñ en Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    demostracion()
    print("\nEjecutando pruebas unitarias...\n")
    unittest.main(verbosity=2)
