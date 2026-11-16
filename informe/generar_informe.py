"""
Generador del informe grupal (PDF) - Software FJ, Fase 4.
Responsable: Estudiante 5 - Consolidación del informe grupal.

Uso:
    1. Completar los datos de la sección DATOS DE LA PORTADA (los textos entre
       corchetes aparecen resaltados en amarillo en el PDF hasta reemplazarlos).
    2. Ejecutar desde la carpeta del proyecto:
           python informe/generar_informe.py
    3. Se genera informe/Informe_Grupal_Software_FJ.pdf

La tabla de resultados se construye ejecutando la simulación real
(simulacion.py), así el informe siempre coincide con el código.
Requiere la librería reportlab (pip install reportlab).
"""

import os
import sys
import tempfile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# ======================================================================
# DATOS DE LA PORTADA (editar aquí)
# ======================================================================
INTEGRANTES = [
    # (nombre completo, rol en el proyecto)
    ("July Viviana Matabanchoy Guacas", "Estudiante 1 - Clase abstracta EntidadBase, excepciones y logs"),
    ("[Nombre completo del integrante]", "Estudiante 2 - Módulo de gestión de clientes"),
    ("[Nombre completo del integrante]", "Estudiante 3 - Jerarquía y polimorfismo de servicios"),
    ("[Nombre completo del integrante]", "Estudiante 4 - Módulo de reservas y métodos sobrecargados"),
    ("[Nombre completo del integrante]", "Estudiante 5 - Simulación de operaciones e informe grupal"),
]
GRUPO = "[Número de grupo]"
TUTOR = "[Nombre del tutor o tutora]"
FECHA = "Noviembre de 2026"
REPOSITORIO = "https://github.com/Julyvmg/Software_FJ"

# ======================================================================
# Configuración
# ======================================================================
CARPETA_INFORME = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_INFORME)
ARCHIVO_PDF = os.path.join(CARPETA_INFORME, "Informe_Grupal_Software_FJ.pdf")
sys.path.insert(0, CARPETA_PROYECTO)

AZUL = colors.HexColor("#1F3864")
GRIS_TABLA = colors.HexColor("#D9E2F3")
LINEA = 24        # Interlineado doble (APA 7) para el texto del cuerpo.

ESTILOS = {
    "titulo_portada": ParagraphStyle("tp", fontName="Times-Bold", fontSize=14, leading=20, alignment=TA_CENTER,
                                     textColor=AZUL),
    "portada": ParagraphStyle("p", fontName="Times-Roman", fontSize=12, leading=20, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName="Times-Bold", fontSize=12, leading=LINEA, alignment=TA_CENTER,
                         spaceBefore=6, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=12, leading=LINEA, alignment=TA_LEFT,
                         spaceBefore=4),
    "cuerpo": ParagraphStyle("c", fontName="Times-Roman", fontSize=12, leading=LINEA, firstLineIndent=1.27 * cm,
                             alignment=TA_LEFT),
    "sin_sangria": ParagraphStyle("s", fontName="Times-Roman", fontSize=12, leading=LINEA),
    "referencia": ParagraphStyle("r", fontName="Times-Roman", fontSize=12, leading=LINEA, leftIndent=1.27 * cm,
                                 firstLineIndent=-1.27 * cm),
    "tabla_titulo": ParagraphStyle("tt", fontName="Times-Bold", fontSize=12, leading=16, spaceBefore=8),
    "tabla_nombre": ParagraphStyle("tn", fontName="Times-Italic", fontSize=12, leading=16, spaceAfter=4),
    "celda": ParagraphStyle("ce", fontName="Times-Roman", fontSize=9.5, leading=11.5),
    "celda_titulo": ParagraphStyle("ct", fontName="Times-Bold", fontSize=9.5, leading=11.5),
    "nota": ParagraphStyle("n", fontName="Times-Italic", fontSize=10, leading=13, spaceBefore=4, spaceAfter=10),
    "codigo": ParagraphStyle("co", fontName="Courier", fontSize=10, leading=14, leftIndent=1.27 * cm),
}


def texto(valor):
    """Escapa el texto y resalta en amarillo los datos pendientes (entre corchetes)."""
    limpio = escape(valor)
    if valor.startswith("["):
        return f'<font backColor="#FFF2A8">{limpio}</font>'
    return limpio


def parrafo(contenido, estilo="cuerpo"):
    return Paragraph(contenido, ESTILOS[estilo])


