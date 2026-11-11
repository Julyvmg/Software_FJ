"""
Módulo: pruebas_servicios.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 3 - Jerarquía y Polimorfismo de Servicios

Descripción:
    Pruebas de la jerarquía de servicios (Servicio, ReservaSala, AlquilerEquipo
    y AsesoriaEspecializada) con ``unittest``. Comprueban:

    1. La creación de cada servicio.            6. El manejo de errores con excepciones.
    2. El cálculo correcto de los costos.       7. Costo con impuestos y descuentos.
    3. La validación de parámetros incorrectos. 8. Servicios no disponibles.
    4. La sobrescritura de métodos.             9. La encapsulación.
    5. El funcionamiento del polimorfismo.     10. Que Servicio es abstracta.

    Durante las pruebas el log se escribe en un archivo temporal, así
    ``sistema.log`` no se llena con datos de prueba.

Ejecución:
    python pruebas_servicios.py               -> demostración en consola + pruebas
    python -m unittest pruebas_servicios -v   -> solo las pruebas
"""

# os y tempfile: archivo de log temporal para las pruebas.
import os
import sys
import tempfile
# unittest es el framework de pruebas incluido en Python.
import unittest

# Clases que se prueban.
from servicio import Servicio, procesar_servicios
from reserva_sala import ReservaSala
from alquiler_equipo import AlquilerEquipo
from asesoria_especializada import AsesoriaEspecializada
# Clase raíz del sistema, para comprobar la herencia.
from entidad_base import EntidadBase
# Excepciones esperadas.
from excepciones import (CalculoInconsistenteError, DatosServicioInvalidos, ErrorSistema, ErrorValidacion,
                         OperacionNoPermitidaError, ParametroFaltante, ServicioNoDisponibleError)
# Gestor de logs, para redirigirlo al archivo temporal.
from gestor_logs import GestorLogs


# ----------------------------------------------------------------------
# Funciones de apoyo: crean servicios válidos; cada prueba cambia solo lo que necesita.
# ----------------------------------------------------------------------
def crear_sala(**cambios):
    """Crea una ReservaSala válida, reemplazando los datos indicados."""
    datos = {"codigo": "SAL-100", "nombre": "Sala de juntas", "descripcion": "Sala con proyector y tablero",
             "precio_base": 20000, "nombre_sala": "Sala Andes", "horas": 3, "capacidad": 12,
             "costo_hora": 50000}
    return ReservaSala(**{**datos, **cambios})


def crear_alquiler(**cambios):
    """Crea un AlquilerEquipo válido, reemplazando los datos indicados."""
    datos = {"codigo": "EQU-100", "nombre": "Portátiles para capacitación", "descripcion": "Equipos Core i7",
             "precio_base": 10000, "tipo_equipo": "Portátil", "cantidad": 5, "dias": 2,
             "tarifa_diaria": 40000}
    return AlquilerEquipo(**{**datos, **cambios})


def crear_asesoria(**cambios):
    """Crea una AsesoriaEspecializada válida, reemplazando los datos indicados."""
    datos = {"codigo": "ASE-100", "nombre": "Auditoría de seguridad", "descripcion": "Revisión de la red interna",
             "precio_base": 0, "tipo_asesoria": "Seguridad", "especialista": "Laura Gómez", "horas": 4.5,
             "tarifa_hora": 120000}
    return AsesoriaEspecializada(**{**datos, **cambios})


