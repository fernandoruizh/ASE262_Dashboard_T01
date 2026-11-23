import plotly.graph_objects as go


from analisis import (
    agrupar_dias_por_departamento,
    contar_solicitudes_por_estado,
    contar_solicitudes_por_departamento,
    promedio_dias_por_estado,
    agrupar_solicitudes_por_estado,
    contar_vacaciones_prolongadas
)


from conexion_sheets import obtener_datos


colores = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#6366F1"]


def aplicar_estilo_glass(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)")
    )
    return fig


def grafico_dias_departamento(datos):
    resumen = agrupar_dias_por_departamento(datos)
    areas = ["Carrera de Análisis de Sistemas E." if a == "Carrera de Análisis de Sistemas Empresariales" else a for a in resumen.keys()]
    dias = list(resumen.values())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=areas,
        y=dias,
        marker_color=[colores[i % len(colores)] for i in range(len(areas))],
        text=dias,
        textposition="auto",
        hovertemplate="Área: %{x}<br>Días solicitados: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="1. Días de vacaciones solicitados por área",
        xaxis_title="Área / Departamento",
        yaxis_title="Total Días",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=50, r=30, t=70, b=50),
        showlegend=False
    )
    return aplicar_estilo_glass(fig)


def grafico_solicitudes_estado(datos):
    resumen = agrupar_solicitudes_por_estado(datos)
    estados = list(resumen.keys())
    cantidades = list(resumen.values())

    # Asignar color fijo según cada estado
    mapa_colores = {
        "ACEPTADO": "#10B981",   # Verde
        "PENDIENTE": "#F59E0B",  # Amarillo
        "DENEGADO": "#EF4444"    # Rojo
    }
    colores_dona = [mapa_colores.get(est, "#3B82F6") for est in estados]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=estados,
        values=cantidades,
        hole=0.60,
        marker=dict(colors=colores_dona),
        textinfo="label+percent",
        hovertemplate="Estado: %{label}<br>Solicitudes: %{value}<br>Porcentaje: %{percent}<extra></extra>"
    ))

    fig.update_layout(
        title="2. Distribución de solicitudes por estado",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=30, r=30, t=70, b=30),
        showlegend=False
    )
    return aplicar_estilo_glass(fig)


def grafico_solicitudes_departamento(datos):
    resumen = contar_solicitudes_por_departamento(datos)
    areas = ["Carrera de Análisis de Sistemas E." if a == "Carrera de Análisis de Sistemas Empresariales" else a for a in resumen.keys()]
    cantidades = list(resumen.values())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cantidades,
        y=areas,
        orientation="h",
        marker_color="#10B981",
        text=cantidades,
        textposition="auto",
        hovertemplate="Área: %{y}<br>Total Solicitudes: %{x}<extra></extra>"
    ))

    fig.update_layout(
        title="3. Total de solicitudes enviadas por departamento",
        xaxis_title="N° de Solicitudes",
        yaxis_title="Área / Departamento",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=80, r=30, t=70, b=50),
        showlegend=False
    )
    return aplicar_estilo_glass(fig)


def grafico_promedio_dias_estado(datos):
    estados = ["ACEPTADO", "PENDIENTE", "DENEGADO"]
    promedios = [promedio_dias_por_estado(datos, est) for est in estados]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=estados,
        y=promedios,
        marker_color=["#10B981", "#F59E0B", "#EF4444"],
        text=[f"{p:.1f} días" for p in promedios],
        textposition="auto",
        hovertemplate="Estado: %{x}<br>Promedio: %{y:.1f} días<extra></extra>"
    ))

    fig.update_layout(
        title="4. Promedio de días pedidos según el estado",
        xaxis_title="Estado",
        yaxis_title="Promedio de Días",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=50, r=30, t=70, b=50),
        showlegend=False
    )
    return aplicar_estilo_glass(fig)


def grafico_vacaciones_prolongadas(datos):
    cantidad = contar_vacaciones_prolongadas(datos, dias_limite=10)

    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number",
        value=cantidad,
        title={"text": "Solicitudes Prolongadas (≥ 10 Días)"},
        number={"font": {"size": 70, "color": "#F59E0B"}}
    ))

    fig.update_layout(
        title="5. Alerta de vacaciones prolongadas",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=30, r=30, t=70, b=30)
    )
    return aplicar_estilo_glass(fig)


def grafico_comparativo_aprobadas(datos):
    aceptadas  = contar_solicitudes_por_estado(datos, "ACEPTADO")
    pendientes = contar_solicitudes_por_estado(datos, "PENDIENTE")
    denegadas  = contar_solicitudes_por_estado(datos, "DENEGADO")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["ACEPTADO", "PENDIENTE", "DENEGADO"],
        y=[aceptadas, pendientes, denegadas],
        marker_color=["#10B981", "#F59E0B", "#EF4444"],
        text=[aceptadas, pendientes, denegadas],
        textposition="auto",
        hovertemplate="Estado: %{x}<br>Cantidad: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="6. Conteo de solicitudes por estado específico",
        xaxis_title="Estado",
        yaxis_title="Cantidad de Solicitudes",
        template="plotly_dark",
        autosize=True,
        height=400,
        margin=dict(l=50, r=30, t=70, b=50),
        showlegend=False
    )
    return aplicar_estilo_glass(fig)