import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Gestión QD", layout="wide", page_icon="📊")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4F8BF9;}
    .big-font {font-size:20px !important;}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (BASE DE DATOS EN MEMORIA) ---
# En una app real, esto se conecta a SQL/Excel. Aquí usamos session_state para demostración.

if 'finanzas' not in st.session_state:
    # Datos iniciales simulados según Doc 1 (Eje 2)
    data_fin = [
        {'Fecha': '2023-10-01', 'Concepto': 'Factura Cliente A', 'Tipo': 'Ingreso', 'Categoria': 'Ventas', 'Monto': 5000000, 'Proyecto': 'Consultoría X'},
        {'Fecha': '2023-10-05', 'Concepto': 'Pago Consultor Senior', 'Tipo': 'Egreso', 'Categoria': 'Costo Directo', 'Monto': 2000000, 'Proyecto': 'Consultoría X'},
        {'Fecha': '2023-10-10', 'Concepto': 'Licencias Software', 'Tipo': 'Egreso', 'Categoria': 'Gasto Admin', 'Monto': 150000, 'Proyecto': 'General'},
        {'Fecha': '2023-10-15', 'Concepto': 'Arriendo Oficina', 'Tipo': 'Egreso', 'Categoria': 'Gasto Admin', 'Monto': 800000, 'Proyecto': 'General'},
        {'Fecha': '2023-10-20', 'Concepto': 'Factura Cliente B', 'Tipo': 'Ingreso', 'Categoria': 'Ventas', 'Monto': 3500000, 'Proyecto': 'Implementación Y'},
    ]
    st.session_state['finanzas'] = pd.DataFrame(data_fin)

if 'pipeline' not in st.session_state:
    # Datos simulados según Doc 1 (Eje 3)
    data_com = [
        {'Cliente': 'Empresa Alpha', 'Servicio': 'Estrategia', 'Etapa': 'Propuesta', 'Valor': 4500000, 'Probabilidad': 50},
        {'Cliente': 'Empresa Beta', 'Servicio': 'Auditoría', 'Etapa': 'Negociación', 'Valor': 2000000, 'Probabilidad': 80},
        {'Cliente': 'Empresa Gamma', 'Servicio': 'Outsourcing', 'Etapa': 'Lead', 'Valor': 8000000, 'Probabilidad': 20},
    ]
    st.session_state['pipeline'] = pd.DataFrame(data_com)

if 'tareas' not in st.session_state:
    # Datos simulados según Doc 1 (Eje 1 - Gobernanza)
    data_gov = [
        {'Tarea': 'Cierre Mensual Octubre', 'Responsable': 'CFO', 'Estado': 'Pendiente', 'Prioridad': 'Alta'},
        {'Tarea': 'Revisión Pricing Q4', 'Responsable': 'Comercial', 'Estado': 'En Progreso', 'Prioridad': 'Media'},
    ]
    st.session_state['tareas'] = pd.DataFrame(data_gov)

# --- FUNCIONES AUXILIARES ---
def calcular_kpis_financieros(df):
    ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    costos_directos = df[df['Categoria'] == 'Costo Directo']['Monto'].sum()
    gastos_admin = df[df['Categoria'] == 'Gasto Admin']['Monto'].sum()
    
    margen_bruto = ingresos - costos_directos
    ebitda = margen_bruto - gastos_admin
    margen_pct = (margen_bruto / ingresos * 100) if ingresos > 0 else 0
    
    return ingresos, margen_bruto, ebitda, margen_pct

# --- BARRA LATERAL DE NAVEGACIÓN ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2830/2830303.png", width=100)
st.sidebar.title("Plataforma QD")
opcion = st.sidebar.radio("Módulos", ["Dashboard & Gobernanza", "Gestión Financiera", "Gestión Comercial", "Proyectos & Unit Economics"])

