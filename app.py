from flask import Flask, render_template, request, redirect, url_for, session
from conexion_sheets import obtener_datos
from analisis import (
    contar_solicitudes_por_estado,
    agrupar_dias_por_departamento,
    contar_solicitudes_por_departamento,
    promedio_dias_por_estado,
    contar_vacaciones_prolongadas,
    agrupar_solicitudes_por_estado
)
from graficos import (
    grafico_dias_departamento,
    grafico_solicitudes_estado,
    grafico_solicitudes_departamento,
    grafico_promedio_dias_estado,
    grafico_vacaciones_prolongadas,
    grafico_comparativo_aprobadas
)

app = Flask(__name__)
app.secret_key = "prosip_vacaciones_vallegrande_secret"

# ==========================================================
# CORREOS AUTORIZADOS PARA JEFE Y ADMINISTRADOR
# ==========================================================
CORREOS_ADMINISTRADOR = [
    "fernando.ruiz@vallegrande.edu.pe",
    "dayana.arata@vallegrande.edu.pe",
    "patrick.garcia.v@vallegrande.edu.pe"
]

CORREOS_JEFE = [
    "fernando.ruiz@vallegrande.edu.pe",
    "dayana.arata@vallegrande.edu.pe",
    "patrick.garcia.v@vallegrande.edu.pe"
]

# Clave de respaldo para gestión
CLAVE_RESPALDO_GESTION = "admin2026"


def obtener_documento_fila(fila):
    """Busca la columna de DNI o Carnet de Extranjería sin importar espacios ni mayúsculas."""
    for clave, valor in fila.items():
        clave_limpia = str(clave).strip().lower()
        if "dni" in clave_limpia or "carnet" in clave_limpia or "extranjer" in clave_limpia:
            val_str = str(valor).strip()
            if val_str.endswith(".0"):
                val_str = val_str[:-2]
            if val_str:
                return val_str
    return ""


def obtener_correo_fila(fila):
    """Busca la columna de correo sin importar espacios."""
    for clave, valor in fila.items():
        if "correo" in str(clave).strip().lower():
            return str(valor).strip().lower()
    return ""


def documentos_coinciden(doc_ingresado, doc_registrado):
    """Compara DNI o Carnet de Extranjería (considerando ceros a la izquierda)."""
    if not doc_ingresado or not doc_registrado:
        return False
    ing = doc_ingresado.strip().upper()
    reg = doc_registrado.strip().upper()
    return ing == reg or ing.lstrip("0") == reg.lstrip("0")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        doc_ingresado = request.form.get("clave", "").strip()
        rol_elegido = request.form.get("rol_elegido", "COLABORADOR").strip().upper()

        # 1. Validar que sea correo institucional @vallegrande.edu.pe
        if not correo.endswith("@vallegrande.edu.pe"):
            return render_template(
                "dashboard.html",
                usuario=None,
                rol=None,
                error="Acceso denegado: Solo se permiten correos @vallegrande.edu.pe"
            )

        # 2. Buscar todas las filas del usuario en Google Sheets
        datos = obtener_datos()
        filas_usuario = [f for f in datos if obtener_correo_fila(f) == correo]

        # Obtener todos los DNI / Carnet de Extranjería registrados para ese correo
        docs_registrados = [
            obtener_documento_fila(f) for f in filas_usuario if obtener_documento_fila(f)
        ]

        es_doc_valido = any(documentos_coinciden(doc_ingresado, d) for d in docs_registrados)

        # 3. Validar permisos y documento según el rol elegido
        if rol_elegido == "ADMINISTRADOR":
            if correo not in CORREOS_ADMINISTRADOR:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="Tu correo no tiene permisos de Administrador. Elige Colaborador."
                )
            if not es_doc_valido and doc_ingresado != CLAVE_RESPALDO_GESTION:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="DNI o Carnet de Extranjería incorrecto."
                )

        elif rol_elegido == "JEFE":
            if correo not in CORREOS_JEFE:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="Tu correo no tiene permisos de Jefe. Elige Colaborador."
                )
            if not es_doc_valido and doc_ingresado != CLAVE_RESPALDO_GESTION:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="DNI o Carnet de Extranjería incorrecto."
                )

        else:  # COLABORADOR
            if not filas_usuario:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="Este correo aún no tiene solicitudes registradas."
                )
            if not es_doc_valido:
                return render_template(
                    "dashboard.html", usuario=None, rol=None,
                    error="Contraseña incorrecta. Ingresa tu N.° de DNI o Carnet de Extranjería."
                )

        # Guardar sesión
        session["usuario"] = correo
        session["rol"] = rol_elegido

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("dashboard"))


@app.route("/")
def dashboard():
    usuario = session.get("usuario")
    rol = session.get("rol")

    if not usuario:
        return render_template("dashboard.html", usuario=None, rol=None, error=None)

    datos = obtener_datos()

    # Filtrar datos según el rol elegido
    if rol in ["ADMINISTRADOR", "JEFE"]:
        datos_filtrados = datos
    else:
        # COLABORADOR: Solo ve sus propias solicitudes
        datos_filtrados = [f for f in datos if obtener_correo_fila(f) == usuario]

    # Calcular KPIs
    total_solicitudes = len(datos_filtrados)
    total_aprobadas   = contar_solicitudes_por_estado(datos_filtrados, "ACEPTADO")
    total_pendientes  = contar_solicitudes_por_estado(datos_filtrados, "PENDIENTE")
    total_denegadas   = contar_solicitudes_por_estado(datos_filtrados, "DENEGADO")
    total_prolongadas = contar_vacaciones_prolongadas(datos_filtrados, dias_limite=10)

    # Generar gráficos
    grafico1 = grafico_dias_departamento(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)
    grafico2 = grafico_solicitudes_estado(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)
    grafico3 = grafico_solicitudes_departamento(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)
    grafico4 = grafico_promedio_dias_estado(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)
    grafico5 = grafico_vacaciones_prolongadas(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)
    grafico6 = grafico_comparativo_aprobadas(datos_filtrados).to_html(full_html=False, include_plotlyjs=False)

    return render_template(
        "dashboard.html",
        usuario=usuario,
        rol=rol,
        mis_solicitudes=datos_filtrados,
        total_solicitudes=total_solicitudes,
        total_aprobadas=total_aprobadas,
        total_pendientes=total_pendientes,
        total_denegadas=total_denegadas,
        total_prolongadas=total_prolongadas,
        grafico1=grafico1,
        grafico2=grafico2,
        grafico3=grafico3,
        grafico4=grafico4,
        grafico5=grafico5,
        grafico6=grafico6
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)