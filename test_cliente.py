"""
Módulo: test_cliente.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 2 - Módulo de Gestión de Clientes

Descripción:
    Pruebas unitarias de la clase ``Cliente`` con ``unittest``. Los métodos se
    numeran (test_01, test_02...) para que se ejecuten en orden secuencial.

    Durante las pruebas el gestor de logs escribe en un archivo temporal, así
    el archivo real ``sistema.log`` no se llena con datos de prueba.

Ejecución:
    python -m unittest test_cliente -v
"""

# os se usa para borrar el archivo de log temporal al terminar.
import os
# tempfile crea un archivo temporal para el log de las pruebas.
import tempfile
# unittest es el framework de pruebas incluido en Python.
import unittest

# Clase que se prueba.
from cliente import Cliente
# Excepciones que deben lanzarse en cada caso.
from excepciones import DatosClienteInvalidos, ErrorSistema, ErrorValidacion, ParametroFaltante
# Gestor de logs, para redirigirlo al archivo temporal.
from gestor_logs import GestorLogs


class TestCliente(unittest.TestCase):
    """Pruebas de creación, validación, modificación y manejo de errores de Cliente."""

    @classmethod
    def setUpClass(cls):
        """Antes de todas las pruebas: el log compartido se dirige a un archivo temporal."""
        # Se crea un archivo temporal vacío y se cierra su descriptor (solo se necesita la ruta).
        descriptor, cls.ruta_log = tempfile.mkstemp(suffix=".log")
        # Se cierra el descriptor para que GestorLogs pueda abrir el archivo en Windows.
        os.close(descriptor)
        # Se guarda el gestor original para restaurarlo al final.
        cls.gestor_original = GestorLogs._instancia
        # Se reemplaza la instancia compartida por una que escribe en el archivo temporal.
        GestorLogs._instancia = GestorLogs(cls.ruta_log)

    @classmethod
    def tearDownClass(cls):
        """Después de todas las pruebas: se restaura el gestor y se borra el archivo temporal."""
        # Se devuelve el gestor original.
        GestorLogs._instancia = cls.gestor_original
        # Se elimina el archivo temporal.
        os.remove(cls.ruta_log)

    def setUp(self):
        """Antes de cada prueba: datos válidos de referencia."""
        # Diccionario con datos correctos; cada prueba cambia solo el dato que quiere probar.
        self.datos = {
            "identificacion": "1032456789",
            "nombre": "Ana María Pérez",
            "correo": "ana.perez@correo.com",
            "telefono": "+57 300 123 4567",
            "direccion": "Calle 10 # 5-20, Bogotá",
        }

    def crear(self, **cambios):
        """
        Crea un cliente con los datos válidos, reemplazando los indicados.

        Args:
            **cambios: Datos que se quieren modificar (ej. nombre="").

        Returns:
            Cliente: El cliente creado.
        """
        # Se copian los datos válidos y se aplican los cambios.
        datos = {**self.datos, **cambios}
        # Se crea el cliente con esos datos.
        return Cliente(**datos)

    # 1 ----------------------------------------------------------------
    def test_01_creacion_correcta(self):
        """Un cliente con datos válidos se crea con sus datos limpios."""
        # Se crea con espacios sobrantes y correo en mayúsculas para probar la limpieza.
        cliente = self.crear(nombre="  Ana   María Pérez ", correo=" Ana.Perez@Correo.com ")
        # La identificación es el ID de la entidad.
        self.assertEqual(cliente.identificacion, "1032456789")
        self.assertEqual(cliente.id, "1032456789")
        # Se quitaron los espacios de los extremos y los dobles internos.
        self.assertEqual(cliente.nombre, "Ana María Pérez")
        # El correo se guardó limpio y en minúsculas.
        self.assertEqual(cliente.correo, "ana.perez@correo.com")
        # Teléfono y dirección se guardaron igual.
        self.assertEqual(cliente.telefono, "+57 300 123 4567")
        self.assertEqual(cliente.direccion, "Calle 10 # 5-20, Bogotá")
        # El estado inicial es ACTIVO.
        self.assertEqual(cliente.estado, "ACTIVO")
        # La identificación también se acepta como número entero.
        self.assertEqual(self.crear(identificacion=1032456789).identificacion, "1032456789")

    # 2 ----------------------------------------------------------------
    def test_02_nombre_vacio(self):
        """Un nombre vacío, con solo espacios o con números es rechazado."""
        # Se prueban varios nombres inválidos.
        for nombre in ("", "   ", "Ab", "Ana123", 12345):
            # subTest muestra cuál valor falló si alguno no lanza el error.
            with self.subTest(nombre=nombre):
                # Debe lanzarse DatosClienteInvalidos.
                with self.assertRaises(DatosClienteInvalidos) as contexto:
                    self.crear(nombre=nombre)
                # El error indica el campo afectado.
                self.assertEqual(contexto.exception.campo, "nombre")

    # 3 ----------------------------------------------------------------
    def test_03_identificacion_faltante(self):
        """Sin identificación se lanza ParametroFaltante; con formato malo, DatosClienteInvalidos."""
        # Se quita la identificación de los datos.
        del self.datos["identificacion"]
        # Crear el cliente sin ella debe lanzar ParametroFaltante (no TypeError).
        with self.assertRaises(ParametroFaltante) as contexto:
            Cliente(**self.datos)
        # El error indica el campo que falta.
        self.assertEqual(contexto.exception.campo, "identificacion")
        # Identificaciones entregadas pero inválidas.
        for identificacion in ("", "  ", "12345", "ABC123456", "1234567890123", True):
            # Cada una debe ser rechazada como dato inválido.
            with self.subTest(identificacion=identificacion):
                with self.assertRaises(DatosClienteInvalidos):
                    self.crear(identificacion=identificacion)

    # 4 ----------------------------------------------------------------
    def test_04_correo_invalido(self):
        """Los correos sin formato usuario@dominio.ext son rechazados."""
        # Correos con distintos errores de formato.
        for correo in ("", "anacorreo.com", "ana@", "@correo.com", "ana@correo", "ana@@correo.com",
                       "ana perez@correo.com", "ana@correo..com", "ana@correo.c"):
            # Cada uno debe lanzar DatosClienteInvalidos en el campo correo.
            with self.subTest(correo=correo):
                with self.assertRaises(DatosClienteInvalidos) as contexto:
                    self.crear(correo=correo)
                self.assertEqual(contexto.exception.campo, "correo")

    # 5 ----------------------------------------------------------------
    def test_05_telefono_incorrecto(self):
        """Teléfonos con letras, símbolos o cantidad de dígitos incorrecta son rechazados."""
        # Teléfonos inválidos.
        for telefono in ("", "300-ABC-4567", "300#1234567", "57+3001234567", "12345", "1" * 16, 3001234567):
            # Cada uno debe lanzar DatosClienteInvalidos en el campo telefono.
            with self.subTest(telefono=telefono):
                with self.assertRaises(DatosClienteInvalidos) as contexto:
                    self.crear(telefono=telefono)
                self.assertEqual(contexto.exception.campo, "telefono")
        # Formatos válidos que sí deben aceptarse.
        for telefono in ("3001234567", "(601) 555-1234", "+57 300 123 4567"):
            with self.subTest(telefono_valido=telefono):
                self.assertEqual(self.crear(telefono=telefono).telefono, telefono)

    # 6 ----------------------------------------------------------------
    def test_06_direccion_vacia(self):
        """Una dirección vacía o demasiado corta es rechazada."""
        # Direcciones inválidas.
        for direccion in ("", "    ", "Cl 1"):
            with self.subTest(direccion=direccion):
                with self.assertRaises(DatosClienteInvalidos) as contexto:
                    self.crear(direccion=direccion)
                self.assertEqual(contexto.exception.campo, "direccion")
        # Una dirección None (faltante) lanza ParametroFaltante.
        with self.assertRaises(ParametroFaltante):
            self.crear(direccion=None)

    # 7 ----------------------------------------------------------------
    def test_07_modificacion_correcta(self):
        """Los setters aceptan datos válidos y los guardan limpios."""
        # Se crea un cliente válido.
        cliente = self.crear()
        # Se modifican sus datos mediante los setters.
        cliente.nombre = "  Ana María Pérez Gómez  "
        cliente.correo = "ANA@EMPRESA.CO"
        cliente.telefono = "601 555 1234"
        cliente.direccion = "Carrera 7 # 32-16"
        # Los nuevos valores quedaron guardados y limpios.
        self.assertEqual(cliente.nombre, "Ana María Pérez Gómez")
        self.assertEqual(cliente.correo, "ana@empresa.co")
        self.assertEqual(cliente.telefono, "601 555 1234")
        self.assertEqual(cliente.direccion, "Carrera 7 # 32-16")
        # El cliente sigue siendo válido.
        cliente.validar()
        # El diccionario refleja los cambios.
        self.assertEqual(cliente.a_diccionario()["correo"], "ana@empresa.co")

    # 8 ----------------------------------------------------------------
    def test_08_rechazo_modificaciones_invalidas(self):
        """Una modificación inválida lanza error y conserva el valor anterior."""
        # Se crea un cliente válido y se guardan sus datos originales.
        cliente = self.crear()
        originales = cliente.a_diccionario()
        # Pares (atributo, valor inválido) que deben ser rechazados.
        cambios_invalidos = [("nombre", ""), ("correo", "sin-arroba"), ("telefono", "abc"),
                             ("direccion", "  "), ("nombre", None)]
        # Se intenta cada cambio.
        for atributo, valor in cambios_invalidos:
            with self.subTest(atributo=atributo, valor=valor):
                # Se espera un error de validación (DatosClienteInvalidos o ParametroFaltante).
                with self.assertRaises(ErrorValidacion):
                    setattr(cliente, atributo, valor)
                # El valor anterior no cambió.
                self.assertEqual(getattr(cliente, atributo), originales[atributo])
        # La identificación no tiene setter: no se puede modificar.
        with self.assertRaises(AttributeError):
            cliente.identificacion = "999999999"
        # Los atributos son privados: no existe "nombre" con doble guion bajo desde fuera.
        self.assertFalse(hasattr(cliente, "__nombre"))

    # 9 ----------------------------------------------------------------
    def test_09_excepciones_personalizadas(self):
        """Las excepciones propias heredan de la jerarquía del sistema y traen mensajes claros."""
        # Ambas excepciones son errores de validación y errores del sistema.
        self.assertTrue(issubclass(DatosClienteInvalidos, ErrorValidacion))
        self.assertTrue(issubclass(ParametroFaltante, ErrorValidacion))
        self.assertTrue(issubclass(ParametroFaltante, ErrorSistema))
        # Se provoca un dato faltante y se revisa el error.
        with self.assertRaises(ParametroFaltante) as faltante:
            self.crear(correo=None)
        # Tiene código propio y menciona el campo.
        self.assertEqual(faltante.exception.codigo, "VAL-003")
        self.assertIn("correo", str(faltante.exception))
        # Se provoca un dato inválido y se revisa el error.
        with self.assertRaises(DatosClienteInvalidos) as invalido:
            self.crear(telefono="abc")
        # Tiene código propio, conserva el valor rechazado y su texto empieza con el código.
        self.assertEqual(invalido.exception.codigo, "CLI-001")
        self.assertEqual(invalido.exception.valor, "abc")
        self.assertTrue(str(invalido.exception).startswith("[CLI-001]"))

    # 10 ---------------------------------------------------------------
    def test_10_manejo_correcto_de_errores(self):
        """Los errores se capturan con try/except, se registran en el log y el programa continúa."""
        # Lista de clientes registrados (como haría el sistema, sin base de datos).
        registrados = []
        # Mensajes de error capturados.
        errores = []
        # Mezcla de datos válidos e inválidos.
        lote = [
            {},                                  # Válido.
            {"nombre": ""},                      # Nombre vacío.
            {"identificacion": None},            # Identificación faltante.
            {"identificacion": "52123456"},      # Válido.
            {"correo": "malo"},                  # Correo inválido.
        ]
        # Se procesa cada registro sin que un error detenga el ciclo.
        for cambios in lote:
            try:
                # Se intenta crear el cliente.
                cliente = self.crear(**cambios)
            except ErrorValidacion as error:
                # El error se registra en el log y se guarda su mensaje.
                GestorLogs.obtener_instancia().error("Registro de cliente rechazado", error, origen="test")
                errores.append(str(error))
            else:
                # Solo si no hubo error se agrega a la lista.
                registrados.append(cliente)
        # Se procesaron los 5 registros: 2 válidos y 3 rechazados.
        self.assertEqual(len(registrados), 2)
        self.assertEqual(len(errores), 3)
        # Los errores quedaron escritos en el archivo de log.
        lineas_error = GestorLogs.obtener_instancia().leer_registros("ERROR")
        self.assertTrue(any("ParametroFaltante" in linea for linea in lineas_error))
        self.assertTrue(any("DatosClienteInvalidos" in linea for linea in lineas_error))
        # La creación exitosa también quedó registrada como INFO.
        lineas_info = GestorLogs.obtener_instancia().leer_registros("INFO")
        self.assertTrue(any("Cliente registrado" in linea for linea in lineas_info))


# Permite ejecutar las pruebas con: python test_cliente.py
if __name__ == "__main__":
    # verbosity=2 muestra el nombre y resultado de cada prueba.
    unittest.main(verbosity=2)
