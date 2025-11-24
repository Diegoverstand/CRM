import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf
from io import BytesIO
from datetime import datetime, date

# --- 1. CONFIGURACIÓN GLOBAL ---
st.set_page_config(
    page_title="QD Sistema Integral (CRM + ERP + Estrategia)",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 5px;}
    .stTabs [data-baseweb="tab"] {height: 50px; background-color: #f0f2f6; font-weight: 600; border-radius: 5px 5px 0 0;}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {background-color: #2c3e50; color: white;}
    .metric-card {border: 1px solid #e0e0e0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE NEGOCIO (CLASES Y FUNCIONES) ---

class FinancialEngine:
    @staticmethod
    def calculate_dcf(investment, cash_flows, rate):
        cash_flow_series = [-investment] + cash_flows
        vpn = npf.npv(rate, cash_flow_series)
        tir = npf.irr(cash_flow_series)
        return vpn, tir

    @staticmethod
    def monte_carlo_simulation(base_revenue, base_cost, investment, rate, tax_rate, iterations=1000):
        results = []
        for _ in range(iterations):
            sim_rev = np.random.normal(base_revenue, base_revenue * 0.15)
            sim_cost = np.random.normal(base_cost, base_cost * 0.10)
            ocf = (sim_rev - sim_cost) * (1 - tax_rate)
            cfs = [-investment] + [ocf] * 5
            vpn = npf.npv(rate, cfs)
            results.append(vpn)
        return results

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
            'banco': 'Gastos Financieros', 'interés': 'Gastos Financieros'
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
        ]
        st.session_state['ledger'] = pd.DataFrame(data)
    
    # PARCHE: Asegurar que exista columna 'Comportamiento' si vienen datos viejos
    if 'Comportamiento' not in st.session_state['ledger'].columns:
        st.session_state['ledger']['Comportamiento'] = 'Fijo'

    # B. PIPELINE CRM
    if 'pipeline' not in st.session_state:
        data_pipe = [
            {'Cliente': 'Alpha', 'Proyecto': 'Migración Cloud', 'Etapa': 'Negociación', 'Valor': 25000000, 'Probabilidad': 70, 'Fecha_Cierre': date(2023, 12, 15), 'Horas_Est': 200},
            {'Cliente': 'Beta', 'Proyecto': 'Auditoría', 'Etapa': 'Propuesta', 'Valor': 8000000, 'Probabilidad': 40, 'Fecha_Cierre': date(2024, 1, 20), 'Horas_Est': 80},
            {'Cliente': 'Gamma', 'Proyecto': 'Outsourcing', 'Etapa': 'Lead', 'Valor': 5000000, 'Probabilidad': 10, 'Fecha_Cierre': date(2024, 2, 10), 'Horas_Est': 50},
        ]
        st.session_state['pipeline'] = pd.DataFrame(data_pipe)

    # C. LIBRERÍA DE COSTOS
    if 'cost_library' not in st.session_state:
        st.session_state['cost_library'] = pd.DataFrame([
            {'Nombre': 'Hora Developer Senior', 'Unidad': 'Hora', 'Costo_Unitario': 45000, 'Categoria': 'RRHH'},
            {'Nombre': 'Licencia Cloud', 'Unidad': 'Mensual', 'Costo_Unitario': 25000, 'Categoria': 'Tecnología'},
        ])

    # D. CARTERA DE PROYECTOS (PRICING GUARDADO)
    if 'projects_db' not in st.session_state:
        st.session_state['projects_db'] = pd.DataFrame(columns=[
            'Nombre_Proyecto', 'Cliente', 'Estado', 'Ingresos_Est', 'Costos_Directos_Est', 'Margen_Est', 'Horas_Est'
        ])

    # E. VARIABLES GLOBALES
    if 'config' not in st.session_state:
        st.session_state['config'] = {'capacidad_horas': 600}

init_session_state()

# --- 4. COMPONENTE DE CARGA MASIVA ---
def render_bulk_loader(target_key, cols, title):
    with st.expander(f"📂 Carga Masiva: {title}", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            df_t = pd.DataFrame(columns=cols)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_t.to_excel(writer, index=False)
            st.download_button(f"📥 Bajar Plantilla {title}", output.getvalue(), f"template_{title}.xlsx")
        with c2:
            up = st.file_uploader(f"Subir Excel {title}", type=['xlsx'], key=f"up_{title}")
            if up:
                try:
                    df_new = pd.read_excel(up)
                    # Forzar columnas si faltan
                    for col in cols:
                        if col not in df_new.columns:
                            df_new[col] = 0 if 'Monto' in col else ''
                    st.session_state[target_key] = pd.concat([st.session_state[target_key], df_new], ignore_index=True)
                    st.success("Carga exitosa")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 5. INTERFAZ PRINCIPAL (SIDEBAR) ---
with st.sidebar:
    st.title("QD Sistema Integral")
    menu = st.radio("Navegación", [
        "1. CRM & Pipeline",           # RECUPERADO
        "2. Operaciones (Libro Diario)",
        "3. Finanzas (Estados Fin.)",
        "4. Pricing & Cartera",        # RECUPERADO
        "5. Proyecciones",
        "6. Estrategia & Riesgo",
        "7. Balanced Scorecard"
    ])
    st.divider()
    st.info("Sistema unificado V4.0")

# =============================================================================
# MÓDULO 1: CRM & PIPELINE (RECUPERADO)
# =============================================================================
if menu == "1. CRM & Pipeline":
    st.header("🚀 Gestión Comercial")
    
    # 1. Pipeline Visual
    tabs_crm = st.tabs(["Pipeline Visual", "Gestión de Datos"])
    
    with tabs_crm[0]:
        df_pipe = st.session_state['pipeline']
        
        # KPIs
        total_pipe = df_pipe['Valor'].sum()
        weighted_pipe = (df_pipe['Valor'] * df_pipe['Probabilidad']/100).sum()
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Total en Pipeline", f"${total_pipe:,.0f}")
        k2.metric("Forecast Ponderado", f"${weighted_pipe:,.0f}")
        k3.metric("Oportunidades", len(df_pipe))
        
        # Funnel Chart
        funnel_df = df_pipe.groupby('Etapa')['Valor'].sum().reset_index()
        # Orden forzado
        orden = ["Lead", "Propuesta", "Negociación", "Ganado", "Perdido"]
        funnel_df['Etapa'] = pd.Categorical(funnel_df['Etapa'], categories=orden, ordered=True)
        funnel_df = funnel_df.sort_values('Etapa')
        
        fig_funnel = px.funnel(funnel_df, x='Valor', y='Etapa', title="Embudo de Ventas")
        st.plotly_chart(fig_funnel, use_container_width=True)

    with tabs_crm[1]:
        st.subheader("Base de Datos Pipeline")
        render_bulk_loader('pipeline', ['Cliente', 'Proyecto', 'Etapa', 'Valor', 'Probabilidad', 'Fecha_Cierre', 'Horas_Est'], "Pipeline")
        
        edited_pipe = st.data_editor(st.session_state['pipeline'], num_rows="dynamic")
        st.session_state['pipeline'] = edited_pipe

# =============================================================================
# MÓDULO 2: OPERACIONES (HÍBRIDO: MANUAL + MASIVO)
# =============================================================================
elif menu == "2. Operaciones (Libro Diario)":
    st.header("📝 Operaciones & Gastos")
    
    tab_ops1, tab_ops2 = st.tabs(["Registro Manual Detallado", "Libro Diario & Carga Masiva"])
    
    with tab_ops1:
        st.subheader("Nuevo Movimiento (Asistente IFRS)")
        with st.form("manual_entry_detailed", clear_on_submit=True):
            c1, c2 = st.columns(2)
            fecha = c1.date_input("Fecha")
            concepto = c2.text_input("Concepto / Glosa")
            
            # Lógica Auto-Clasificación
            sugerencia = FinancialEngine.classify_expense_auto(concepto) if concepto else "Otros Gastos"
            
            entidad = c1.text_input("Entidad")
            tipo = c2.selectbox("Tipo", ["Gasto", "Ingreso", "Activo", "Pasivo", "Patrimonio"])
            
            opciones_nic = [
                "Ingresos Ordinarios", "Costo de Ventas", "Gastos de Administración", 
                "Gastos de Ventas", "Beneficios a Empleados", "Gastos Financieros",
                "Propiedad, Planta y Equipo", "Efectivo y Equivalentes"
            ]
            
            idx_nic = opciones_nic.index(sugerencia) if sugerencia in opciones_nic else 0
            clasif_nic = c1.selectbox("Clasificación NIC", opciones_nic, index=idx_nic)
            
            comportamiento = c2.selectbox("Comportamiento", ["Fijo", "Variable"])
            monto = c1.number_input("Monto", min_value=0.0)
            
            # Proyecto vinculado al CRM
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
        
        st.markdown("### Histórico de Movimientos")
        st.dataframe(st.session_state['ledger'].sort_values('Fecha', ascending=False), use_container_width=True)

# =============================================================================
# MÓDULO 3: FINANZAS (COMPLETO)
# =============================================================================
elif menu == "3. Finanzas (Estados Fin.)":
    st.header("📊 Estados Financieros")
    
    df = st.session_state['ledger'].copy()
    # Convertir a datetime para agrupación
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Periodo'] = df['Fecha'].dt.to_period('M').astype(str)
    
    tabs_fin = st.tabs(["Estado de Resultados", "Balance General", "Flujo de Caja", "Indicadores"])
    
    with tabs_fin[0]:
        st.subheader("Estado de Resultados (P&L)")
        df_pnl = df[df['Tipo'].isin(['Ingreso', 'Gasto'])]
        pivot_pnl = df_pnl.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum', fill_value=0)
        
        # Color simple sin matplotlib para evitar errores
        st.dataframe(pivot_pnl.style.format("${:,.0f}"), use_container_width=True)
        
        # Gráfico Utilidad Neta
        utilidad = df_pnl.groupby('Periodo')['Monto'].sum()
        st.plotly_chart(px.bar(x=utilidad.index, y=utilidad.values, title="Utilidad Neta por Mes"), use_container_width=True)

    with tabs_fin[1]:
        st.subheader("Balance General")
        df_bal = df[df['Tipo'].isin(['Activo', 'Pasivo', 'Patrimonio'])]
        pivot_bal = df_bal.pivot_table(index='Clasificacion_NIC', columns='Periodo', values='Monto', aggfunc='sum').cumsum(axis=1).fillna(0)
        st.dataframe(pivot_bal.style.format("${:,.0f}"), use_container_width=True)

    with tabs_fin[2]:
        st.subheader("Flujo de Caja (Directo)")
        df_cash = df[df['Estado'].isin(['Pagado', 'Cobrado', 'Pagado/Cobrado'])]
        cash_flow = df_cash.groupby('Periodo')['Monto'].sum()
        
        fig_cf = go.Figure(go.Waterfall(
            x = cash_flow.index, y = cash_flow.values,
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        st.plotly_chart(fig_cf, use_container_width=True)

    with tabs_fin[3]:
        st.subheader("KPIs Financieros")
        ingresos = df[df['Tipo']=='Ingreso']['Monto'].sum()
        costos_var = abs(df[(df['Tipo']=='Gasto')&(df['Comportamiento']=='Variable')]['Monto'].sum())
        costos_fijo = abs(df[(df['Tipo']=='Gasto')&(df['Comportamiento']=='Fijo')]['Monto'].sum())
        
        margen_cont = ingresos - costos_var
        ebit = margen_cont - costos_fijo
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Margen Bruto", f"${margen_cont:,.0f}")
        c2.metric("EBIT (Operativo)", f"${ebit:,.0f}")
        
        gao = margen_cont / ebit if ebit != 0 else 0
        c3.metric("GAO (Apalancamiento)", f"{gao:.2f}x", help="Sensibilidad de utilidad ante cambios en ventas")

# =============================================================================
# MÓDULO 4: PRICING & CARTERA (RECUPERADO)
# =============================================================================
elif menu == "4. Pricing & Cartera":
    st.header("🏷️ Pricing & Proyectos")
    
    tabs_price = st.tabs(["Calculadora", "Cartera de Proyectos", "Librería Costos"])
    
    with tabs_price[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Configurar Proyecto")
            p_nom = st.text_input("Nombre Proyecto")
            lib = st.session_state['cost_library']
            item = st.selectbox("Agregar Item", lib['Nombre'].tolist())
            qty = st.number_input("Cantidad", 1)
            
            if 'temp_items' not in st.session_state: st.session_state['temp_items'] = []
            if st.button("Añadir"):
                row = lib[lib['Nombre']==item].iloc[0]
                st.session_state['temp_items'].append({'Item': item, 'Costo': row['Costo_Unitario']*qty})
            
            # Mostrar items
            st.dataframe(pd.DataFrame(st.session_state['temp_items']))
            
        with c2:
            st.subheader("Resultado")
            costo_dir = sum([x['Costo'] for x in st.session_state['temp_items']])
            st.metric("Costo Directo", f"${costo_dir:,.0f}")
            
            overhead = st.slider("Overhead %", 0, 50, 20)
            margen = st.slider("Margen %", 10, 80, 30)
            
            precio = (costo_dir * (1 + overhead/100)) / (1 - margen/100) if margen < 100 else 0
            st.metric("Precio Sugerido", f"${precio:,.0f}")
            
            if st.button("Guardar en Cartera"):
                new_p = {'Nombre_Proyecto': p_nom, 'Estado': 'Evaluación', 'Ingresos_Est': precio, 'Margen_Est': margen/100, 'Horas_Est': 100}
                st.session_state['projects_db'] = pd.concat([st.session_state['projects_db'], pd.DataFrame([new_p])], ignore_index=True)
                st.success("Guardado")
                st.session_state['temp_items'] = []

    with tabs_price[1]:
        st.subheader("Mapa de Cartera")
        df_p = st.session_state['projects_db']
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True)
            fig_bub = px.scatter(df_p, x="Ingresos_Est", y="Margen_Est", size="Horas_Est", color="Estado", title="Valor vs Rentabilidad")
            st.plotly_chart(fig_bub, use_container_width=True)
        else:
            st.info("No hay proyectos guardados.")

    with tabs_price[2]:
        render_bulk_loader('cost_library', ['Nombre', 'Unidad', 'Costo_Unitario', 'Categoria'], "Costos")
        st.data_editor(st.session_state['cost_library'], num_rows="dynamic")

# =============================================================================
# MÓDULO 5: PROYECCIONES
# =============================================================================
elif menu == "5. Proyecciones":
    st.header("🔮 Escenarios Futuros")
    
    col1, col2 = st.columns([1,3])
    with col1:
        escenario = st.selectbox("Escenario", ["Base", "Optimista", "Pesimista"])
        factor = 1.2 if escenario == "Optimista" else (0.8 if escenario == "Pesimista" else 1.0)
        inc_crm = st.checkbox("Incluir CRM", True)
        inc_pric = st.checkbox("Incluir Pricing", True)

    with col2:
        # Datos Base
        base_ingresos = 10000000 # Promedio mensual simulado
        
        # Delta CRM
        pipe = st.session_state['pipeline']
        val_crm = (pipe['Valor'] * (pipe['Probabilidad']/100)).sum() * factor if inc_crm else 0
        
        # Delta Pricing
        projs = st.session_state['projects_db']
        val_pric = projs['Ingresos_Est'].sum() * 0.5 * factor if inc_pric and not projs.empty else 0
        
        total = base_ingresos + val_crm + val_pric
        
        st.metric("Ingresos Proyectados (Mes)", f"${total:,.0f}", delta=f"${total-base_ingresos:,.0f} vs Base")
        
        fig_w = go.Figure(go.Waterfall(
            x = ["Base", "CRM Ponderado", "Nuevos Proyectos", "Total"],
            y = [base_ingresos, val_crm, val_pric, 0],
            measure = ["relative", "relative", "relative", "total"]
        ))
        st.plotly_chart(fig_w, use_container_width=True)

# =============================================================================
# MÓDULO 6: ESTRATEGIA (NUEVO)
# =============================================================================
elif menu == "6. Estrategia & Riesgo":
    st.header("♟️ Ingeniería Financiera")
    
    tabs_strat = st.tabs(["Evaluación Proyectos (VPN)", "Simulación Riesgo", "Crecimiento Sustentable"])
    
    with tabs_strat[0]:
        c1, c2 = st.columns(2)
        inv = c1.number_input("Inversión Inicial", 10000000)
        flujo = c2.number_input("Flujo Anual Est.", 3000000)
        tasa = c1.number_input("Tasa Descuento %", 10.0) / 100
        years = c2.slider("Años", 1, 10, 5)
        
        vpn, tir = FinancialEngine.calculate_dcf(inv, [flujo]*years, tasa)
        st.metric("VPN", f"${vpn:,.0f}")
        st.metric("TIR", f"{tir*100:.2f}%")

    with tabs_strat[1]:
        if st.button("Correr Monte Carlo"):
            res = FinancialEngine.monte_carlo_simulation(flujo, flujo*0.5, inv, tasa, 0.27)
            fig_hist = px.histogram(x=res, title="Distribución de Resultados VPN")
            st.plotly_chart(fig_hist, use_container_width=True)

    with tabs_strat[2]:
        roe = st.number_input("ROE %", 15.0)/100
        retencion = 1 - (st.slider("Dividendos %", 0, 100, 20)/100)
        sgr = roe * retencion
        st.metric("Crecimiento Sustentable Máximo", f"{sgr*100:.1f}%")

# =============================================================================
# MÓDULO 7: BSC
# =============================================================================
elif menu == "7. Balanced Scorecard":
    st.header("🚦 Cuadro de Mando Integral")
    
    # Financiera (Auto)
    ing_real = st.session_state['ledger'][st.session_state['ledger']['Tipo']=='Ingreso']['Monto'].sum()
    meta = 50000000
    st.subheader("1. Financiera")
    st.progress(min(ing_real/meta, 1.0))
    st.caption(f"Ingresos: ${ing_real:,.0f} / ${meta:,.0f}")
    
    # Clientes (Auto)
    st.subheader("2. Clientes")
    pipe_val = st.session_state['pipeline']['Valor'].sum()
    st.metric("Valor Pipeline", f"${pipe_val:,.0f}")
    
    # Procesos (Manual)
    st.subheader("3. Procesos Internos")
    eff = st.slider("Eficiencia Operativa", 0, 100, 80)
    st.progress(eff/100)
    
    # Aprendizaje (Manual)
    st.subheader("4. Aprendizaje")
    clima = st.select_slider("Clima Laboral", ["Malo", "Regular", "Bueno", "Excelente"], value="Bueno")
    st.write(f"Estado: {clima}")