def tabla(numero, nombre, filas, anchos, nota=None):
    """Tabla con formato APA: número en negrita y título en cursiva arriba."""
    datos = [[Paragraph(c, ESTILOS["celda_titulo"]) for c in filas[0]]]
    datos += [[Paragraph(str(c), ESTILOS["celda"]) for c in fila] for fila in filas[1:]]
    cuadro = Table(datos, colWidths=anchos, repeatRows=1)
    cuadro.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_TABLA),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FB")]),
    ]))
    elementos = [KeepTogether([parrafo(f"Tabla {numero}", "tabla_titulo"), parrafo(nombre, "tabla_nombre")]),
                 cuadro]
    if nota:
        elementos.append(parrafo(f"<i>Nota.</i> {nota}", "nota"))
    return elementos


def ejecutar_simulacion():
    """Ejecuta la simulación en silencio (log temporal) y devuelve resultados y resumen."""
    from gestor_logs import GestorLogs
    from simulacion import SimuladorOperaciones
    descriptor, ruta = tempfile.mkstemp(suffix=".log")
    os.close(descriptor)
    original = GestorLogs._instancia
    GestorLogs._instancia = GestorLogs(ruta)
    try:
        simulador = SimuladorOperaciones(mostrar_en_consola=False)
        simulador.simular()
        return simulador.resultados, simulador.resumen()
    finally:
        GestorLogs._instancia = original
        os.remove(ruta)


def numerar_pagina(canvas, documento):
    """Número de página arriba a la derecha (APA 7)."""
    canvas.saveState()
    canvas.setFont("Times-Roman", 12)
    canvas.drawRightString(letter[0] - 2.54 * cm, letter[1] - 1.5 * cm, str(documento.page))
    canvas.restoreState()


# ======================================================================
# Contenido
# ======================================================================
def portada():
    e = [Spacer(1, 2.2 * cm),
         parrafo("Sistema Integral de Gestión de Clientes, Servicios y Reservas: Software FJ", "titulo_portada"),
         Spacer(1, 0.3 * cm),
         parrafo("Fase 4 - Componente práctico: Prácticas simuladas", "portada"),
         Spacer(1, 1.6 * cm),
         parrafo("<b>Integrantes</b>", "portada")]
    e += [parrafo(texto(nombre), "portada") for nombre, _ in INTEGRANTES]
    e += [Spacer(1, 1.0 * cm),
          parrafo(f"<b>Grupo:</b> {texto(GRUPO)}", "portada"),
          parrafo(f"<b>Tutor(a):</b> {texto(TUTOR)}", "portada"),
          Spacer(1, 2.2 * cm),
          parrafo("Universidad Nacional Abierta y a Distancia - UNAD", "portada"),
          parrafo("Escuela de Ciencias Básicas, Tecnología e Ingeniería - ECBTI", "portada"),
          parrafo("Programa de Ingeniería de Sistemas", "portada"),
          parrafo("Curso: Programación (213023)", "portada"),
          Spacer(1, 0.6 * cm),
          parrafo(texto(FECHA), "portada"),
          PageBreak()]
    return e


def introduccion():
    return [
        parrafo("Introducción", "h1"),
        parrafo("El presente informe consolida el trabajo colaborativo realizado en la Fase 4 del curso "
                "Programación (213023), cuyo propósito es implementar el manejo de excepciones en una aplicación "
                "orientada a objetos que sea estable y robusta. El problema planteado en el Anexo 3 consiste en "
                "construir, sin bases de datos, un sistema para la empresa Software FJ que gestione clientes, "
                "servicios (reserva de salas, alquiler de equipos y asesorías especializadas) y reservas, y que "
                "siga funcionando aun cuando se presenten errores durante su ejecución."),
        parrafo("La solución se desarrolló en Python aplicando los cuatro principios de la programación "
                "orientada a objetos: abstracción, mediante las clases abstractas <i>EntidadBase</i> y "
                "<i>Servicio</i>; herencia, con tres servicios especializados que extienden a <i>Servicio</i>; "
                "polimorfismo, porque cada servicio sobrescribe sus métodos para calcular costos, describirse y "
                "validar sus parámetros; y encapsulación, con atributos privados que solo se modifican a través "
                "de propiedades con validación (Romano et al., 2019). La información se maneja con objetos, "
                "listas y diccionarios en memoria, y el único archivo que se escribe es <i>sistema.log</i>, "
                "donde quedan registrados los eventos y los errores."),
        parrafo("El manejo de errores sigue las recomendaciones de la documentación oficial del lenguaje "
                "(Van Rossum &amp; Drake, 2024; Cuevas Álvarez, 2016): se definieron excepciones personalizadas "
                "organizadas en una jerarquía, se usaron los bloques <i>try/except</i>, <i>try/except/else</i> y "
                "<i>try/except/finally</i> según el propósito de cada operación, y se aplicó el encadenamiento "
                "de excepciones para conservar la causa original de cada fallo. El trabajo se dividió en cinco "
                "módulos, uno por integrante, que se integraron en un único repositorio de GitHub. Este documento "
                "presenta el enlace del repositorio, una síntesis de la solución, los resultados de la "
                "simulación de operaciones exigida y las conclusiones del equipo."),
    ]


