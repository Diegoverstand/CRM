import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime, timedelta
import numpy as np

# --- 1. CONFIGURACIÓN Y ESTILOS CORPORATIVOS ---
st.set_page_config(
    page_title="QD Corporate ERP",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilos Responsive y Corporativos */
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif; color: #2c3e50;}
    .stTabs [data-baseweb="tab-list"] {gap: 5px;}
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #2c3e50;
        color: white;
    }
    /* Alertas visuales */
    .alert-danger {color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;}
    .alert-success {color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO Y DATOS (DATABASE MOCKUP) ---

def init_session_state():
    # A. LIBRO DIARIO (Transacciones Reales)
    if 'ledger' not in st.session_state:
        # Estructura compatible con IFRS
        data = [
            # Activos Iniciales (Apertura)
            {'Fecha': datetime(2023, 1, 1), 'Concepto': 'Capital Inicial', 'Entidad': 'Socios', 'Tipo': 'Patrimonio', 'Clasificacion_NIC': 'Capital Social', 'Monto': 50000000, 'Proyecto': 'General', 'Estado': 'Pagado'},
            {'Fecha': datetime(2023, 1, 1), 'Concepto': 'Saldo Banco', 'Entidad': 'Banco Chile', 'Tipo': 'Activo', 'Clasificacion_NIC': 'Efectivo y Equivalentes', 'Monto': 20000000, 'Proyecto': 'General', 'Estado': 'Pagado'},
            # Operaciones
            {'Fecha': datetime(2023, 10, 5), 'Concepto': 'Servicio Consultoría A', 'Entidad': 'Cliente A', 'Tipo': 'Ingreso', 'Clasificacion_NIC': 'Ingresos Ordinarios', 'Monto': 15000000, 'Proyecto': 'Consultoría X', 'Estado': 'Cobrado'},
            {'Fecha': datetime(2023, 10, 10), 'Concepto': 'Licencias Azure', 'Entidad': 'Microsoft', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Gastos de Administración', 'Monto': -800000, 'Proyecto': 'General', 'Estado': 'Pagado'},
            {'Fecha': datetime(2023, 10, 12), 'Concepto': 'Nómina Octubre', 'Entidad': 'Personal', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Beneficios a Empleados', 'Monto': -6000000, 'Proyecto': 'General', 'Estado': 'Pagado'},
            {'Fecha': datetime(2023, 10, 15), 'Concepto': 'Compra Laptops', 'Entidad': 'PC Factory', 'Tipo': 'Activo', 'Clasificacion_NIC': 'Propiedad, Planta y Equipo', 'Monto': -4000000, 'Proyecto': 'General', 'Estado': 'Pagado'},
        ]
        st.session_state['ledger'] = pd.DataFrame(data)

    # B. PIPELINE COMERCIAL (CRM)
    if 'pipeline' not in st.session_state:
        data_pipe = [
            {'Cliente': 'Alpha Corp', 'Proyecto': 'Migración Cloud', 'Etapa': 'Negociación', 'Valor': 25000000, 'Probabilidad': 70, 'Fecha_Cierre': datetime(2023, 12, 15), 'Horas_Est': 200},
            {'Cliente': 'Beta Ltd', 'Proyecto': 'Auditoría Seg.', 'Etapa': 'Propuesta', 'Valor': 8000000, 'Probabilidad': 40, 'Fecha_Cierre': datetime(2024, 1, 20), 'Horas_Est': 80},
        ]
        st.session_state['pipeline'] = pd.DataFrame(data_pipe)

    # C. CARTERA DE PROYECTOS & PRICING (Base de Datos de Proyectos Aprobados/Guardados)
    if 'projects_db' not in st.session_state:
        st.session_state['projects_db'] = pd.DataFrame(columns=[
            'Nombre_Proyecto', 'Cliente', 'Estado', 'Ingresos_Est', 'Costos_Directos_Est', 'Margen_Est', 'Horas_Est', 'Horas_Reales', 'Fecha_Inicio'
        ])
    
    # D. LIBRERÍA DE VARIABLES DE COSTOS (Para Pricing)
    if 'cost_library' not in st.session_state:
        st.session_state['cost_library'] = pd.DataFrame([
            {'Nombre': 'Hora Developer Senior', 'Unidad': 'Hora', 'Costo_Unitario': 45000, 'Categoria': 'RRHH'},
            {'Hora': 'Hora Consultor Junior', 'Unidad': 'Hora', 'Costo_Unitario': 25000, 'Categoria': 'RRHH'},
            {'Nombre': 'Licencia PowerBI', 'Unidad': 'Mensual', 'Costo_Unitario': 15000, 'Categoria': 'Software'},
        ])

    # E. VARIABLES GLOBALES DE CONFIGURACIÓN
    if 'config' not in st.session_state:
        st.session_state['config'] = {'capacidad_horas_mensual': 600} # Ejemplo: 4 personas * 150 hrs

init_session_state()

# --- 3. FUNCIONES CORE ---

def classify_expense_auto(concepto):
    """Clasificador simple basado en IFRS/NIC sugerido"""
    concepto = concepto.lower()
    mapping = {
        'taxi': 'Gastos de Viaje', 'uber': 'Gastos de Viaje', 'vuelo': 'Gastos de Viaje',
        'almuerzo': 'Gastos de Representación', 'restaurante': 'Gastos de Representación',
        'nómina': 'Beneficios a Empleados', 'sueldo': 'Beneficios a Empleados',
        'licencia': 'Amortización Intangibles', 'software': 'Amortización Intangibles',
        'computador': 'Propiedad, Planta y Equipo', 'silla': 'Propiedad, Planta y Equipo',
        'arriendo': 'Gastos por Arrendamiento (NIIF 16)', 'oficina': 'Gastos por Arrendamiento (NIIF 16)',
        'banco': 'Gastos Financieros', 'interés': 'Gastos Financieros'
    }
    for key, val in mapping.items():
        if key in concepto:
            return val
    return "Otros Gastos Operacionales"

def generate_financial_report(df, period='M'):
    """Genera reportes agrupados por periodo"""
    df['Periodo'] = df['Fecha'].dt.to_period(period).astype(str)
    return df

# --- 4. UI: SIDEBAR & NAVEGACIÓN ---
with st.sidebar:
    st.title("QD Corporate System")
    st.caption("v.3.5.0 - Enterprise Edition")
    
    menu = st.radio("Módulos", [
        "1. Operaciones Diarias (Gastos)", 
        "2. Finanzas Deep Dive", 
        "3. Pricing & Cartera",
        "4. Proyecciones & Escenarios",
        "5. Tablero BSC"
    ])
    
    st.markdown("---")
    st.info("Sistema conectado a Pipeline y Pricing en tiempo real.")

# ==============================================================================
# MÓDULO 1: OPERACIONES DIARIAS (GASTOS E INGRESOS NIC/IFRS)
# ==============================================================================
if menu == "1. Operaciones Diarias (Gastos)":
    st.header("📝 Registro de Operaciones (Norma IFRS)")
    st.markdown("Ingrese los movimientos diarios para alimentar la contabilidad y flujos de caja.")
    
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Nuevo Movimiento")
            with st.form("expense_form", clear_on_submit=True):
                fecha = st.date_input("Fecha Comprobante")
                concepto = st.text_input("Concepto / Glosa")
                
                # Lógica de autocompletado
                sugerencia_nic = classify_expense_auto(concepto) if concepto else "Otros Gastos Operacionales"
                
                entidad = st.text_input("Entidad (Proveedor/Cliente/Empleado)")
                
                tipo_mov = st.selectbox("Tipo de Movimiento", ["Gasto", "Ingreso", "Activo (Inversión)", "Pasivo (Deuda)", "Patrimonio"])
                
                # Lista NIC extendida
                opciones_nic = [
                    "Ingresos Ordinarios", "Costo de Ventas", 
                    "Gastos de Administración", "Gastos de Ventas", "Beneficios a Empleados",
                    "Gastos Financieros", "Gastos por Arrendamiento (NIIF 16)", 
                    "Propiedad, Planta y Equipo", "Efectivo y Equivalentes",
                    "Cuentas por Cobrar", "Cuentas por Pagar", "Impuestos por Pagar"
                ]
                
                # Preseleccionar si hay coincidencia
                idx_sel = opciones_nic.index(sugerencia_nic) if sugerencia_nic in opciones_nic else 0
                clasificacion = st.selectbox("Clasificación IFRS/NIC", opciones_nic, index=idx_sel)
                
                col_amt, col_tax = st.columns(2)
                monto = col_amt.number_input("Monto Total (Bruto)", min_value=0.0, format="%.2f")
                es_egreso = tipo_mov in ["Gasto", "Activo (Inversión)"] # Lógica simplificada signo
                
                proyecto = st.selectbox("Centro de Costo / Proyecto", ["General"] + st.session_state['pipeline']['Proyecto'].unique().tolist())
                estado = st.selectbox("Estado Flujo", ["Pagado/Cobrado", "Pendiente (Devengado)"])
                
                obs = st.text_area("Detalle / ID Comprobante")
                
                submitted = st.form_submit_button("💾 Registrar Asiento")
                
                if submitted:
                    signo = -1 if es_egreso else 1
                    nuevo_asiento = {
                        'Fecha': datetime.combine(fecha, datetime.min.time()),
                        'Concepto': concepto,
                        'Entidad': entidad,
                        'Tipo': tipo_mov,
                        'Clasificacion_NIC': clasificacion,
                        'Monto': monto * signo,
                        'Proyecto': proyecto,
                        'Estado': estado
                    }
                    st.session_state['ledger'] = pd.concat([st.session_state['ledger'], pd.DataFrame([nuevo_asiento])], ignore_index=True)
                    st.success("Movimiento registrado en Libro Diario.")

        with col2:
            st.subheader("📖 Libro Diario (Últimos Movimientos)")
            df_ledger = st.session_state['ledger'].sort_values('Fecha', ascending=False)
            
            # Filtros rápidos
            f_proyecto = st.multiselect("Filtrar por Proyecto", df_ledger['Proyecto'].unique())
            if f_proyecto:
                df_ledger = df_ledger[df_ledger['Proyecto'].isin(f_proyecto)]
                
            st.dataframe(
                df_ledger[['Fecha', 'Concepto', 'Tipo', 'Clasificacion_NIC', 'Monto', 'Estado']], 
                use_container_width=True,
                height=500
            )

# ==============================================================================
# MÓDULO 2: FINANZAS DEEP DIVE (ESTADOS FINANCIEROS)
# ==============================================================================
elif menu == "2. Finanzas Deep Dive":
    st.header("📊 Estados Financieros & Análisis Profundo")
    
    # Controles de Periodo
    c_per1, c_per2 = st.columns([1, 4])
    agrupacion = c_per1.selectbox("Agrupar por:", ["M", "Q", "Y"], format_func=lambda x: {"M":"Mensual", "Q":"Trimestral", "Y":"Anual"}[x])
    
    df = st.session_state['ledger'].copy()
    df['Periodo'] = df['Fecha'].dt.to_period(agrupacion).astype(str)
    
    tabs_fin = st.tabs(["📉 Estado de Resultados (P&L)", "⚖️ Balance General", "💸 Flujo de Caja", "📈 Indicadores KPI"])
    
    with tabs_fin[0]: # P&L
        st.subheader("Estado de Resultados Integral")
        # Filtrar solo Ingresos y Gastos
        df_pnl = df[df['Tipo'].isin(['Ingreso', 'Gasto'])]
        
        pivot_pnl = df_pnl.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum', fill_value=0)
        
        # Ordenar filas lógicas
        ingresos = pivot_pnl.loc[pivot_pnl.index.str.contains('Ingresos')].sum()
        costos = pivot_pnl.loc[pivot_pnl.index.str.contains('Costo') | pivot_pnl.index.str.contains('Beneficios')].sum()
        gastos = pivot_pnl.loc[pivot_pnl.index.str.contains('Gastos')].sum()
        
        res_operacional = ingresos + costos + gastos # Suma porque gastos son negativos
        
        st.dataframe(pivot_pnl.style.format("${:,.0f}").background_gradient(cmap="RdYlGn", axis=None), use_container_width=True)
        
        st.markdown("#### Resultado Operacional del Periodo")
        fig_res = px.bar(x=res_operacional.index, y=res_operacional.values, title="Utilidad/Pérdida Neta por Periodo")
        st.plotly_chart(fig_res, use_container_width=True)

    with tabs_fin[1]: # Balance
        st.subheader("Balance Financiero (Situación)")
        # Lógica simplificada de acumulación de saldos
        df_bal = df[df['Tipo'].isin(['Activo', 'Pasivo', 'Patrimonio', 'Activo (Inversión)', 'Pasivo (Deuda)'])]
        pivot_bal = df_bal.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum').cumsum(axis=1).fillna(0)
        st.dataframe(pivot_bal.style.format("${:,.0f}"), use_container_width=True)
        
    with tabs_fin[2]: # Cash Flow
        st.subheader("Flujo de Caja (Método Directo)")
        # Filtrar solo lo efectivamente pagado/cobrado
        df_cash = df[df['Estado'] == 'Pagado/Cobrado']
        cash_flow = df_cash.groupby('Periodo')['Monto'].sum()
        
        col_cf1, col_cf2 = st.columns([3,1])
        with col_cf1:
            fig_cf = go.Figure()
            fig_cf.add_trace(go.Waterfall(
                x = cash_flow.index, y = cash_flow.values,
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            st.plotly_chart(fig_cf, use_container_width=True)
        with col_cf2:
            st.metric("Caja Neta Periodo Actual", f"${cash_flow.iloc[-1]:,.0f}" if len(cash_flow)>0 else "$0")

    with tabs_fin[3]: # KPIs
        st.subheader("Indicadores de Salud Financiera")
        # Simulación de ratios ya que faltan datos de balance completo doble partida
        ingresos_tot = df[df['Tipo']=='Ingreso']['Monto'].sum()
        costos_tot = df[df['Tipo']=='Gasto']['Monto'].sum()
        margen_neto = (ingresos_tot + costos_tot) / ingresos_tot if ingresos_tot > 0 else 0
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Margen Neto Histórico", f"{margen_neto*100:.1f}%")
        k2.metric("Burn Rate Promedio", f"${abs(costos_tot/len(df['Periodo'].unique())):,.0f}/mes")
        k3.metric("Ratio Cobertura", "1.2x", delta="Simulado")
        k4.metric("ROI Proyectos", "18%", delta="Simulado")

# ==============================================================================
# MÓDULO 3: PRICING AVANZADO Y CARTERA DE PROYECTOS
# ==============================================================================
elif menu == "3. Pricing & Cartera":
    st.header("🏷️ Pricing Estructurado & Cartera")
    
    subtabs_pricing = st.tabs(["🧮 Calculadora & Cotizador", "📂 Cartera de Proyectos", "⚙️ Librería de Variables"])
    
    with subtabs_pricing[0]:
        col_calc1, col_calc2 = st.columns([1, 1])
        
        with col_calc1:
            st.subheader("1. Definición del Proyecto")
            p_nombre = st.text_input("Nombre del Proyecto / Propuesta")
            p_cliente = st.selectbox("Cliente", ["Nuevo"] + st.session_state['pipeline']['Cliente'].unique().tolist())
            
            st.subheader("2. Estructura de Costos Variables")
            # Selector de variables desde librería
            lib = st.session_state['cost_library']
            add_item = st.selectbox("Agregar Variable desde Librería", lib['Nombre'].tolist())
            
            if 'temp_pricing_items' not in st.session_state:
                st.session_state['temp_pricing_items'] = []

            c_add1, c_add2 = st.columns(2)
            qty = c_add1.number_input("Cantidad", value=1)
            if c_add2.button("Añadir Item"):
                item_data = lib[lib['Nombre'] == add_item].iloc[0]
                st.session_state['temp_pricing_items'].append({
                    'Item': add_item, 'Cantidad': qty, 'Costo_Unit': item_data['Costo_Unitario'],
                    'Subtotal': qty * item_data['Costo_Unitario'], 'Categoria': item_data['Categoria']
                })
            
            # Tabla de items añadidos
            if st.session_state['temp_pricing_items']:
                df_items = pd.DataFrame(st.session_state['temp_pricing_items'])
                st.dataframe(df_items, height=150)
                costo_directo_total = df_items['Subtotal'].sum()
            else:
                costo_directo_total = 0
                st.info("Agregue items de costo para calcular.")

        with col_calc2:
            st.subheader("3. Rentabilidad y Precio")
            st.metric("Costo Directo Total", f"${costo_directo_total:,.0f}")
            
            overhead_pct = st.slider("Overhead / Indirectos (%)", 0, 50, 20)
            costo_full = costo_directo_total * (1 + overhead_pct/100)
            
            margen_target = st.slider("Margen Objetivo (%)", 10, 80, 35)
            precio_venta = costo_full / (1 - margen_target/100) if margen_target < 100 else 0
            
            st.markdown(f"""
            <div style="background-color:#e8f4f8; padding:15px; border-radius:10px; text-align:center;">
                <h3>Precio Sugerido</h3>
                <h1 style="color:#007bff;">${precio_venta:,.0f}</h1>
                <small>Margen Neto: ${(precio_venta - costo_full):,.0f}</small>
            </div>
            """, unsafe_allow_html=True)
            
            horas_est = st.number_input("Horas Estimadas Totales", value=100)
            
            if st.button("💾 Guardar Proyecto en Cartera"):
                new_proj = {
                    'Nombre_Proyecto': p_nombre,
                    'Cliente': p_cliente,
                    'Estado': 'En Evaluación',
                    'Ingresos_Est': precio_venta,
                    'Costos_Directos_Est': costo_directo_total,
                    'Margen_Est': (precio_venta - costo_full)/precio_venta,
                    'Horas_Est': horas_est,
                    'Horas_Reales': 0,
                    'Fecha_Inicio': datetime.now()
                }
                st.session_state['projects_db'] = pd.concat([st.session_state['projects_db'], pd.DataFrame([new_proj])], ignore_index=True)
                st.session_state['temp_pricing_items'] = [] # Reset
                st.success("Proyecto guardado exitosamente.")

    with subtabs_pricing[1]:
        st.subheader("Cartera de Proyectos (Portfolio)")
        df_projs = st.session_state['projects_db']
        if not df_projs.empty:
            # Cálculo de variables visuales
            df_projs['Rentabilidad %'] = (df_projs['Margen_Est'] * 100).map('{:.1f}%'.format)
            
            st.dataframe(
                df_projs[['Nombre_Proyecto', 'Cliente', 'Estado', 'Ingresos_Est', 'Rentabilidad %', 'Horas_Est']],
                use_container_width=True
            )
            
            # Gráfico de burbujas: Rentabilidad vs Ingreso vs Horas
            fig_bubble = px.scatter(df_projs, x="Ingresos_Est", y="Margen_Est", size="Horas_Est", color="Estado",
                                   hover_name="Nombre_Proyecto", title="Mapa de Cartera: Valor vs Rentabilidad vs Esfuerzo")
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("No hay proyectos guardados en la cartera.")

    with subtabs_pricing[2]:
        st.subheader("Gestión de Variables de Pricing")
        edited_lib = st.data_editor(st.session_state['cost_library'], num_rows="dynamic")
        st.session_state['cost_library'] = edited_lib

# ==============================================================================
# MÓDULO 4: PROYECCIONES Y ESCENARIOS (INTEGRACIÓN)
# ==============================================================================
elif menu == "4. Proyecciones & Escenarios":
    st.header("🔮 Simulador de Escenarios Financieros")
    st.markdown("Proyección basada en: **Datos Actuales + Pipeline (Ponderado) + Cartera Pricing**")
    
    col_sc1, col_sc2 = st.columns([1, 3])
    
    with col_sc1:
        st.subheader("Configuración Escenario")
        escenario = st.selectbox("Escenario Base", ["Conservador", "Realista", "Optimista"])
        
        # Factores de ajuste según escenario
        if escenario == "Conservador":
            factor_prob = 0.8
            factor_costo = 1.1
        elif escenario == "Optimista":
            factor_prob = 1.2
            factor_costo = 0.95
        else:
            factor_prob = 1.0
            factor_costo = 1.0
            
        st.markdown("**Proyectos Nuevos a Incluir:**")
        incluir_pipeline = st.checkbox("Incluir Pipeline CRM", value=True)
        incluir_pricing = st.checkbox("Incluir Proyectos Evaluados (Pricing)", value=True)
        
        st.divider()
        st.metric("Capacidad Horas Disp.", st.session_state['config']['capacidad_horas_mensual'])

    with col_sc2:
        # 1. Base Actual (Promedio mensual de ingresos/gastos fijos)
        base_income = 15000000 # Simulado promedio
        base_fixed_cost = 8000000 # Simulado promedio
        
        # 2. Delta Proyectos Nuevos
        delta_ingreso = 0
        delta_costo = 0
        delta_horas = 0
        
        if incluir_pipeline:
            # Sumar valor ponderado del pipeline
            pipe = st.session_state['pipeline']
            delta_ingreso += (pipe['Valor'] * (pipe['Probabilidad']/100) * factor_prob).sum()
            delta_horas += pipe['Horas_Est'].sum()
        
        if incluir_pricing:
            # Sumar proyectos guardados en estado evaluación
            projs = st.session_state['projects_db']
            eval_projs = projs[projs['Estado'] == 'En Evaluación']
            # Asumimos 50% probabilidad por defecto para items de pricing sin CRM
            delta_ingreso += (eval_projs['Ingresos_Est'] * 0.5 * factor_prob).sum()
            delta_costo += (eval_projs['Costos_Directos_Est'] * factor_costo).sum()
            delta_horas += eval_projs['Horas_Est'].sum()
            
        # 3. Resultados Proyectados
        ingreso_proj = base_income + delta_ingreso
        egreso_proj = base_fixed_cost + delta_costo
        utilidad_proj = ingreso_proj - egreso_proj
        
        # Alerta de Capacidad
        horas_totales = 400 + delta_horas # 400 base + nuevos
        capacidad = st.session_state['config']['capacidad_horas_mensual']
        
        if horas_totales > capacidad:
            st.error(f"🚨 INCONSISTENCIA: Las horas requeridas ({horas_totales}) superan la capacidad ({capacidad}). Se requiere contratación o outsourcing.")
        else:
            st.success(f"✅ Capacidad operativa suficiente ({int(horas_totales/capacidad*100)}% ocupación).")
            
        # Comparativa Visual
        st.subheader("Estado de Resultados Proyectado (Mensualizado)")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Ingresos Proyectados", f"${ingreso_proj:,.0f}", delta=f"${delta_ingreso:,.0f} vs Base")
        col_res2.metric("EBITDA Proyectado", f"${utilidad_proj:,.0f}")
        col_res3.metric("Costo de Oportunidad", f"${utilidad_proj * 0.15:,.0f}", help="Retorno extra si invertimos el capital en fondo libre de riesgo")

        # Gráfico Waterfall
        fig_water = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["Base Actual", "Nuevos Negocios (CRM)", "Proyectos Pricing", "Total Proyectado"],
            y = [base_income, 
                 (st.session_state['pipeline']['Valor'] * 0.7).sum() if incluir_pipeline else 0,
                 (eval_projs['Ingresos_Est']*0.5).sum() if incluir_pricing else 0,
                 0], # El total se calcula solo si pongo el ultimo valor, aqui es simplificado
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        # Ajuste manual para el waterfall visual correcto
        fig_water = px.bar(x=["Base", "Impacto CRM", "Impacto Pricing", "Total"], 
                           y=[base_income, delta_ingreso*0.6, delta_ingreso*0.4, ingreso_proj],
                           title="Composición del Crecimiento Proyectado")
        
        st.plotly_chart(fig_water, use_container_width=True)

# ==============================================================================
# MÓDULO 5: TABLERO DE CONTROL (BSC INTEGRADO)
# ==============================================================================
elif menu == "5. Tablero BSC":
    st.header("🚦 Balanced Scorecard Integrado")
    
    # Datos integrados
    ingresos_reales = st.session_state['ledger'][st.session_state['ledger']['Tipo']=='Ingreso']['Monto'].sum()
    meta_ingresos = 60000000 # Meta hardcodeada para ejemplo
    
    pipeline_val = st.session_state['pipeline']['Valor'].sum()
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Perspectiva Financiera")
        st.progress(min(ingresos_reales/meta_ingresos, 1.0))
        st.caption(f"Avance Meta Ingresos: ${ingresos_reales:,.0f} / ${meta_ingresos:,.0f}")
        
    with c2:
        st.subheader("Perspectiva Clientes")
        st.metric("Valor Pipeline Activo", f"${pipeline_val:,.0f}")
        st.metric("Proyectos en Cartera", len(st.session_state['projects_db']))

    st.markdown("---")
    st.info("Este tablero se alimenta automáticamente de los módulos de Operaciones, CRM y Pricing.")