class TestServicios(unittest.TestCase):
    """Pruebas de la jerarquía y el polimorfismo de servicios."""

    @classmethod
    def setUpClass(cls):
        """Antes de todas las pruebas: el log compartido se dirige a un archivo temporal."""
        descriptor, cls.ruta_log = tempfile.mkstemp(suffix=".log")
        os.close(descriptor)
        cls.gestor_original = GestorLogs._instancia
        GestorLogs._instancia = GestorLogs(cls.ruta_log)

    @classmethod
    def tearDownClass(cls):
        """Después de todas las pruebas: se restaura el gestor y se borra el archivo temporal."""
        GestorLogs._instancia = cls.gestor_original
        os.remove(cls.ruta_log)

    # 1 ----------------------------------------------------------------
    def test_01_creacion_de_cada_servicio(self):
        """Los tres servicios se crean con sus datos limpios y heredan de Servicio y EntidadBase."""
        sala = crear_sala(nombre="  Sala   de juntas ")
        alquiler = crear_alquiler(cantidad="5")          # Un texto numérico también se acepta.
        asesoria = crear_asesoria(tipo_asesoria="seguridad")
        # Datos comunes (heredados) y propios.
        self.assertEqual(sala.codigo, "SAL-100")
        self.assertEqual(sala.nombre, "Sala de juntas")
        self.assertEqual(sala.capacidad, 12)
        self.assertEqual(alquiler.cantidad, 5)
        self.assertEqual(asesoria.tipo_asesoria, "SEGURIDAD")
        # Estado inicial.
        for servicio in (sala, alquiler, asesoria):
            with self.subTest(servicio=servicio.tipo):
                self.assertEqual(servicio.estado, "DISPONIBLE")
                self.assertIsInstance(servicio, Servicio)
                self.assertIsInstance(servicio, EntidadBase)
        # Sin código se genera uno automático con el prefijo de cada clase.
        self.assertTrue(crear_sala(codigo=None).codigo.startswith("SAL-"))
        self.assertTrue(crear_alquiler(codigo=None).codigo.startswith("EQU-"))
        self.assertTrue(crear_asesoria(codigo=None).codigo.startswith("ASE-"))

    # 2 ----------------------------------------------------------------
    def test_02_calculo_de_costos(self):
        """Cada servicio calcula su costo con su propia fórmula."""
        # 20 000 + 3 h * 50 000 = 170 000
        self.assertEqual(crear_sala().calcular_costo(), 170000.0)
        # 10 000 + 5 equipos * 2 días * 40 000 = 410 000
        self.assertEqual(crear_alquiler().calcular_costo(), 410000.0)
        # 0 + 4.5 h * 120 000 = 540 000
        self.assertEqual(crear_asesoria().calcular_costo(), 540000.0)
        # Medias horas en la sala: 20 000 + 1.5 * 50 000 = 95 000
        self.assertEqual(crear_sala(horas=1.5).calcular_costo(), 95000.0)

    # 3 ----------------------------------------------------------------
    def test_03_validacion_de_parametros_incorrectos(self):
        """Datos fuera de las reglas de cada servicio lanzan DatosServicioInvalidos."""
        # (función creadora, campo, valor inválido)
        casos = [
            (crear_sala, "horas", 0), (crear_sala, "horas", -2), (crear_sala, "horas", 13),
            (crear_sala, "capacidad", 0), (crear_sala, "capacidad", 150), (crear_sala, "capacidad", 2.5),
            (crear_sala, "costo_hora", "abc"), (crear_sala, "nombre_sala", "  "),
            (crear_alquiler, "cantidad", 0), (crear_alquiler, "cantidad", 51), (crear_alquiler, "dias", 0),
            (crear_alquiler, "dias", 31), (crear_alquiler, "dias", 1.5), (crear_alquiler, "tarifa_diaria", 0),
            (crear_asesoria, "horas", 0), (crear_asesoria, "horas", 41), (crear_asesoria, "especialista", "Ab"),
            (crear_asesoria, "especialista", "Laura123"), (crear_asesoria, "tipo_asesoria", "Cocina"),
            (crear_asesoria, "precio_base", -1), (crear_asesoria, "nombre", "AB"),
            (crear_asesoria, "tarifa_hora", True),
        ]
        for creador, campo, valor in casos:
            with self.subTest(clase=creador.__name__, campo=campo, valor=valor):
                with self.assertRaises(DatosServicioInvalidos) as contexto:
                    creador(**{campo: valor})
                # El error indica exactamente qué campo falló.
                self.assertEqual(contexto.exception.campo, campo)

    # 4 ----------------------------------------------------------------
    def test_04_sobrescritura_de_metodos(self):
        """Cada subclase define su propia versión de los tres métodos abstractos."""
        for clase in (ReservaSala, AlquilerEquipo, AsesoriaEspecializada):
            for metodo in ("calcular_costo", "describir_servicio", "validar_parametros"):
                with self.subTest(clase=clase.__name__, metodo=metodo):
                    # El método está definido en la propia subclase (no es el de Servicio).
                    self.assertIn(metodo, clase.__dict__)
                    self.assertIsNot(getattr(clase, metodo), getattr(Servicio, metodo))
        # Las descripciones son distintas según el tipo.
        self.assertIn("Reserva de sala", crear_sala().describir_servicio())
        self.assertIn("Alquiler de 5", crear_alquiler().describir_servicio())
        self.assertIn("Asesoría en SEGURIDAD", crear_asesoria().describir_servicio())
        # describir() y str() de EntidadBase reutilizan describir_servicio().
        sala = crear_sala()
        self.assertEqual(str(sala), sala.describir_servicio())

    # 5 ----------------------------------------------------------------
    def test_05_polimorfismo(self):
        """procesar_servicios trata a todos los servicios igual y cada uno responde a su manera."""
        servicios = [crear_sala(), crear_alquiler(), crear_asesoria()]
        resultado = procesar_servicios(servicios)
        # Se procesaron los tres sin errores.
        self.assertEqual(len(resultado["procesados"]), 3)
        self.assertEqual(resultado["errores"], [])
        # Cada uno usó su propia fórmula de costo.
        costos = [fila["costo"] for fila in resultado["procesados"]]
        self.assertEqual(costos, [170000.0, 410000.0, 540000.0])
        self.assertEqual(resultado["total"], 1120000.0)
        # Los tipos reales se conservan.
        tipos = [fila["tipo"] for fila in resultado["procesados"]]
        self.assertEqual(tipos, ["ReservaSala", "AlquilerEquipo", "AsesoriaEspecializada"])

    # 6 ----------------------------------------------------------------
    def test_06_manejo_de_errores(self):
        """Faltantes, encadenamiento y lotes con errores que no detienen el programa."""
        # Un dato obligatorio sin entregar lanza ParametroFaltante (no TypeError).
        with self.assertRaises(ParametroFaltante) as faltante:
            crear_alquiler(dias=None)
        self.assertEqual(faltante.exception.campo, "dias")
        self.assertIn("AlquilerEquipo", str(faltante.exception))
        # Encadenamiento: el error propio guarda el ValueError original como causa.
        with self.assertRaises(DatosServicioInvalidos) as invalido:
            crear_sala(horas="tres")
        self.assertIsInstance(invalido.exception.__cause__, ValueError)
        # La jerarquía de excepciones es la del sistema.
        self.assertTrue(issubclass(DatosServicioInvalidos, ErrorValidacion))
        self.assertTrue(issubclass(ServicioNoDisponibleError, ErrorSistema))
        self.assertTrue(issubclass(CalculoInconsistenteError, ErrorSistema))
        # Lote mixto: los errores se capturan y el ciclo continúa.
        creados, errores = [], []
        for creador, cambios in [(crear_sala, {}), (crear_sala, {"horas": 0}), (crear_alquiler, {}),
                                 (crear_asesoria, {"especialista": None}), (crear_asesoria, {})]:
            try:
                servicio = creador(**cambios)
            except ErrorValidacion as error:
                GestorLogs.obtener_instancia().error("Creación de servicio rechazada", error, origen="test")
                errores.append(error)
            else:
                creados.append(servicio)
        self.assertEqual((len(creados), len(errores)), (3, 2))
        # Los errores y las creaciones quedaron en el log.
        log = GestorLogs.obtener_instancia()
        self.assertTrue(any("DatosServicioInvalidos" in linea for linea in log.leer_registros("ERROR")))
        self.assertTrue(any("Servicio creado" in linea for linea in log.leer_registros("INFO")))

    # 7 ----------------------------------------------------------------
    def test_07_costo_total_con_parametros_opcionales(self):
        """calcular_costo_total simula sobrecarga con impuesto y descuento opcionales."""
        sala = crear_sala()                                               # Subtotal 170 000.
        self.assertEqual(sala.calcular_costo_total(), 170000.0)
        self.assertEqual(sala.calcular_costo_total(impuesto=Servicio.IVA), 202300.0)
        self.assertEqual(sala.calcular_costo_total(descuento=0.10), 153000.0)
        self.assertEqual(sala.calcular_costo_total(Servicio.IVA, 0.10), 182070.0)
        # Tasas fuera de rango son rechazadas.
        for impuesto, descuento in ((-0.1, 0), (1.5, 0), (0, 1), (0, "x")):
            with self.subTest(impuesto=impuesto, descuento=descuento):
                with self.assertRaises(DatosServicioInvalidos):
                    sala.calcular_costo_total(impuesto, descuento)

    # 8 ----------------------------------------------------------------
    def test_08_servicio_no_disponible(self):
        """Un servicio NO_DISPONIBLE se rechaza en el procesamiento sin detener a los demás."""
        alquiler = crear_alquiler()
        alquiler.cambiar_estado("NO_DISPONIBLE", motivo="equipos en mantenimiento")
        self.assertFalse(alquiler.esta_disponible)
        with self.assertRaises(ServicioNoDisponibleError):
            alquiler.verificar_disponibilidad()
        # No se puede pasar al mismo estado (regla de EntidadBase).
        with self.assertRaises(OperacionNoPermitidaError):
            alquiler.cambiar_estado("NO_DISPONIBLE")
        # En un lote, el no disponible y el objeto ajeno se reportan; los otros se procesan.
        resultado = procesar_servicios([crear_sala(), alquiler, "no soy un servicio", crear_asesoria()])
        self.assertEqual(len(resultado["procesados"]), 2)
        self.assertEqual(len(resultado["errores"]), 2)
        self.assertIn("SER-001", resultado["errores"][0])

    # 9 ----------------------------------------------------------------
    def test_09_encapsulacion(self):
        """Los datos privados solo se cambian por setters que validan."""
        sala = crear_sala()
        # El precio base tiene setter que valida.
        sala.precio_base = 30000
        self.assertEqual(sala.calcular_costo(), 180000.0)
        with self.assertRaises(DatosServicioInvalidos):
            sala.precio_base = -5
        self.assertEqual(sala.precio_base, 30000)          # Se conservó el valor anterior.
        # Los demás datos son de solo lectura.
        with self.assertRaises(AttributeError):
            sala.horas = 100
        with self.assertRaises(AttributeError):
            sala.codigo = "OTRO"
        # Los atributos son privados (name mangling).
        self.assertFalse(hasattr(sala, "__horas"))

    # 10 ---------------------------------------------------------------
    def test_10_servicio_es_abstracta(self):
        """Servicio no se puede instanciar, ni tampoco una subclase incompleta."""
        with self.assertRaises(TypeError):
            Servicio("SER-1", "Genérico", "Servicio genérico", 1000)

        # Subclase que olvida implementar validar_parametros().
        class ServicioIncompleto(Servicio):
            def calcular_costo(self):
                return 0

            def describir_servicio(self):
                return "incompleto"

        with self.assertRaises(TypeError):
            ServicioIncompleto("SER-2", "Incompleto", "Le falta un método", 0)