def repositorio():
    filas = [["Integrante", "Archivos", "Responsabilidad"],
             [texto(INTEGRANTES[0][0]) + "<br/>(Estudiante 1)", "entidad_base.py, excepciones.py, gestor_logs.py, "
              "main.py", "Clase abstracta común (ID, estados, fechas), jerarquía de excepciones y registro de "
              "eventos en sistema.log."],
             [texto(INTEGRANTES[1][0]) + "<br/>(Estudiante 2)", "cliente.py, test_cliente.py",
              "Clase Cliente con datos personales encapsulados y validados con expresiones regulares."],
             [texto(INTEGRANTES[2][0]) + "<br/>(Estudiante 3)", "servicio.py, reserva_sala.py, alquiler_equipo.py, "
              "asesoria_especializada.py, pruebas_servicios.py", "Clase abstracta Servicio, tres servicios "
              "especializados y procesamiento polimórfico."],
             [texto(INTEGRANTES[3][0]) + "<br/>(Estudiante 4)", "reserva.py, excepciones_reserva.py, "
              "pruebas_reserva.py", "Clase Reserva (confirmación y cancelación), gestor de reservas y cálculo de "
              "costos con parámetros opcionales."],
             [texto(INTEGRANTES[4][0]) + "<br/>(Estudiante 5)", "simulacion.py, verificacion_global.py, "
              "informe/", "Simulación de operaciones, verificación de la integración e informe grupal."]]
    return [
        parrafo("Enlace del Repositorio en GitHub", "h1"),
        parrafo("El código fuente completo y documentado se encuentra en el siguiente "
                "repositorio público, desarrollado siguiendo las orientaciones del curso para el trabajo "
                "colaborativo con GitHub (Zambrano, 2025; Silva, 2025):"),
        Spacer(1, 4),
        parrafo(f'<link href="{REPOSITORIO}" color="blue"><u>{REPOSITORIO}</u></link>', "h2"),
        Spacer(1, 4),
        parrafo("Para ejecutar el sistema solo se necesita Python 3; no se usan librerías externas ni bases de "
                "datos. Desde la carpeta del proyecto se pueden usar los siguientes comandos:", "cuerpo"),
        parrafo("python simulacion.py", "codigo"),
        parrafo("python verificacion_global.py", "codigo"),
        parrafo("python -m unittest test_cliente pruebas_servicios pruebas_reserva -v", "codigo"),
        Spacer(1, 6),
        *tabla(1, "Organización del repositorio y distribución del trabajo", filas,
               [4.0 * cm, 5.4 * cm, 7.1 * cm]),
    ]


def solucion():
    filas = [["Mecanismo", "Dónde se aplica", "Propósito"],
             ["Excepciones personalizadas", "excepciones.py, excepciones_reserva.py",
              "Todas heredan de ErrorSistema y tienen un código (CLI-001, SER-002, RES-004...). Un solo "
              "except ErrorSistema captura los errores previstos sin ocultar los errores de programación."],
             ["try/except", "Validaciones de Cliente, Servicio y Reserva",
              "Capturar errores concretos (por ejemplo ValueError al convertir un número) y traducirlos a un "
              "error del sistema con un mensaje claro."],
             ["try/except/else", "Reserva.confirmar(), procesar_servicios(), simulación",
              "El bloque else solo guarda el costo final o cuenta la operación cuando no hubo errores."],
             ["try/except/finally", "Reserva.cancelar(), main.py, simulación",
              "El bloque finally deja rastro en el log o actualiza contadores siempre, con éxito o con error."],
             ["raise ... from error", "Confirmación, cancelación y validaciones",
              "Lanzar un error de más alto nivel conservando la causa original en __cause__ (Yee, 2005)."]]
    return [
        parrafo("Síntesis de la Solución", "h1"),
        parrafo("La clase abstracta <i>EntidadBase</i>, construida con el módulo <i>abc</i> (Python Software "
                "Foundation, s. f.-a), concentra lo que comparten todas las entidades: un identificador de solo "
                "lectura, un estado controlado, las fechas de creación y modificación, y la obligación de "
                "implementar <i>validar()</i> y <i>describir()</i>. De ella heredan <i>Cliente</i>, la clase "
                "abstracta <i>Servicio</i> y <i>Reserva</i>. <i>Servicio</i> tiene tres subclases "
                "(<i>ReservaSala</i>, <i>AlquilerEquipo</i> y <i>AsesoriaEspecializada</i>), y cada una calcula "
                "su costo con su propia fórmula. <i>Reserva</i> se asocia con un cliente y un servicio, controla "
                "las transiciones PENDIENTE, CONFIRMADA y CANCELADA, y simula la sobrecarga de métodos con "
                "parámetros opcionales: <i>calcular_costo()</i> calcula el costo básico, con impuesto, con "
                "descuento o con ambos sin duplicar la fórmula. El registro de eventos usa una única instancia "
                "compartida de <i>GestorLogs</i>, siguiendo la idea del patrón Singleton (Gamma et al., 1994)."),
        *tabla(2, "Mecanismos de manejo de excepciones utilizados", filas, [3.6 * cm, 4.6 * cm, 8.3 * cm]),
    ]


