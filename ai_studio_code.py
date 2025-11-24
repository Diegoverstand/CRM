import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Gestión Integral QD",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .metric-container {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4F8BF9;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px;
        color: #31333F;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4F8BF9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE UTILIDAD ---
def convert_df_to_excel(df):
    """Convierte DataFrame a Excel en memoria para descarga."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def get_semaphor_color(val, target, inverse=False):
    """Determina color para BSC (Rojo/Amarillo/Verde)."""
    if inverse:
        if val <= target: return "green"
        elif val <= target * 1.1: return "orange"
        else: return "red"
    else:
        if val >= target: return "green"
        elif val >= target * 0.9: return "orange"
        else: return "red"

# --- INICIALIZACIÓN DE ESTADO (SESSION STATE) ---
if 'financial_data' not in st.session_state:
    # Datos semilla con estructura avanzada (incluye Costo Fijo/Variable)
    data_fin = [
        {'Fecha': datetime(2023, 10, 1), 'Concepto': 'Factura Cliente A', 'Tipo': 'Ingreso', 'Categoria': 'Ventas', 'Comportamiento': 'Variable', 'Monto': 15000000, 'Proyecto': 'Consultoría X'},
        {'Fecha': datetime(2023, 10, 5), 'Concepto': 'Nómina Consultores', 'Tipo': 'Egreso', 'Categoria': 'RRHH', 'Comportamiento': 'Fijo', 'Monto': 6000000, 'Proyecto': 'General'},
        {'Fecha': datetime(2023, 10, 10), 'Concepto': 'Licencias Cloud', 'Tipo': 'Egreso', 'Categoria': 'Tecnología', 'Comportamiento': 'Fijo', 'Monto': 800000, 'Proyecto': 'General'},
        {'Fecha': datetime(2023, 10, 12), 'Concepto': 'Subcontrato Diseño', 'Tipo': 'Egreso', 'Categoria': 'Costo Directo', 'Comportamiento': 'Variable', 'Monto': 2500000, 'Proyecto': 'Consultoría X'},
        {'Fecha': datetime(2023, 10, 20), 'Concepto': 'Arriendo Oficina', 'Tipo': 'Egreso', 'Categoria': 'Infraestructura', 'Comportamiento': 'Fijo', 'Monto': 1200000, 'Proyecto': 'General'},
        {'Fecha': datetime(2023, 10, 25), 'Concepto': 'Factura Cliente B', 'Tipo': 'Ingreso', 'Categoria': 'Ventas', 'Comportamiento': 'Variable', 'Monto': 9000000, 'Proyecto': 'Implementación Y'},
    ]
    st.session_state['financial_data'] = pd.DataFrame(data_fin)

if 'commercial_data' not in st.session_state:
    data_com = [
        {'Cliente': 'Alpha Corp', 'Servicio': 'Estrategia', 'Etapa': 'Propuesta', 'Valor': 5000000, 'Probabilidad': 60},
        {'Cliente': 'Beta Inc', 'Servicio': 'Auditoría', 'Etapa': 'Negociación', 'Valor': 2500000, 'Probabilidad': 80},
        {'Cliente': 'Gamma Ltd', 'Servicio': 'Desarrollo', 'Etapa': 'Lead', 'Valor': 12000000, 'Probabilidad': 20},
    ]
    st.session_state['commercial_data'] = pd.DataFrame(data_com)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830303.png", width=60)
    st.title("Gestión QD")
    st.markdown("---")
    
    # Filtros Globales de Fecha (Afectan a módulo financiero)
    st.header("🗓️ Filtros Globales")
    date_range = st.date_input(
        "Rango de Análisis",
        value=(datetime(2023, 10, 1), datetime(2023, 10, 31))
    )
    
    st.markdown("---")
    st.info("**Versión 2.0 (Pro)**\n\nIncluye análisis de sensibilidad y BSC.")

# --- TABS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Datos & Carga", 
    "💰 Finanzas Profundas", 
    "🏷️ Pricing & Escenarios", 
    "🚦 Balanced Scorecard"
])

# ==========================================
# TAB 1: GESTIÓN DE DATOS (DATA MANAGEMENT)
# ==========================================
with tab1:
    st.header("Gestión de Bases de Datos")
    st.markdown("Descarga templates, sube tus históricos o edita en vivo.")
    
    col_d1, col_d2 = st.columns(2)
    
    # --- SECCIÓN FINANCIERA ---
    with col_d1:
        st.subheader("1. Base Financiera")
        
        # Generar Template
        df_fin_template = pd.DataFrame(columns=['Fecha', 'Concepto', 'Tipo', 'Categoria', 'Comportamiento', 'Monto', 'Proyecto'])
        excel_fin = convert_df_to_excel(df_fin_template)
        
        st.download_button(
            label="📥 Descargar Template Finanzas (.xlsx)",
            data=excel_fin,
            file_name='template_finanzas_qd.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            help="Usa este archivo para cargar tus datos históricos."
        )
        
        # Cargar Datos
        uploaded_fin = st.file_uploader("Subir Excel Finanzas", type=['xlsx', 'csv'])
        if uploaded_fin:
            try:
                if uploaded_fin.name.endswith('.csv'):
                    df_new = pd.read_csv(uploaded_fin)
                else:
                    df_new = pd.read_excel(uploaded_fin)
                
                # Validación básica
                required_cols = ['Fecha', 'Tipo', 'Monto', 'Comportamiento']
                if all(col in df_new.columns for col in required_cols):
                    st.session_state['financial_data'] = df_new
                    st.success("✅ Base Financiera actualizada correctamente.")
                else:
                    st.error(f"❌ El archivo debe contener las columnas: {required_cols}")
            except Exception as e:
                st.error(f"Error al procesar archivo: {e}")

        # Editor CRUD
        st.markdown("**Edición en Vivo:**")
        edited_fin = st.data_editor(
            st.session_state['financial_data'], 
            num_rows="dynamic",
            column_config={
                "Tipo": st.column_config.SelectboxColumn(options=["Ingreso", "Egreso"]),
                "Comportamiento": st.column_config.SelectboxColumn(options=["Fijo", "Variable"], help="Vital para cálculo de Punto de Equilibrio"),
                "Fecha": st.column_config.DatetimeColumn(format="D/M/YYYY")
            },
            key="editor_fin"
        )
        st.session_state['financial_data'] = edited_fin

    # --- SECCIÓN COMERCIAL ---
    with col_d2:
        st.subheader("2. Pipeline Comercial")
        
        df_com_template = pd.DataFrame(columns=['Cliente', 'Servicio', 'Etapa', 'Valor', 'Probabilidad'])
        excel_com = convert_df_to_excel(df_com_template)
        
        st.download_button(
            label="📥 Descargar Template Pipeline (.xlsx)",
            data=excel_com,
            file_name='template_pipeline_qd.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        uploaded_com = st.file_uploader("Subir Excel Pipeline", type=['xlsx', 'csv'])
        if uploaded_com:
            try:
                df_new_com = pd.read_excel(uploaded_com) if uploaded_com.name.endswith('.xlsx') else pd.read_csv(uploaded_com)
                st.session_state['commercial_data'] = df_new_com
                st.success("✅ Pipeline actualizado.")
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("**Edición en Vivo:**")
        edited_com = st.data_editor(
            st.session_state['commercial_data'],
            num_rows="dynamic",
            column_config={
                "Etapa": st.column_config.SelectboxColumn(options=["Lead", "Propuesta", "Negociación", "Ganado", "Perdido"]),
                "Probabilidad": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")
            },
            key="editor_com"
        )
        st.session_state['commercial_data'] = edited_com

# ==========================================
# TAB 2: FINANZAS AVANZADAS (DEEP FINANCE)
# ==========================================
with tab2:
    st.header("Análisis Financiero Profundo")
    
    # 1. Preparación de Datos
    df = st.session_state['financial_data'].copy()
    
    # Convertir a datetime si no lo es
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Filtro por fecha (Sidebar)
    if len(date_range) == 2:
        mask = (df['Fecha'].dt.date >= date_range[0]) & (df['Fecha'].dt.date <= date_range[1])
        df_filtered = df.loc[mask]
    else:
        df_filtered = df

    if df_filtered.empty:
        st.warning("⚠️ No hay datos en el rango de fechas seleccionado.")
    else:
        # CÁLCULOS PRINCIPALES
        total_ingresos = df_filtered[df_filtered['Tipo'] == 'Ingreso']['Monto'].sum()
        total_egresos = df_filtered[df_filtered['Tipo'] == 'Egreso']['Monto'].sum()
        
        # Desglose Costos
        costos_variables = df_filtered[(df_filtered['Tipo'] == 'Egreso') & (df_filtered['Comportamiento'] == 'Variable')]['Monto'].sum()
        costos_fijos = df_filtered[(df_filtered['Tipo'] == 'Egreso') & (df_filtered['Comportamiento'] == 'Fijo')]['Monto'].sum()
        
        margen_contribucion = total_ingresos - costos_variables
        utilidad_neta = total_ingresos - total_egresos
        
        # Ratios
        margen_bruto_pct = (margen_contribucion / total_ingresos * 100) if total_ingresos > 0 else 0
        margen_neto_pct = (utilidad_neta / total_ingresos * 100) if total_ingresos > 0 else 0
        
        # Punto de Equilibrio (Break-even Point)
        # Fórmula: Costos Fijos / (Ratio Margen Contribución)
        ratio_mc = margen_contribucion / total_ingresos if total_ingresos > 0 else 0
        punto_equilibrio = costos_fijos / ratio_mc if ratio_mc > 0 else 0

        # --- PANEL DE INDICADORES ---
        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        col_k1.metric("Ingresos Totales", f"${total_ingresos:,.0f}", delta=f"{len(df_filtered)} movs")
        col_k2.metric("EBITDA / Margen Op.", f"${(total_ingresos - costos_variables - (costos_fijos*0.8)):,.0f}", help="Estimado simplificado") # Simplificación
        col_k3.metric("Utilidad Neta", f"${utilidad_neta:,.0f}", delta=f"{margen_neto_pct:.1f}%")
        col_k4.metric("Punto de Equilibrio", f"${punto_equilibrio:,.0f}", help="Ventas necesarias para cubrir costos fijos y variables", delta_color="off")

        st.divider()

        # --- SECCIÓN DE LIQUIDEZ (Input Manual Simulado) ---
        col_liq, col_graph = st.columns([1, 2])
        
        with col_liq:
            st.subheader("💧 Análisis de Liquidez")
            st.caption("Como el Balance General no se genera solo con P&L, ingresa saldos actuales:")
            activo_cte = st.number_input("Activo Corriente (Caja + CxC)", value=25000000)
            pasivo_cte = st.number_input("Pasivo Corriente (CxP Corto Plazo)", value=12000000)
            
            razon_corriente = activo_cte / pasivo_cte if pasivo_cte > 0 else 0
            st.metric("Razón Corriente", f"{razon_corriente:.2f}", delta="Objetivo > 1.5", delta_color="normal" if razon_corriente > 1.5 else "inverse")
            
            if razon_corriente < 1:
                st.error("⚠️ Alerta: Problemas potenciales de liquidez.")
            else:
                st.success("✅ Liquidez Saludable.")

        with col_graph:
            st.subheader("Evolución Ingresos vs Gastos")
            # Agrupar por mes
            df_chart = df_filtered.copy()
            df_chart['Mes'] = df_chart['Fecha'].dt.strftime('%Y-%m')
            grouped = df_chart.groupby(['Mes', 'Tipo'])['Monto'].sum().reset_index()
            
            fig_line = px.line(grouped, x='Mes', y='Monto', color='Tipo', markers=True, 
                               color_discrete_map={'Ingreso': '#28a745', 'Egreso': '#dc3545'})
            st.plotly_chart(fig_line, use_container_width=True)

        # --- GRÁFICO SUNBURST ---
        st.subheader("🔍 Desglose de Egresos (Drill-down)")
        df_egresos = df_filtered[df_filtered['Tipo'] == 'Egreso']
        if not df_egresos.empty:
            fig_sun = px.sunburst(df_egresos, path=['Categoria', 'Concepto'], values='Monto', 
                                  color='Categoria', title="¿En qué se gasta el dinero?")
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.info("No hay egresos registrados para mostrar.")

# ==========================================
# TAB 3: PRICING & SIMULADOR
# ==========================================
with tab3:
    st.header("🧪 Simulador de Estrategia de Precios")
    
    col_p1, col_p2 = st.columns([1, 2])
    
    with col_p1:
        st.subheader("1. Estructura de Costos")
        
        costo_hh = st.number_input("Costo Hora Hombre (Promedio)", value=35000)
        horas = st.number_input("Horas Estimadas Proyecto", value=100)
        materiales = st.number_input("Costos Directos (Licencias/Viáticos)", value=500000)
        overhead = st.slider("Overhead / Indirectos (%)", 0, 50, 15)
        
        costo_directo = (costo_hh * horas) + materiales
        costo_total = costo_directo * (1 + overhead/100)
        
        st.metric("Costo Base Total", f"${costo_total:,.0f}")
        
        margen_objetivo = st.slider("Margen Objetivo (%)", 10, 80, 30)
        precio_sugerido = costo_total / (1 - margen_objetivo/100)
        
        st.markdown(f"**Precio Sugerido:** :blue[${precio_sugerido:,.0f}]")
        
    with col_p2:
        st.subheader("2. Análisis de Sensibilidad & Mercado")
        
        precio_mercado = st.number_input("Precio Mercado (Competencia/Benchmark)", value=precio_sugerido * 0.95)
        
        # Slider de Sensibilidad
        sensibilidad = st.slider("Variación de Precio (Escenario What-If)", -20, 20, 0, format="%d%%")
        
        precio_simulado = precio_sugerido * (1 + sensibilidad/100)
        margen_simulado_monto = precio_simulado - costo_total
        margen_simulado_pct = (margen_simulado_monto / precio_simulado * 100)
        
        # Resultados de Simulación
        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.metric("Precio Simulado", f"${precio_simulado:,.0f}", delta=f"{sensibilidad}%")
        c_res2.metric("Nuevo Margen $", f"${margen_simulado_monto:,.0f}")
        
        color_delta = "normal" if margen_simulado_pct >= margen_objetivo else "inverse"
        c_res3.metric("Nuevo Margen %", f"{margen_simulado_pct:.1f}%", delta=f"Obj: {margen_objetivo}%", delta_color=color_delta)
        
        # Gráfico Comparativo
        data_sim = pd.DataFrame({
            'Escenario': ['Costo Base', 'Mercado', 'Precio Sugerido', 'Precio Simulado'],
            'Monto': [costo_total, precio_mercado, precio_sugerido, precio_simulado],
            'Color': ['grey', 'orange', 'blue', 'green']
        })
        
        fig_bar = px.bar(data_sim, x='Escenario', y='Monto', color='Escenario', text_auto='.2s', 
                         color_discrete_map={'Costo Base':'grey', 'Mercado':'orange', 'Precio Sugerido':'blue', 'Precio Simulado':'green'})
        fig_bar.add_hline(y=costo_total, line_dash="dot", annotation_text="Break-even Proyecto")
        st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# TAB 4: BALANCED SCORECARD (BSC)
# ==========================================
with tab4:
    st.header("🚦 Tablero de Mando Integral (BSC)")
    st.markdown("Visión holística de la empresa con indicadores Cuantitativos (Auto) y Cualitativos (Manual).")
    
    # --- 1. PERSPECTIVA FINANCIERA (Automático) ---
    st.subheader("1. Perspectiva Financiera")
    # Traemos datos calculados del Tab 2
    ingresos_mes = df_filtered[df_filtered['Tipo'] == 'Ingreso']['Monto'].sum()
    meta_ingresos = st.number_input("Meta Ingresos (Mes)", value=20000000)
    
    col_f1, col_f2 = st.columns(2)
    color_fin = get_semaphor_color(ingresos_mes, meta_ingresos)
    col_f1.markdown(f"#### Ingresos: :{color_fin}[${ingresos_mes:,.0f}] / ${meta_ingresos:,.0f}")
    col_f1.progress(min(ingresos_mes/meta_ingresos, 1.0))
    
    col_f2.metric("Estado Financiero", "En curso", delta="Datos reales", delta_color="off")

    st.markdown("---")

    # --- 2. PERSPECTIVA CLIENTES (Híbrido) ---
    st.subheader("2. Perspectiva Clientes")
    col_c1, col_c2 = st.columns(2)
    
    # Dato Cuantitativo (CRM)
    df_crm = st.session_state['commercial_data']
    ganadas = len(df_crm[df_crm['Etapa']=='Ganado'])
    total_cerradas = len(df_crm[df_crm['Etapa'].isin(['Ganado', 'Perdido'])])
    win_rate = (ganadas / total_cerradas * 100) if total_cerradas > 0 else 0
    
    col_c1.metric("Win Rate (Tasa Cierre)", f"{win_rate:.1f}%", delta="Obj: >30%")
    
    # Dato Cualitativo (Input)
    nps = col_c2.slider("NPS / Satisfacción Cliente (0-100)", 0, 100, 75)
    color_nps = get_semaphor_color(nps, 70)
    col_c2.markdown(f"**Salud Cliente:** :{color_nps}[{'Excelente' if nps>70 else 'Mejorable'}]")

    st.markdown("---")

    # --- 3. PERSPECTIVA PROCESOS INTERNOS (Manual) ---
    st.subheader("3. Perspectiva Procesos Internos")
    col_p1, col_p2 = st.columns(2)
    
    tiempo_entrega = col_p1.number_input("Tiempo Promedio Entrega (Días)", value=15)
    meta_entrega = 12
    color_proc = get_semaphor_color(tiempo_entrega, meta_entrega, inverse=True) # Menos es mejor
    
    col_p1.markdown(f"Performance Entrega: :{color_proc}[{'Dentro de meta' if tiempo_entrega <= meta_entrega else 'Retraso'}]")
    
    eficiencia = col_p2.slider("Índice de Eficiencia Operativa (%)", 0, 100, 85)
    col_p2.progress(eficiencia/100)

    st.markdown("---")

    # --- 4. PERSPECTIVA APRENDIZAJE Y CRECIMIENTO (Cualitativo) ---
    st.subheader("4. Aprendizaje y Crecimiento")
    col_l1, col_l2 = st.columns(2)
    
    clima = col_l1.select_slider("Clima Laboral", options=["Crítico", "Tenso", "Neutro", "Bueno", "Excelente"], value="Bueno")
    color_clima = "green" if clima in ["Bueno", "Excelente"] else "red"
    col_l1.markdown(f"Estado Equipo: :{color_clima}[{clima}]")
    
    capacitacion = col_l2.number_input("% Equipo Capacitado este Q", 0, 100, 40)
    col_l2.metric("Cobertura Capacitación", f"{capacitacion}%", delta="Meta: 50%")