# ==========================================
# MÓDULO 1: GOBERNANZA & DASHBOARD INTEGRAL
# ==========================================
if opcion == "Dashboard & Gobernanza":
    st.title("🏛️ Governance Board")
    st.markdown("Vista consolidada para la toma de decisiones (Según Doc 1 - Eje 1)")

    # 1. KPIs Principales (Header)
    df_fin = st.session_state['finanzas']
    ingresos, margen, ebitda, margen_pct = calcular_kpis_financieros(df_fin)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ingresos Totales", f"${ingresos:,.0f}")
    col2.metric("Margen Bruto", f"${margen:,.0f}", f"{margen_pct:.1f}%")
    col3.metric("EBITDA Estimado", f"${ebitda:,.0f}")
    col4.metric("Pipeline Ponderado", f"${(st.session_state['pipeline']['Valor'] * st.session_state['pipeline']['Probabilidad']/100).sum():,.0f}")

    st.divider()

    # 2. Gestión de Tareas (Rituales)
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.subheader("📋 Acuerdos y Tareas Pendientes")
        edited_df = st.data_editor(st.session_state['tareas'], num_rows="dynamic", use_container_width=True)
        st.session_state['tareas'] = edited_df # Guardar cambios
    
    with col_t2:
        st.subheader("📅 Próximos Rituales")
        st.info("**Reunión Semanal de Performance**\n\n🕒 Lunes 09:00 AM\n\n📌 Revisar Pipeline y Caja Semanal")
        st.warning("**Cierre Mensual Financiero**\n\n🕒 Día 5 del mes\n\n📌 Revisar ERR y Balance")

# ==========================================
# MÓDULO 2: GESTIÓN FINANCIERA
# ==========================================
elif opcion == "Gestión Financiera":
    st.title("💰 Gestión Financiera Integral")
    st.markdown("Contabilidad de Gestión: Separación de Costos Directos vs Gastos Admin (Doc 1 - Eje 2)")

    # Formulario de Ingreso Rápido
    with st.expander("➕ Registrar Nueva Transacción (Factura/Gasto)", expanded=False):
        with st.form("form_finanzas"):
            c1, c2, c3, c4 = st.columns(4)
            fecha = c1.date_input("Fecha", datetime.now())
            concepto = c2.text_input("Concepto / Proveedor")
            tipo = c3.selectbox("Tipo", ["Ingreso", "Egreso"])
            cat = c4.selectbox("Categoría (Plan de Cuentas)", ["Ventas", "Costo Directo", "Gasto Admin", "Impuestos"])
            
            c5, c6 = st.columns(2)
            monto = c5.number_input("Monto", min_value=0)
            proyecto = c6.text_input("Proyecto Asociado (Opcional)", "General")
            
            submitted = st.form_submit_button("Guardar Transacción")
            if submitted:
                nuevo_reg = {'Fecha': str(fecha), 'Concepto': concepto, 'Tipo': tipo, 'Categoria': cat, 'Monto': monto, 'Proyecto': proyecto}
                st.session_state['finanzas'] = pd.concat([st.session_state['finanzas'], pd.DataFrame([nuevo_reg])], ignore_index=True)
                st.success("Registro guardado exitosamente.")

    # Visualización de Estado de Resultados (ERR)
    df = st.session_state['finanzas']
    
    st.subheader("Estado de Resultados (P&L)")
    
    # Tabla Pivote para ERR
    pivot = df.groupby(['Tipo', 'Categoria'])['Monto'].sum().reset_index()
    
    c_chart, c_data = st.columns([2,1])
    
    with c_chart:
        # Gráfico de Cascada (Waterfall) simplificado
        fig = px.bar(pivot, x='Categoria', y='Monto', color='Tipo', title="Ingresos vs Egresos por Categoría", 
                     color_discrete_map={'Ingreso': '#00CC96', 'Egreso': '#EF553B'})
        st.plotly_chart(fig, use_container_width=True)
    
    with c_data:
        st.dataframe(df.sort_values(by='Fecha', ascending=False), use_container_width=True)