def resultados_simulacion(resultados, resumen):
    filas = [["N.°", "Operación", "Esperado", "Obtenido", "Excepción capturada"]]
    for f in resultados:
        filas.append([f"{f['numero']:02d}", escape(f["descripcion"]), f["esperado"].capitalize().replace("Exito", "Éxito"),
                      f["obtenido"].capitalize().replace("Exito", "Éxito"), f["tipo_error"] or "-"])
    return [
        parrafo("Resultados de la Simulación de Operaciones", "h1"),
        parrafo(f"El Anexo 3 exige simular al menos diez operaciones completas. El programa "
                f"<i>simulacion.py</i> ejecuta {resumen['total']}, que incluyen registros válidos e inválidos de "
                f"clientes, creación correcta e incorrecta de servicios, reservas exitosas y fallidas, y un "
                f"error inesperado del lenguaje. Cada operación declara de antemano si debe terminar en éxito o "
                f"en error, y el programa compara ese resultado con el obtenido. En la ejecución se obtuvieron "
                f"{resumen['exitosas']} operaciones exitosas y {resumen['errores_controlados']} errores "
                f"controlados. En total, {resumen['coinciden']} de las {resumen['total']} operaciones se "
                f"comportaron según lo esperado y la aplicación terminó sin interrupciones."),
        parrafo("Además, la integración se comprobó con <i>verificacion_global.py</i>, que importa todos los "
                "módulos, ejecuta las pruebas unitarias de los tres módulos (escritas con <i>unittest</i>; "
                "Python Software Foundation, s. f.-b), corre el programa principal y la simulación, y revisa "
                "qué archivos están publicados en la rama principal del repositorio."),
        *tabla(3, "Operaciones simuladas y resultado obtenido", filas,
               [0.9 * cm, 7.0 * cm, 1.9 * cm, 1.9 * cm, 4.8 * cm],
               nota="Los errores de la columna Excepción capturada fueron controlados y registrados en "
                    "sistema.log. El IndexError de la operación final es un error no previsto del lenguaje: se "
                    "captura en la última barrera del simulador para demostrar que el programa no se detiene."),
    ]


def conclusiones():
    return [
        parrafo("Conclusiones", "h1"),
        parrafo("El manejo estructurado de excepciones permitió cumplir el objetivo central de la actividad: "
                "el sistema detecta datos inválidos, parámetros faltantes, operaciones no permitidas, servicios "
                "no disponibles y reservas incorrectas, informa cada caso con un mensaje claro y continúa "
                "funcionando. La simulación lo demostró al ejecutar todas sus operaciones sin interrupciones, "
                "incluido un error no previsto del lenguaje."),
        parrafo("Organizar las excepciones personalizadas en una jerarquía con una clase raíz común "
                "facilitó capturar los errores del sistema de forma específica, sin recurrir a capturas "
                "indiscriminadas que oculten fallos de programación. El encadenamiento con <i>raise ... from</i> "
                "resultó útil para el diagnóstico, porque cada error de alto nivel, como la falla al confirmar "
                "una reserva, conserva la causa que lo originó y ambas quedan escritas en el archivo de logs."),
        parrafo("Cada variante de los bloques <i>try</i> cumple un papel distinto: <i>except</i> traduce y "
                "controla el error, <i>else</i> garantiza que una acción, como fijar el costo final de una "
                "reserva, solo ocurra cuando la operación fue exitosa, y <i>finally</i> asegura las tareas de "
                "seguimiento con cualquier resultado. Elegir el bloque adecuado hace el código más claro y "
                "predecible."),
        parrafo("La abstracción, la herencia, el polimorfismo y la encapsulación produjeron un diseño modular "
                "y extensible: agregar un nuevo tipo de servicio solo requiere crear una subclase de "
                "<i>Servicio</i>, sin modificar las clases de clientes ni de reservas. Del mismo modo, Python "
                "no admite la sobrecarga tradicional de métodos, pero los parámetros opcionales permitieron "
                "ofrecer varias formas de calcular costos con una sola implementación."),
        parrafo("Finalmente, el trabajo colaborativo con GitHub, la división del proyecto en un módulo por "
                "integrante, las convenciones comunes de estilo (van Rossum et al., 2001) y las pruebas "
                "automatizadas permitieron integrar el código de los cinco estudiantes en un único proyecto "
                "funcional, verificable por cualquier persona que descargue el repositorio."),
    ]


