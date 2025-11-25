import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf
from io import BytesIO
from datetime import datetime, date, timedelta

# --- 1. CONFIGURACIÓN GLOBAL & ESTILOS MODERNOS ---
st.set_page_config(
    page_title="QD Corporate System",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# CSS para UI Moderna y Fluida
st.markdown("""
<style>
    /* Tipografía y Espaciado */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Tabs Modernos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        font-size: 14px;
        font-weight: 600;
        color: #555;
        border-radius: 6px;
        border: none;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f5f5f5;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #EEF2FF;
        color: #4F46E5;
    }

    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #4F46E5;
    }
    
    /* Contenedores */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE NEGOCIO ---

class FinancialEngine:
    @staticmethod
    def calculate_dcf(investment, cash_flows, rate):
        cash_flow_series = [-investment] + cash_flows
        vpn = npf.npv(rate, cash_flow_series)
        tir = npf.irr(cash_flow_series)
        return vpn, tir

    @staticmethod
    def classify_expense_auto(concepto):
        concepto = concepto.lower()
        mapping = {
            'taxi': 'Gastos de Viaje', 'uber': 'Gastos de Viaje', 'vuelo': 'Gastos de Viaje',
            'almuerzo': 'Gastos de Representación', 'restaurante': 'Gastos de Representación',
            'nómina': 'Beneficios a Empleados', 'sueldo': 'Beneficios a Empleados',
            'licencia': 'Amortización Intangibles', 'software': 'Amortización Intangibles',
            'computador': 'Propiedad, Planta y Equipo', 'silla': 'Propiedad, Planta y Equipo',
            'arriendo': 'Gastos por Arrendamiento (NIIF 16)', 'oficina': 'Gastos por Arrendamiento (NIIF 16)',
            'banco': 'Gastos Financieros', 'interés': 'Gastos Financieros',
            'cliente': 'Cuentas por Cobrar', 'factura': 'Cuentas por Pagar'
        }
        for key, val in mapping.items():
            if key in concepto:
                return val
        return "Otros Gastos Operacionales"

# --- 3. INICIALIZACIÓN DE ESTADO (BD) ---
def init_session_state():
    # A. LIBRO DIARIO
    if 'ledger' not in st.session_state:
        data = [
            {'Fecha': datetime(2023, 1, 1), 'Concepto': 'Capital Inicial', 'Entidad': 'Socios', 'Tipo': 'Patrimonio', 'Clasificacion_NIC': 'Capital Social', 'Monto': 50000000, 'Proyecto': 'General', 'Estado': 'Pagado', 'Comportamiento': 'Fijo'},
            {'Fecha': datetime(2023, 10, 5), 'Concepto': 'Venta Consultoría A', 'Entidad': 'Cliente A', 'Tipo': 'Ingreso', 'Clasificacion_NIC': 'Ingresos Ordinarios', 'Monto': 15000000, 'Proyecto': 'Consultoría X', 'Estado': 'Cobrado', 'Comportamiento': 'Variable'},
            {'Fecha': datetime(2023, 10, 12), 'Concepto': 'Nómina Operativa', 'Entidad': 'Personal', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Costo de Ventas', 'Monto': -6000000, 'Proyecto': 'Consultoría X', 'Estado': 'Pagado', 'Comportamiento': 'Variable'},
            {'Fecha': datetime(2023, 10, 15), 'Concepto': 'Arriendo', 'Entidad': 'Inmobiliaria', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Gastos de Administración', 'Monto': -1000000, 'Proyecto': 'General', 'Estado': 'Pagado', 'Comportamiento': 'Fijo'},
            {'Fecha': datetime(2023, 10, 20), 'Concepto': 'Pago Clientes', 'Entidad': 'Cliente A', 'Tipo': 'Activo', 'Clasificacion_NIC': 'Efectivo y Equivalentes', 'Monto': 5000000, 'Proyecto': 'General', 'Estado': 'Pagado', 'Comportamiento': 'Fijo'},
        ]
        st.session_state['ledger'] = pd.DataFrame(data)
    
    # Parche retrocompatibilidad
    if 'Comportamiento' not in st.session_state['ledger'].columns:
        st.session_state['ledger']['Comportamiento'] = 'Fijo'

    # B. PIPELINE CRM
    if 'pipeline' not in st.session_state:
        data_pipe = [
            {'Cliente': 'Alpha', 'Proyecto': 'Migración Cloud', 'Etapa': 'Negociación', 'Valor': 25000000, 'Probabilidad': 70, 'Fecha_Cierre': date(2023, 12, 15), 'Horas_Est': 200},
            {'Cliente': 'Beta', 'Proyecto': 'Auditoría', 'Etapa': 'Propuesta', 'Valor': 8000000, 'Probabilidad': 40, 'Fecha_Cierre': date(2024, 1, 20), 'Horas_Est': 80},
            {'Cliente': 'Gamma', 'Proyecto': 'Outsourcing', 'Etapa': 'Ganado', 'Valor': 5000000, 'Probabilidad': 100, 'Fecha_Cierre': date(2023, 9, 10), 'Horas_Est': 50},
            {'Cliente': 'Delta', 'Proyecto': 'Asesoría', 'Etapa': 'Perdido', 'Valor': 3000000, 'Probabilidad': 0, 'Fecha_Cierre': date(2023, 9, 15), 'Horas_Est': 20},
        ]
        st.session_state['pipeline'] = pd.DataFrame(data_pipe)

    # C. LIBRERÍA DE COSTOS
    if 'cost_library' not in st.session_state:
        st.session_state['cost_library'] = pd.DataFrame([
            {'Nombre': 'Hora Developer Senior', 'Unidad': 'Hora', 'Costo_Unitario': 45000, 'Categoria': 'RRHH'},
            {'Nombre': 'Licencia Cloud', 'Unidad': 'Mensual', 'Costo_Unitario': 25000, 'Categoria': 'Tecnología'},
        ])

    # D. CARTERA DE PROYECTOS
    if 'projects_db' not in st.session_state:
        st.session_state['projects_db'] = pd.DataFrame(columns=[
            'Nombre_Proyecto', 'Cliente', 'Estado', 'Ingresos_Est', 'Costos_Directos_Est', 'Margen_Est', 'Horas_Est'
        ])
    
    # E. VARIABLES DE MARKETING (Para CAC)
    if 'marketing_spend' not in st.session_state:
        st.session_state['marketing_spend'] = 1000000 # Valor por defecto simulado

init_session_state()

# --- 4. COMPONENTE DE CARGA MASIVA ---
def render_bulk_loader(target_key, cols, title):
    with st.expander(f"📥 Carga Masiva: {title}", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            df_t = pd.DataFrame(columns=cols)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_t.to_excel(writer, index=False)
            st.download_button(f"Bajar Plantilla", output.getvalue(), f"template_{title}.xlsx")
        with c2:
            up = st.file_uploader(f"Subir Excel", type=['xlsx'], key=f"up_{title}")
            if up:
                try:
                    df_new = pd.read_excel(up)
                    for col in cols:
                        if col not in df_new.columns:
                            df_new[col] = 0 if 'Monto' in col else ''
                    st.session_state[target_key] = pd.concat([st.session_state[target_key], df_new], ignore_index=True)
                    st.success("Carga exitosa")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 5. INTERFAZ PRINCIPAL (SIDEBAR) ---
with st.sidebar:
    st.title("QD Corporate System")
    st.caption("v5.0 Enterprise Edition")
    
    # Menú Reordenado
    menu = st.radio("Navegación", [
        "1. Operaciones Diarias",
        "2. Pricing & Cartera",
        "3. CRM & Pipeline",
        "4. Finanzas (EEFF)",
        "5. Estrategia & Evaluación",
        "6. Balanced Scorecard",
        "7. Proyecciones"
    ])
    st.divider()

# =============================================================================
# MÓDULO 1: OPERACIONES DIARIAS
# =============================================================================
if menu == "1. Operaciones Diarias":
    st.header("📝 Operaciones & Libro Diario")
    
    tab_ops1, tab_ops2 = st.tabs(["Registro Manual", "Histórico & Carga"])
    
    with tab_ops1:
        with st.container(border=True):
            st.subheader("Nuevo Movimiento")
            with st.form("manual_entry", clear_on_submit=True):
                c1, c2 = st.columns(2)
                fecha = c1.date_input("Fecha")
                concepto = c2.text_input("Concepto / Glosa")
                
                sugerencia = FinancialEngine.classify_expense_auto(concepto) if concepto else "Otros Gastos"
                
                entidad = c1.text_input("Entidad")
                tipo = c2.selectbox("Tipo", ["Gasto", "Ingreso", "Activo", "Pasivo", "Patrimonio"])
                
                opciones_nic = [
                    "Ingresos Ordinarios", "Costo de Ventas", "Gastos de Administración", 
                    "Gastos de Ventas", "Beneficios a Empleados", "Gastos Financieros",
                    "Propiedad, Planta y Equipo", "Efectivo y Equivalentes", "Cuentas por Cobrar", "Cuentas por Pagar"
                ]
                
                idx_nic = opciones_nic.index(sugerencia) if sugerencia in opciones_nic else 0
                clasif_nic = c1.selectbox("Clasificación NIC", opciones_nic, index=idx_nic)
                
                comportamiento = c2.selectbox("Comportamiento", ["Fijo", "Variable"])
                monto = c1.number_input("Monto", min_value=0.0)
                
                proyectos_crm = ["General"] + st.session_state['pipeline']['Proyecto'].unique().tolist()
                proyecto = c2.selectbox("Proyecto Asociado", proyectos_crm)
                
                if st.form_submit_button("Registrar Movimiento"):
                    signo = -1 if tipo in ["Gasto", "Activo"] else 1
                    new_row = {
                        'Fecha': datetime.combine(fecha, datetime.min.time()),
                        'Concepto': concepto, 'Entidad': entidad, 'Tipo': tipo,
                        'Clasificacion_NIC': clasif_nic, 'Monto': monto * signo,
                        'Proyecto': proyecto, 'Estado': 'Pendiente', 'Comportamiento': comportamiento
                    }
                    st.session_state['ledger'] = pd.concat([st.session_state['ledger'], pd.DataFrame([new_row])], ignore_index=True)
                    st.success("Registrado correctamente")

    with tab_ops2:
        cols_ledger = ['Fecha', 'Concepto', 'Entidad', 'Tipo', 'Clasificacion_NIC', 'Monto', 'Proyecto', 'Estado', 'Comportamiento']
        render_bulk_loader('ledger', cols_ledger, "Libro Diario")
        st.dataframe(st.session_state['ledger'].sort_values('Fecha', ascending=False), use_container_width=True)

# =============================================================================
# MÓDULO 2: PRICING & CARTERA
# =============================================================================
elif menu == "2. Pricing & Cartera":
    st.header("🏷️ Pricing & Gestión de Proyectos")
    
    tabs_price = st.tabs(["Calculadora de Precios", "Cartera de Proyectos", "Librería Costos"])
    
    with tabs_price[0]:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.container(border=True):
                st.subheader("Configuración")
                p_nom = st.text_input("Nombre Proyecto")
                cliente_p = st.selectbox("Cliente", ["Nuevo"] + st.session_state['pipeline']['Cliente'].unique().tolist())
                
                lib = st.session_state['cost_library']
                item = st.selectbox("Agregar Recurso", lib['Nombre'].tolist())
                qty = st.number_input("Cantidad", 1)
                
                if 'temp_items' not in st.session_state: st.session_state['temp_items'] = []
                if st.button("Añadir Item"):
                    row = lib[lib['Nombre']==item].iloc[0]
                    st.session_state['temp_items'].append({'Item': item, 'Costo': row['Costo_Unitario']*qty})
                
                st.dataframe(pd.DataFrame(st.session_state['temp_items']), height=150, use_container_width=True)
            
        with c2:
            with st.container(border=True):
                st.subheader("Rentabilidad")
                costo_dir = sum([x['Costo'] for x in st.session_state['temp_items']])
                st.metric("Costo Directo Total", f"${costo_dir:,.0f}")
                
                overhead = st.slider("Overhead / Indirectos %", 0, 50, 20)
                margen = st.slider("Margen Objetivo %", 10, 80, 30)
                
                costo_full = costo_dir * (1 + overhead/100)
                precio = costo_full / (1 - margen/100) if margen < 100 else 0
                
                st.metric("Precio Venta Sugerido", f"${precio:,.0f}", delta=f"Margen Neto: ${(precio - costo_full):,.0f}")
                
                horas_est = st.number_input("Horas Totales Estimadas", 100)
                
                if st.button("💾 Guardar Proyecto en Cartera", type="primary"):
                    new_p = {
                        'Nombre_Proyecto': p_nom, 
                        'Cliente': cliente_p,
                        'Estado': 'Evaluación', 
                        'Ingresos_Est': precio, 
                        'Costos_Directos_Est': costo_dir, # Usamos esto como Proxy de Inversión para flujo
                        'Margen_Est': margen/100, 
                        'Horas_Est': horas_est
                    }
                    st.session_state['projects_db'] = pd.concat([st.session_state['projects_db'], pd.DataFrame([new_p])], ignore_index=True)
                    st.success("Proyecto guardado exitosamente")
                    st.session_state['temp_items'] = []

with tabs_price[1]:
        st.subheader("Cartera de Proyectos")
        df_p = st.session_state['projects_db']
        
        if not df_p.empty:
            # --- INICIO CORRECCIÓN ERROR ---
            # 1. Convertir forzosamente a números (por si se guardaron como texto)
            cols_numericas = ['Ingresos_Est', 'Margen_Est', 'Horas_Est']
            for col in cols_numericas:
                if col in df_p.columns:
                    df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0)
            
            # 2. Crear una columna temporal para el tamaño (evitar ceros que rompen Plotly)
            # Si horas es <= 0, le ponemos tamaño 1 para que no falle, pero se vea pequeña
            df_p['Size_Plot'] = df_p['Horas_Est'].apply(lambda x: max(float(x), 1.0))
            # -------------------------------

            st.dataframe(df_p.drop(columns=['Size_Plot'], errors='ignore'), use_container_width=True)
            
            try:
                fig_bub = px.scatter(
                    df_p, 
                    x="Ingresos_Est", 
                    y="Margen_Est", 
                    size="Size_Plot", # Usamos la columna segura
                    color="Estado", 
                    title="Mapa de Valor vs Rentabilidad",
                    hover_data=['Nombre_Proyecto', 'Horas_Est'], # Mostrar nombre al pasar mouse
                    labels={'Size_Plot': 'Esfuerzo (Horas)'}
                )
                st.plotly_chart(fig_bub, use_container_width=True)
            except Exception as e:
                st.warning(f"No hay suficientes datos válidos para generar el gráfico aún. ({e})")
        else:
            st.info("No hay proyectos guardados.")

    with tabs_price[2]:
        render_bulk_loader('cost_library', ['Nombre', 'Unidad', 'Costo_Unitario', 'Categoria'], "Librería")
        st.data_editor(st.session_state['cost_library'], num_rows="dynamic", use_container_width=True)

# =============================================================================
# MÓDULO 3: CRM & PIPELINE
# =============================================================================
elif menu == "3. CRM & Pipeline":
    st.header("🚀 CRM & Inteligencia de Ventas")
    
    tabs_crm = st.tabs(["KPIs Ventas & CAC", "Pipeline Visual", "Gestión Datos"])
    
    df_pipe = st.session_state['pipeline']
    
    with tabs_crm[0]:
        st.subheader("Indicadores de Eficiencia Comercial")
        
        # Inputs para cálculo
        with st.expander("Configuración Métricas (Gastos Marketing)", expanded=False):
            marketing_spend = st.number_input("Gasto Marketing Mensual (Simulado)", value=1000000)
            avg_lifespan = st.number_input("Vida Promedio Cliente (Meses)", value=12)
        
        # Cálculos
        ganados = df_pipe[df_pipe['Etapa'] == 'Ganado']
        cerrados = df_pipe[df_pipe['Etapa'].isin(['Ganado', 'Perdido'])]
        nuevos_clientes = len(ganados)
        
        # 1. Tasa de Conversión
        conversion_rate = (len(ganados) / len(cerrados) * 100) if len(cerrados) > 0 else 0
        
        # 2. CAC (Costo Adquisición)
        cac = marketing_spend / nuevos_clientes if nuevos_clientes > 0 else 0
        
        # 3. Ticket Promedio
        ticket_promedio = ganados['Valor'].mean() if nuevos_clientes > 0 else 0
        
        # 4. CLV (Customer Lifetime Value) - Simplificado
        # CLV = Ticket * Frecuencia (asumimos 1 mensual) * Vida
        clv = ticket_promedio * 1 * avg_lifespan
        
        # Visualización
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tasa de Conversión", f"{conversion_rate:.1f}%")
        k2.metric("CAC (Costo Adquisición)", f"${cac:,.0f}")
        k3.metric("Ticket Promedio", f"${ticket_promedio:,.0f}")
        k4.metric("CLV Estimado", f"${clv:,.0f}", help="Valor de Vida del Cliente", delta=f"Ratio CLV/CAC: {(clv/cac if cac>0 else 0):.1f}x")

    with tabs_crm[1]:
        # Funnel
        funnel_df = df_pipe.groupby('Etapa')['Valor'].sum().reset_index()
        orden = ["Lead", "Propuesta", "Negociación", "Ganado", "Perdido"]
        funnel_df['Etapa'] = pd.Categorical(funnel_df['Etapa'], categories=orden, ordered=True)
        funnel_df = funnel_df.sort_values('Etapa')
        
        c_chart, c_data = st.columns([2, 1])
        with c_chart:
            fig_funnel = px.funnel(funnel_df, x='Valor', y='Etapa', title="Embudo de Ventas")
            st.plotly_chart(fig_funnel, use_container_width=True)
        with c_data:
            st.metric("Total Pipeline", f"${df_pipe['Valor'].sum():,.0f}")
            st.metric("Forecast Ponderado", f"${(df_pipe['Valor'] * df_pipe['Probabilidad']/100).sum():,.0f}")

    with tabs_crm[2]:
        render_bulk_loader('pipeline', ['Cliente', 'Proyecto', 'Etapa', 'Valor', 'Probabilidad', 'Fecha_Cierre', 'Horas_Est'], "Pipeline")
        st.data_editor(st.session_state['pipeline'], num_rows="dynamic", use_container_width=True)

# =============================================================================
# MÓDULO 4: FINANZAS (EEFF)
# =============================================================================
elif menu == "4. Finanzas (EEFF)":
    st.header("📊 Estados Financieros e Indicadores")
    
    df = st.session_state['ledger'].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Periodo'] = df['Fecha'].dt.to_period('M').astype(str)
    
    tabs_fin = st.tabs(["Indicadores Clave", "Estado de Resultados", "Balance General", "Flujo de Caja"])
    
    with tabs_fin[0]:
        st.subheader("KPIs Financieros Corporativos")
        
        # Cálculos de Masas Patrimoniales
        activos_cte = df[(df['Tipo']=='Activo') & (df['Clasificacion_NIC'].isin(['Efectivo y Equivalentes', 'Cuentas por Cobrar']))]['Monto'].sum()
        pasivos_cte = abs(df[(df['Tipo']=='Pasivo') & (df['Clasificacion_NIC'].isin(['Cuentas por Pagar', 'Impuestos por Pagar']))]['Monto'].sum())
        total_activos = df[df['Tipo']=='Activo']['Monto'].sum()
        total_pasivos = abs(df[df['Tipo']=='Pasivo']['Monto'].sum())
        patrimonio = abs(df[df['Tipo']=='Patrimonio']['Monto'].sum())
        
        # Cálculos de Resultados
        ingresos = df[df['Tipo']=='Ingreso']['Monto'].sum()
        costos_venta = abs(df[df['Clasificacion_NIC']=='Costo de Ventas']['Monto'].sum())
        gastos_op = abs(df[df['Clasificacion_NIC'].isin(['Gastos de Administración', 'Gastos de Ventas'])]['Monto'].sum())
        
        utilidad_bruta = ingresos - costos_venta
        ebitda = utilidad_bruta - gastos_op # Simplificado (asumiendo gastos op no incluyen depreciacion aqui)
        utilidad_neta = ebitda # - impuestos - intereses
        
        # Ratios
        liquidez = activos_cte / pasivos_cte if pasivos_cte > 0 else 0
        apalancamiento = total_pasivos / patrimonio if patrimonio > 0 else 0
        margen_bruto = (utilidad_bruta / ingresos * 100) if ingresos > 0 else 0
        margen_neto = (utilidad_neta / ingresos * 100) if ingresos > 0 else 0
        roi = (utilidad_neta / (total_activos if total_activos > 0 else 1)) * 100
        
        # Display
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Margen Bruto", f"{margen_bruto:.1f}%")
        col2.metric("EBITDA", f"${ebitda:,.0f}")
        col3.metric("Margen Neto", f"{margen_neto:.1f}%")
        col4.metric("ROI (Retorno Inv.)", f"{roi:.1f}%")
        col5.metric("Ingresos Totales", f"${ingresos:,.0f}")
        
        col6, col7 = st.columns(2)
        col6.metric("Liquidez Corriente", f"{liquidez:.2f}", delta="Meta > 1.0")
        col7.metric("Apalancamiento (D/E)", f"{apalancamiento:.2f}", delta="Meta < 2.0", delta_color="inverse")

    with tabs_fin[1]:
        st.subheader("P&L (Estado de Resultados)")
        df_pnl = df[df['Tipo'].isin(['Ingreso', 'Gasto'])]
        pivot_pnl = df_pnl.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum', fill_value=0)
        st.dataframe(pivot_pnl.style.format("${:,.0f}"), use_container_width=True)

    with tabs_fin[2]:
        st.subheader("Balance General")
        df_bal = df[df['Tipo'].isin(['Activo', 'Pasivo', 'Patrimonio'])]
        pivot_bal = df_bal.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum').cumsum(axis=1).fillna(0)
        st.dataframe(pivot_bal.style.format("${:,.0f}"), use_container_width=True)

    with tabs_fin[3]:
        st.subheader("Cash Flow")
        df_cash = df[df['Estado'].isin(['Pagado', 'Cobrado', 'Pagado/Cobrado'])]
        cash = df_cash.groupby('Periodo')['Monto'].sum()
        st.bar_chart(cash)

# =============================================================================
# MÓDULO 5: ESTRATEGIA & EVALUACIÓN (CON INTEGRACIÓN PRICING)
# =============================================================================
elif menu == "5. Estrategia & Evaluación":
    st.header("♟️ Ingeniería Financiera de Proyectos")
    
    tabs_strat = st.tabs(["Evaluación Proyectos (VPN/TIR)", "Simulación Riesgo"])
    
    with tabs_strat[0]:
        st.subheader("Evaluación desde Cartera")
        
        col_sel, col_calc = st.columns([1, 2])
        
        with col_sel:
            st.markdown("Seleccione un proyecto cotizado:")
            proyectos_db = st.session_state['projects_db']
            
            if not proyectos_db.empty:
                opciones_proy = proyectos_db['Nombre_Proyecto'].tolist()
                seleccion = st.selectbox("Proyecto a Evaluar", opciones_proy)
                
                # Obtener datos del proyecto seleccionado
                datos_proy = proyectos_db[proyectos_db['Nombre_Proyecto'] == seleccion].iloc[0]
                inv_sug = datos_proy['Costos_Directos_Est'] # Proxy Inversión
                ing_sug = datos_proy['Ingresos_Est'] # Ingreso Total
                
                st.info(f"Datos Cargados:\n\nCosto Est: ${inv_sug:,.0f}\n\nVenta Est: ${ing_sug:,.0f}")
            else:
                st.warning("No hay proyectos en cartera.")
                inv_sug, ing_sug = 10000000, 15000000 # Default

        with col_calc:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                inv = c1.number_input("Inversión Inicial (Capex)", value=float(inv_sug))
                years = c2.slider("Duración (Años)", 1, 10, 5)
                
                # Asumimos que el ingreso del pricing es anual o total? 
                # Para el modelo simplificado, asumiremos que genera un margen anual del 20% del valor venta
                flujo_est = c1.number_input("Flujo Neto Anual Estimado", value=float(ing_sug * 0.2)) 
                tasa = c2.number_input("Tasa Descuento (WACC) %", 12.0) / 100
                
                if st.button("Calcular Indicadores", type="primary"):
                    vpn, tir = FinancialEngine.calculate_dcf(inv, [flujo_est]*years, tasa)
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric("VPN (Valor Presente)", f"${vpn:,.0f}", delta="Viable" if vpn>0 else "No Viable")
                    k2.metric("TIR (Tasa Interna)", f"{tir*100:.2f}%", delta=f"vs Tasa {tasa*100:.1f}%")
                    k3.metric("Payback", f"{(inv/flujo_est):.1f} Años")

    with tabs_strat[1]:
        st.subheader("Simulación Monte Carlo")
        if st.button("Ejecutar Simulación de Riesgo"):
            res = FinancialEngine.monte_carlo_simulation(flujo_est, flujo_est*0.5, inv, tasa, 0.27)
            fig_hist = px.histogram(x=res, title="Distribución de Resultados Posibles (VPN)", color_discrete_sequence=['#6366f1'])
            st.plotly_chart(fig_hist, use_container_width=True)

# =============================================================================
# MÓDULO 6: BALANCED SCORECARD
# =============================================================================
elif menu == "6. Balanced Scorecard":
    st.header("🚦 Cuadro de Mando Integral (BSC)")
    
    # Recalcular métricas globales
    df_l = st.session_state['ledger']
    ingresos_tot = df_l[df_l['Tipo']=='Ingreso']['Monto'].sum()
    ebitda_val = ingresos_tot - abs(df_l[df_l['Tipo']=='Gasto']['Monto'].sum()) # Aprox
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("1. Financiera")
            st.metric("Ingresos Totales", f"${ingresos_tot:,.0f}", delta="Meta Anual")
            st.metric("EBITDA", f"${ebitda_val:,.0f}")
            st.progress(0.7) # Simulado
            
    with col2:
        with st.container(border=True):
            st.subheader("2. Clientes")
            pipe_val = st.session_state['pipeline']['Valor'].sum()
            st.metric("Valor Pipeline", f"${pipe_val:,.0f}")
            st.metric("NPS (Encuesta)", "75/100")
            st.progress(0.8)

    col3, col4 = st.columns(2)
    
    with col3:
        with st.container(border=True):
            st.subheader("3. Procesos Internos")
            st.metric("Eficiencia Operativa", "85%")
            st.metric("Tiempo Entrega", "15 Días")
            st.progress(0.85)
            
    with col4:
        with st.container(border=True):
            st.subheader("4. Aprendizaje y Crecimiento")
            st.metric("Clima Laboral", "Bueno")
            st.metric("Capacitación", "40% Staff")
            st.progress(0.4)

# =============================================================================
# MÓDULO 7: PROYECCIONES
# =============================================================================
elif menu == "7. Proyecciones":
    st.header("🔮 Proyección de Crecimiento")
    
    col1, col2 = st.columns([1,3])
    with col1:
        with st.container(border=True):
            st.subheader("Escenario")
            escenario = st.selectbox("Selección", ["Conservador", "Base", "Optimista"])
            factor = 1.2 if escenario == "Optimista" else (0.8 if escenario == "Conservador" else 1.0)
            
            st.write("Variables:")
            inc_crm = st.checkbox("Incluir CRM", True)
            inc_pric = st.checkbox("Incluir Cartera", True)

    with col2:
        with st.container(border=True):
            # Datos Base
            base_ingresos = 10000000 # Promedio mensual simulado
            
            # Delta CRM
            pipe = st.session_state['pipeline']
            val_crm = (pipe['Valor'] * (pipe['Probabilidad']/100)).sum() * factor if inc_crm else 0
            
            # Delta Pricing
            projs = st.session_state['projects_db']
            val_pric = projs['Ingresos_Est'].sum() * 0.5 * factor if inc_pric and not projs.empty else 0
            
            total = base_ingresos + val_crm + val_pric
            growth_rate = ((total - base_ingresos) / base_ingresos) * 100
            
            st.metric("Ingresos Proyectados (Mes)", f"${total:,.0f}", delta=f"Crecimiento: {growth_rate:.1f}%")
            
            fig_w = go.Figure(go.Waterfall(
                x = ["Base Actual", "Oportunidades CRM", "Proyectos Cartera", "Total Proyectado"],
                y = [base_ingresos, val_crm, val_pric, 0],
                measure = ["relative", "relative", "relative", "total"],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            st.plotly_chart(fig_w, use_container_width=True)