# ----------------------------------------------------------------------
# Demostración en consola (para la sustentación)
# ----------------------------------------------------------------------
def demostracion():
    """Muestra en consola la creación, el polimorfismo y el manejo de errores."""
    print("=" * 78)
    print(" SOFTWARE FJ - Demostración de la jerarquía de servicios (Estudiante 3)")
    print("=" * 78)

    # 1. Creación de servicios válidos e inválidos.
    print("\n1) Creación de servicios")
    servicios = []
    intentos = [
        ("Sala válida", crear_sala, {}),
        ("Alquiler válido", crear_alquiler, {}),
        ("Asesoría válida", crear_asesoria, {}),
        ("Sala con 0 horas", crear_sala, {"horas": 0}),
        ("Alquiler sin días", crear_alquiler, {"dias": None}),
        ("Asesoría de tipo inexistente", crear_asesoria, {"tipo_asesoria": "Cocina"}),
    ]
    for etiqueta, creador, cambios in intentos:
        try:
            servicio = creador(**cambios)
        except ErrorSistema as error:
            GestorLogs.obtener_instancia().error(f"No se creó: {etiqueta}", error, origen="demostracion")
            print(f"   [X] {etiqueta}: {error}")
        else:
            servicios.append(servicio)
            print(f"   [OK] {etiqueta}: {servicio.codigo}")

    # 2. Polimorfismo: la misma función procesa los tres tipos.
    print("\n2) Polimorfismo con procesar_servicios() (con IVA del 19 %)")
    servicios[1].cambiar_estado("NO_DISPONIBLE", motivo="mantenimiento")   # Se fuerza un error.
    resultado = procesar_servicios(servicios, impuesto=Servicio.IVA)
    for fila in resultado["procesados"]:
        print(f"   {fila['tipo']:<22} {fila['descripcion']}")
        print(f"   {'':<22} -> subtotal ${fila['costo']:,.2f} | total con IVA ${fila['costo_final']:,.2f}")
    for error in resultado["errores"]:
        print(f"   [X] {error}")
    print(f"   TOTAL: ${resultado['total']:,.2f}")
    print("\n   El programa siguió funcionando a pesar de los errores (ver sistema.log).\n")


if __name__ == "__main__":
    # Consola en UTF-8 para que se vean tildes y ñ en Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    demostracion()
    unittest.main(verbosity=2)