def referencias():
    lista = [
        "Cuevas Álvarez, A. (2016). <i>Python 3: Curso práctico</i>. RA-MA Editorial. "
        "https://elibro-net.bibliotecavirtual.unad.edu.co/es/ereader/unad/106404?page=373",
        "Gamma, E., Helm, R., Johnson, R., &amp; Vlissides, J. (1994). <i>Design patterns: Elements of reusable "
        "object-oriented software</i>. Addison-Wesley.",
        "Python Software Foundation. (s. f.-a). <i>abc - Abstract base classes</i>. Recuperado el 10 de noviembre "
        "de 2026, de https://docs.python.org/3/library/abc.html",
        "Python Software Foundation. (s. f.-b). <i>unittest - Unit testing framework</i>. Recuperado el 10 de "
        "noviembre de 2026, de https://docs.python.org/3/library/unittest.html",
        "Romano, F., Baka, B., &amp; Phillips, D. (2019). <i>Getting started with Python: Understand key data "
        "structures and use Python in object-oriented programming</i>. Packt Publishing. "
        "https://research-ebsco-com.bibliotecavirtual.unad.edu.co/linkprocessor/plink?id=b41fd66a-1134-3dcd-"
        "8dba-90f36451f08d",
        "Silva, F. D. (2025). <i>Basics of using GitHub</i> [Objeto virtual de información]. Repositorio "
        "Institucional UNAD. https://repository.unad.edu.co/handle/10596/75882",
        "Van Rossum, G., &amp; Drake, F. L., Jr. (2024). <i>El tutorial de Python</i>. Python Software "
        "Foundation. https://docs.python.org/es/3.12/tutorial/errors.html",
        "Van Rossum, G., Warsaw, B., &amp; Coghlan, A. (2001). <i>PEP 8 - Style guide for Python code</i>. "
        "Python Software Foundation. https://peps.python.org/pep-0008/",
        "Yee, K.-P. (2005). <i>PEP 3134 - Exception chaining and embedded tracebacks</i>. Python Software "
        "Foundation. https://peps.python.org/pep-3134/",
        "Zambrano, J. P. (2025). <i>Introducción al uso de GitHub</i> [Objeto virtual de información]. "
        "Repositorio Institucional UNAD. https://repository.unad.edu.co/handle/10596/75876",
    ]
    return [PageBreak(), parrafo("Referencias", "h1")] + [parrafo(r, "referencia") for r in lista]


def generar():
    resultados, resumen = ejecutar_simulacion()
    documento = SimpleDocTemplate(ARCHIVO_PDF, pagesize=letter, leftMargin=2.54 * cm, rightMargin=2.54 * cm,
                                  topMargin=2.54 * cm, bottomMargin=2.54 * cm,
                                  title="Informe grupal - Software FJ (Fase 4)",
                                  author="Grupo " + GRUPO, subject="Programación 213023 - UNAD")
    contenido = (portada() + introduccion() + [PageBreak()] + repositorio() + [PageBreak()] + solucion()
                 + [PageBreak()] + resultados_simulacion(resultados, resumen) + [PageBreak()]
                 + conclusiones() + referencias())
    documento.build(contenido, onFirstPage=numerar_pagina, onLaterPages=numerar_pagina)
    pendientes = sum(1 for n, _ in INTEGRANTES if n.startswith("[")) + GRUPO.startswith("[") + TUTOR.startswith("[")
    print(f"Informe generado: {ARCHIVO_PDF}")
    print(f"Simulación: {resumen['total']} operaciones, {resumen['coinciden']} según lo esperado.")
    if pendientes:
        print(f"Atención: quedan {pendientes} datos de portada pendientes (resaltados en amarillo).")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    generar()