# ==========================================
# MÓDULO 3: GESTIÓN COMERCIAL (CRM)
# ==========================================
elif opcion == "Gestión Comercial":
    st.title("🚀 Estrategia Comercial & Pipeline")
    st.markdown("Control de oportunidades y proyecciones (Doc 1 - Eje 3)")

    tab1, tab2 = st.tabs(["Pipeline", "Calculadora de Pricing"])

    with tab1:
        # Pipeline Visual
        df_pipe = st.session_state['pipeline']
        
        # Funnel Chart
        funnel_data = df_pipe.groupby('Etapa')['Valor'].sum().reset_index()
        # Ordenar el funnel lógicamente
        orden_etapas = ["Lead", "Propuesta", "Negociación", "Ganado", "Perdido"]
        funnel_data['Etapa'] = pd.Categorical(funnel_data['Etapa'], categories=orden_etapas, ordered=True)
        funnel_data = funnel_data.sort_values('Etapa')

        col_g, col_t = st.columns([3, 2])
        
        with col_g:
            fig_funnel = px.funnel(funnel_data, x='Valor', y='Etapa', title="Embudo de Ventas")
            st.plotly_chart(fig_funnel, use_container_width=True)

        with col_t:
            st.subheader("Oportunidades Activas")
            edited_pipe = st.data_editor(df_pipe, num_rows="dynamic")
            st.session_state['pipeline'] = edited_pipe

            total_pipe = df_pipe['Valor'].sum()
            forecast = (df_pipe['Valor'] * df_pipe['Probabilidad']/100).sum()
            st.metric("Valor Total en Pipeline", f"${total_pipe:,.0f}")
            st.metric("Forecast Ponderado", f"${forecast:,.0f}", help="Suma de Valor * Probabilidad")

    with tab2:
        st.subheader("Calculadora de Propuestas (Unit Economics)")
        st.markdown("Asegura el margen mínimo antes de enviar la propuesta.")
        
        c1, c2 = st.columns(2)
        tarifas = c1.number_input("Ingresos Estimados (Precio Venta)", value=1000000)
        horas = c2.number_input("Horas Estimadas", value=20)
        costo_hora = c2.number_input("Costo por Hora Promedio", value=25000)
        gastos_ext = c1.number_input("Gastos Directos (Viáticos, Software)", value=50000)
        
        costo_total = (horas * costo_hora) + gastos_ext
        margen_prop = tarifas - costo_total
        margen_pct_prop = (margen_prop / tarifas * 100) if tarifas > 0 else 0
        
        st.divider()
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric("Costo Total Proyecto", f"${costo_total:,.0f}")
        cm2.metric("Margen Proyectado", f"${margen_prop:,.0f}")
        
        color_kpi = "normal"
        if margen_pct_prop < 30: color_kpi = "inverse" # Alerta si baja rentabilidad
        cm3.metric("Margen %", f"{margen_pct_prop:.1f}%", delta_color=color_kpi)
        
        if margen_pct_prop < 30:
            st.error("⚠️ El margen está por debajo del 30%. Revisa costos o tarifa.")
        else:
            st.success("✅ Propuesta saludable financiera.")

# ==========================================
# MÓDULO 4: PROYECTOS
# ==========================================
elif opcion == "Proyectos & Unit Economics":
    st.title("🏗️ Control de Proyectos")
    st.markdown("Rentabilidad real vs presupuestada por proyecto (Doc 2 - 2.3)")
    
    df_fin = st.session_state['finanzas']
    
    # Agrupar finanzas por Proyecto
    proyectos = df_fin[df_fin['Proyecto'] != 'General'].groupby('Proyecto').apply(
        lambda x: pd.Series({
            'Ingresos': x[x['Tipo'] == 'Ingreso']['Monto'].sum(),
            'Costos Directos': x[x['Categoria'] == 'Costo Directo']['Monto'].sum(),
        })
    ).reset_index()
    
    proyectos['Margen Bruto'] = proyectos['Ingresos'] - proyectos['Costos Directos']
    proyectos['Margen %'] = (proyectos['Margen Bruto'] / proyectos['Ingresos'] * 100).fillna(0)
    
    st.dataframe(proyectos.style.format({
        'Ingresos': '${:,.0f}', 
        'Costos Directos': '${:,.0f}', 
        'Margen Bruto': '${:,.0f}',
        'Margen %': '{:.1f}%'
    }), use_container_width=True)
    
    # Gráfico comparativo
    if not proyectos.empty:
        fig_proj = px.bar(proyectos, x='Proyecto', y=['Ingresos', 'Costos Directos'], barmode='group', title="Rentabilidad por Proyecto")
        st.plotly_chart(fig_proj, use_container_width=True)
    else:
        st.info("No hay transacciones asociadas a proyectos específicos aún.")