"""
Módulo: verificacion_global.py
Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - UNAD - Fase 4
Responsable: Estudiante 5 - Simulación de operaciones e integración

Descripción:
    Comprueba que el código de los cinco integrantes funcione como un solo
    proyecto. Ejecuta cinco verificaciones y muestra un informe:

    1. Módulos:     todos los archivos del sistema se pueden importar.
    2. Pruebas:     se ejecutan las pruebas de Clientes, Servicios y Reservas.
    3. main.py:     la demostración de EntidadBase termina sin interrumpirse.
    4. Simulación:  al menos 10 operaciones, todas con el resultado esperado.
    5. GitHub:      qué archivos del sistema ya están en la rama origin/main.

    Las verificaciones 2 a 4 escriben su log en un archivo temporal para no
    llenar ``sistema.log`` con datos de prueba.

Ejecución:
    git fetch origin            (recomendado, para ver el estado actual de GitHub)
    python verificacion_global.py
"""

import contextlib
import importlib
import io
import os
import subprocess
import sys
import tempfile
import unittest

from gestor_logs import GestorLogs

# Archivos que forman el sistema, por integrante.
MODULOS = {
    "Estudiante 1 - Base": ["excepciones", "gestor_logs", "entidad_base", "main"],
    "Estudiante 2 - Clientes": ["cliente", "test_cliente"],
    "Estudiante 3 - Servicios": ["servicio", "reserva_sala", "alquiler_equipo", "asesoria_especializada",
                                 "pruebas_servicios"],
    "Estudiante 4 - Reservas": ["excepciones_reserva", "reserva", "pruebas_reserva"],
    "Estudiante 5 - Simulación": ["simulacion", "verificacion_global"],
}
# Módulos de pruebas unitarias del equipo.
SUITES_DE_PRUEBA = ["test_cliente", "pruebas_servicios", "pruebas_reserva"]
# Mínimo de operaciones que exige el Anexo 3.
MINIMO_OPERACIONES = 10


@contextlib.contextmanager
def log_temporal():
    """Redirige GestorLogs a un archivo temporal mientras dura el bloque with."""
    descriptor, ruta = tempfile.mkstemp(suffix=".log")
    os.close(descriptor)
    original = GestorLogs._instancia
    GestorLogs._instancia = GestorLogs(ruta)
    try:
        yield ruta
    finally:
        # Se ejecuta siempre: se restaura el gestor real y se borra el temporal.
        GestorLogs._instancia = original
        os.remove(ruta)


def verificar_modulos():
    """1. Importa cada módulo del sistema."""
    fallos = []
    for integrante, modulos in MODULOS.items():
        for nombre in modulos:
            try:
                importlib.import_module(nombre)
            except ImportError as error:
                fallos.append(f"{nombre}.py ({integrante}): {error}")
    total = sum(len(m) for m in MODULOS.values())
    return not fallos, f"{total - len(fallos)}/{total} módulos importados", fallos


def verificar_pruebas():
    """2. Ejecuta las pruebas unitarias del equipo."""
    cargador = unittest.TestLoader()
    suite = unittest.TestSuite(cargador.loadTestsFromName(nombre) for nombre in SUITES_DE_PRUEBA)
    salida = io.StringIO()

    with log_temporal():
        resultado = unittest.TextTestRunner(stream=salida, verbosity=0).run(suite)

        problemas = [str(prueba) for prueba, _ in resultado.failures + resultado.errors]
        detalle = (f"{resultado.testsRun} pruebas, {len(resultado.failures)} fallos, "
                   f"{len(resultado.errors)} errores") 
    return resultado.wasSuccessful(), detalle, problemas


def verificar_main():
    """3. Ejecuta la demostración de main.py (Estudiante 1) sin mostrar su salida."""
    import main
    with log_temporal() as ruta, contextlib.redirect_stdout(io.StringIO()) as salida:
        main.Aplicacion().iniciar()
        terminado = any("Fin de la ejecución" in linea for linea in GestorLogs(ruta).leer_registros("INFO"))
    fallo_general = "Fallo general" in salida.getvalue()
    correcto = terminado and not fallo_general
    return correcto, "terminó sin interrupciones" if correcto else "no terminó correctamente", []


def verificar_simulacion():
    """4. Ejecuta la simulación y compara cada resultado con el esperado."""
    from simulacion import SimuladorOperaciones
    with log_temporal() as ruta:
        simulador = SimuladorOperaciones(mostrar_en_consola=False)
        simulador.simular()
        errores_en_log = len(GestorLogs(ruta).leer_registros("ERROR"))
    datos = simulador.resumen()
    distintos = [f"{f['numero']:02d} {f['descripcion']}" for f in simulador.resultados if not f["coincide"]]
    correcto = datos["total"] >= MINIMO_OPERACIONES and not distintos
    detalle = (f"{datos['total']} operaciones ({datos['exitosas']} éxitos, {datos['errores_controlados']} "
               f"errores controlados), {datos['coinciden']}/{datos['total']} según lo esperado, "
               f"{errores_en_log} errores escritos en el log")
    return correcto, detalle, distintos


def verificar_github(rama="origin/main"):
    """5. Revisa qué archivos del sistema existen en la rama remota (requiere git)."""
    try:
        salida = subprocess.run(["git", "ls-tree", "--name-only", rama], capture_output=True, text=True,
                                check=True, cwd=os.path.dirname(os.path.abspath(__file__))).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        return False, f"no se pudo consultar {rama}: {error}", []
    en_rama = set(salida.split())
    faltan = [f"{nombre}.py ({integrante})" for integrante, modulos in MODULOS.items()
              for nombre in modulos if f"{nombre}.py" not in en_rama]
    total = sum(len(m) for m in MODULOS.values())
    return not faltan, f"{total - len(faltan)}/{total} archivos del sistema están en {rama}", faltan


def main():
    """Ejecuta todas las verificaciones; un fallo en una no impide las demás."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    verificaciones = [
        ("1. Módulos del sistema", verificar_modulos),
        ("2. Pruebas unitarias del equipo", verificar_pruebas),
        ("3. Programa main.py", verificar_main),
        ("4. Simulación de operaciones", verificar_simulacion),
        ("5. Integración en GitHub", verificar_github),
    ]
    print("=" * 78)
    print(" SOFTWARE FJ - Verificación global del proyecto")
    print("=" * 78)
    todas_bien = True
    for titulo, verificacion in verificaciones:
        try:
            correcto, detalle, problemas = verificacion()
        except Exception as error:
            # Última barrera: una verificación que se rompe se informa y se sigue con la siguiente.
            correcto, detalle, problemas = False, f"{type(error).__name__}: {error}", []
        todas_bien = todas_bien and correcto
        print(f"\n[{'OK' if correcto else 'X '}] {titulo}: {detalle}")
        for problema in problemas:
            print(f"      - {problema}")
    print("\n" + "=" * 78)
    print(" RESULTADO: " + ("todo integrado y funcionando." if todas_bien
                            else "hay puntos pendientes (ver la lista anterior)."))
    print("=" * 78)
    return 0 if todas_bien else 1


if __name__ == "__main__":
    sys.exit(main())
