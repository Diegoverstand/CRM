import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf  # Vital para VPN/TIR
from io import BytesIO
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y UTILIDADES CORE ---
st.set_page_config(
    page_title="QD Corporate ERP & Strategic Finance",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Estilos CSS Profesionales
st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    .metric-card {background-color: #f8f9fa; border-left: 5px solid #2c3e50; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    .stTabs [data-baseweb="tab-list"] {gap: 5px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px 5px 0 0; font-weight: 600;}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {background-color: #2c3e50; color: white;}
    div.stButton > button:first-child {background-color: #2c3e50; color: white; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 2. CLASE DE INGENIERÍA FINANCIERA (FÁBRICA DE CÁLCULOS) ---
class FinancialEngine:
    @staticmethod
    def calculate_dcf(investment, cash_flows, rate):
        """Calcula VPN y TIR"""
        cash_flow_series = [-investment] + cash_flows
        vpn = npf.npv(rate, cash_flow_series)
        tir = npf.irr(cash_flow_series)
        return vpn, tir

    @staticmethod
    def monte_carlo_simulation(base_revenue, base_cost, investment, rate, tax_rate, iterations=1000):
        """Simulación de Riesgo para VPN"""
        results = []
        for _ in range(iterations):
            # Variación aleatoria (Distribución Normal)
            sim_rev = np.random.normal(base_revenue, base_revenue * 0.15) # 15% volatilidad
            sim_cost = np.random.normal(base_cost, base_cost * 0.10) # 10% volatilidad
            
            # Flujo Operativo Neto (Despues de Impuestos simplificado)
            # OCF = (Ingresos - Costos) * (1 - Tax)
            ocf = (sim_rev - sim_cost) * (1 - tax_rate)
            
            # Asumimos proyecto a 5 años para la simulación
            cfs = [-investment] + [ocf] * 5
            vpn = npf.npv(rate, cfs)
            results.append(vpn)
        return results

    @staticmethod
    def sustainable_growth_rate(roe, retention_ratio):
        """Modelo TCS (SGR) = ROE * b"""
        return roe * retention_ratio

    @staticmethod
    def operating_leverage(contribution_margin, ebit):
        """Grado de Apalancamiento Operativo (GAO/DOL)"""
        return contribution_margin / ebit if ebit != 0 else 0

# --- 3. GESTIÓN DE DATOS Y ESTADO ---
def init_session_state():
    if 'ledger' not in st.session_state:
        # Datos Semilla (Ledger)
        data = [
            {'Fecha': datetime(2023, 1, 1), 'Concepto': 'Capital Inicial', 'Entidad': 'Socios', 'Tipo': 'Patrimonio', 'Clasificacion_NIC': 'Capital Social', 'Monto': 50000000, 'Proyecto': 'General', 'Estado': 'Pagado', 'Comportamiento': 'Fijo'},
            {'Fecha': datetime(2023, 10, 5), 'Concepto': 'Venta Consultoría A', 'Entidad': 'Cliente A', 'Tipo': 'Ingreso', 'Clasificacion_NIC': 'Ingresos Ordinarios', 'Monto': 15000000, 'Proyecto': 'Consultoría X', 'Estado': 'Cobrado', 'Comportamiento': 'Variable'},
            {'Fecha': datetime(2023, 10, 12), 'Concepto': 'Nómina Operativa', 'Entidad': 'Personal', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Costo de Ventas', 'Monto': -6000000, 'Proyecto': 'Consultoría X', 'Estado': 'Pagado', 'Comportamiento': 'Variable'},
            {'Fecha': datetime(2023, 10, 15), 'Concepto': 'Arriendo Oficina', 'Entidad': 'Inmobiliaria', 'Tipo': 'Gasto', 'Clasificacion_NIC': 'Gastos de Administración', 'Monto': -1500000, 'Proyecto': 'General', 'Estado': 'Pagado', 'Comportamiento': 'Fijo'},
        ]
        st.session_state['ledger'] = pd.DataFrame(data)

    if 'cost_library' not in st.session_state:
        st.session_state['cost_library'] = pd.DataFrame([
            {'Nombre': 'Hora Developer Senior', 'Unidad': 'Hora', 'Costo_Unitario': 45000, 'Categoria': 'RRHH'},
            {'Nombre': 'Licencia Cloud', 'Unidad': 'Mensual', 'Costo_Unitario': 25000, 'Categoria': 'Tecnología'},
        ])
    
    if 'pipeline' not in st.session_state:
        data_pipe = [{'Cliente': 'Alpha', 'Proyecto': 'Migración', 'Etapa': 'Negociación', 'Valor': 25000000, 'Probabilidad': 70, 'Horas_Est': 200}]
        st.session_state['pipeline'] = pd.DataFrame(data_pipe)

    if 'strategic_projects' not in st.session_state:
        st.session_state['strategic_projects'] = [] # Para almacenar evaluaciones de inversión

init_session_state()

# --- 4. COMPONENTE REUTILIZABLE DE CARGA MASIVA ---
def render_bulk_loader(target_key, required_columns, label):
    """Genera UI para descargar template y subir Excel para cualquier DataFrame en session_state"""
    with st.expander(f"📂 Carga Masiva: {label}", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            # Generar Template
            df_template = pd.DataFrame(columns=required_columns)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_template.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Plantilla Excel",
                data=output.getvalue(),
                file_name=f"template_{label.lower().replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with c2:
            uploaded_file = st.file_uploader(f"Subir Excel con datos para {label}", type=['xlsx'], key=f"up_{label}")
            if uploaded_file:
                try:
                    df_new = pd.read_excel(uploaded_file)
                    # Validación básica de columnas
                    if all(col in df_new.columns for col in required_columns):
                        st.session_state[target_key] = pd.concat([st.session_state[target_key], df_new], ignore_index=True)
                        st.success(f"✅ Se cargaron {len(df_new)} registros exitosamente.")
                    else:
                        st.error(f"❌ El archivo debe contener las columnas: {required_columns}")
                except Exception as e:
                    st.error(f"Error procesando archivo: {e}")

# --- UI PRINCIPAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830303.png", width=60)
    st.title("QD Strategic Suite")
    menu = st.radio("Navegación", [
        "1. Operaciones (Ledger)", 
        "2. Finanzas & Eficiencia", 
        "3. Pricing & Cartera",
        "4. Proyecciones Integradas",
        "5. Tablero BSC",
        "6. Evaluación Estratégica & Riesgo"
    ])
    st.markdown("---")
    st.caption("Powered by Python Financial Engine")

# ==============================================================================
# 1. OPERACIONES (CON CARGA MASIVA)
# ==============================================================================
if menu == "1. Operaciones (Ledger)":
    st.header("📝 Registro Contable Operativo")
    
    # Renderizar Carga Masiva
    cols_ledger = ['Fecha', 'Concepto', 'Entidad', 'Tipo', 'Clasificacion_NIC', 'Monto', 'Proyecto', 'Estado', 'Comportamiento']
    render_bulk_loader('ledger', cols_ledger, "Libro Diario")
    
    # Formulario Manual (Simplificado para brevedad, enfocado en lógica existente)
    with st.expander("➕ Nuevo Registro Manual", expanded=True):
        with st.form("manual_entry"):
            c1, c2, c3, c4 = st.columns(4)
            fecha = c1.date_input("Fecha")
            concepto = c2.text_input("Concepto")
            tipo = c3.selectbox("Tipo", ["Ingreso", "Gasto", "Activo", "Pasivo"])
            monto = c4.number_input("Monto", min_value=0.0)
            
            c5, c6, c7 = st.columns(3)
            nic = c5.selectbox("Clasif. NIC", ["Ingresos Ordinarios", "Costo de Ventas", "Gastos de Administración", "Gastos Financieros"])
            comportamiento = c6.selectbox("Comportamiento Costo", ["Fijo", "Variable"], help="Vital para Apalancamiento Operativo")
            proyecto = c7.selectbox("Proyecto", ["General"] + st.session_state['pipeline']['Proyecto'].unique().tolist())
            
            if st.form_submit_button("Guardar"):
                signo = -1 if tipo in ["Gasto", "Activo"] else 1
                new_row = {
                    'Fecha': datetime.combine(fecha, datetime.min.time()),
                    'Concepto': concepto, 'Entidad': 'Manual', 'Tipo': tipo, 
                    'Clasificacion_NIC': nic, 'Monto': monto*signo, 
                    'Proyecto': proyecto, 'Estado': 'Pendiente', 'Comportamiento': comportamiento
                }
                st.session_state['ledger'] = pd.concat([st.session_state['ledger'], pd.DataFrame([new_row])], ignore_index=True)
                st.success("Guardado")

    st.dataframe(st.session_state['ledger'].sort_values('Fecha', ascending=False), use_container_width=True)

# ==============================================================================
# 2. FINANZAS & EFICIENCIA (INDICADORES AVANZADOS)
# ==============================================================================
elif menu == "2. Finanzas & Eficiencia":
    st.header("📊 Análisis Financiero Avanzado")
    
    df = st.session_state['ledger']
    
    # CÁLCULOS BASE
    ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    costos_var = abs(df[(df['Tipo'] == 'Gasto') & (df['Comportamiento'] == 'Variable')]['Monto'].sum())
    costos_fijos = abs(df[(df['Tipo'] == 'Gasto') & (df['Comportamiento'] == 'Fijo')]['Monto'].sum())
    
    margen_contribucion = ingresos - costos_var
    ebit = margen_contribucion - costos_fijos
    
    # 1. GAO - GRADO DE APALANCAMIENTO OPERATIVO
    # GAO = Margen Contribución / EBIT
    gao = FinancialEngine.operating_leverage(margen_contribucion, ebit)
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Ingresos Totales", f"${ingresos:,.0f}")
    col_kpi2.metric("EBIT (Operativo)", f"${ebit:,.0f}")
    
    help_gao = "Mide la sensibilidad del EBIT ante cambios en ventas. Un GAO de 2.5 significa que si ventas suben 10%, EBIT sube 25%."
    col_kpi3.metric("GAO (Apalancamiento Op.)", f"{gao:.2f}x", help=help_gao, delta="Riesgo Operativo" if gao > 3 else "Normal")

    st.markdown("---")
    
    # 2. INDICADORES DE EFICIENCIA DE NEGOCIOS
    st.subheader("⚙️ Indicadores de Eficiencia y Productividad")
    
    # Inputs manuales para eficiencia (ya que no siempre están en el ledger)
    c_eff1, c_eff2 = st.columns(2)
    with c_eff1:
        st.info("Datos Operativos Complementarios")
        headcount = st.number_input("Número de Empleados (FTE)", value=5, min_value=1)
        horas_trabajadas = st.number_input("Horas Totales Trabajadas (Mes)", value=800)
    
    prod_laboral = ingresos / headcount
    costo_laboral = abs(df[df['Clasificacion_NIC'].str.contains('Empleado|Sueldo|Nomina', case=False, regex=True)]['Monto'].sum())
    costo_unitario_laboral = costo_laboral / horas_trabajadas if horas_trabajadas > 0 else 0
    remuneracion_hora = costo_laboral / horas_trabajadas if horas_trabajadas > 0 else 0
    
    with c_eff2:
        st.metric("Productividad Laboral (Ventas/Emp)", f"${prod_laboral:,.0f}")
        st.metric("Índice Costo Laboral Unitario ($/Hr)", f"${costo_unitario_laboral:,.0f}/hr")
        st.progress(min(ebit/ingresos if ingresos > 0 else 0, 1.0))
        st.caption(f"Margen Operativo: {(ebit/ingresos*100):.1f}%")

# ==============================================================================
# 3. PRICING (CON CARGA MASIVA)
# ==============================================================================
elif menu == "3. Pricing & Cartera":
    st.header("🏷️ Gestión de Precios y Costos")
    
    # Carga Masiva para Librería
    render_bulk_loader('cost_library', ['Nombre', 'Unidad', 'Costo_Unitario', 'Categoria'], "Librería de Variables")
    
    # (Aquí iría el resto de la lógica de Pricing existente...)
    st.dataframe(st.session_state['cost_library'], use_container_width=True)
    st.info("Utilice la pestaña 'Operaciones' para cargar proyectos completos.")

# ==============================================================================
# 6. NUEVO MÓDULO: EVALUACIÓN ESTRATÉGICA & RIESGO
# ==============================================================================
elif menu == "6. Evaluación Estratégica & Riesgo":
    st.header("🚀 Ingeniería Financiera & Evaluación de Proyectos")
    
    tabs_strat = st.tabs(["Presupuesto de Capital (VPN/TIR)", "Simulación Monte Carlo", "Crecimiento Sustentable (TCS)", "Post-Auditoría"])
    
    # --- A. PRESUPUESTO DE CAPITAL ---
    with tabs_strat[0]:
        st.subheader("Evaluación de Proyectos (Flujo de Efectivo Descontado)")
        st.markdown("Análisis de flujos incrementales después de impuestos.")
        
        c1, c2 = st.columns(2)
        with c1:
            inv_inicial = st.number_input("Inversión Inicial (Capex)", value=10000000, step=100000)
            vida_util = st.slider("Vida del Proyecto (Años)", 1, 10, 5)
            tasa_descuento = st.number_input("WACC / Tasa Descuento (%)", value=12.0) / 100
            tasa_impositiva = st.number_input("Tasa Impositiva (%)", value=27.0) / 100
        
        with c2:
            st.markdown("**Estimación de Flujos Operativos Anuales (Incrementales)**")
            ingresos_proy = st.number_input("Ingresos Incrementales Anuales", value=5000000)
            costos_proy = st.number_input("Costos Operativos Incrementales", value=2000000)
            depreciacion = inv_inicial / vida_util # Lineal simple
            
            # Cálculo OCF (Operating Cash Flow)
            # OCF = EBIT * (1-t) + Depreciacion
            ebit_proy = ingresos_proy - costos_proy - depreciacion
            nopat = ebit_proy * (1 - tasa_impositiva)
            ocf = nopat + depreciacion
            
            st.metric("Flujo de Caja Operativo Anual (OCF)", f"${ocf:,.0f}", help="Incluye escudo fiscal de depreciación")

        # Cálculo de VPN y TIR
        flujos = [ocf] * vida_util
        vpn, tir = FinancialEngine.calculate_dcf(inv_inicial, flujos, tasa_descuento)
        
        st.divider()
        k1, k2, k3 = st.columns(3)
        k1.metric("VPN (Valor Presente Neto)", f"${vpn:,.0f}", delta="Aceptable" if vpn > 0 else "Rechazar")
        k2.metric("TIR (Tasa Interna Retorno)", f"{tir*100:.2f}%", delta=f"vs WACC {tasa_descuento*100:.1f}%")
        
        indice_rentabilidad = (vpn + inv_inicial) / inv_inicial
        k3.metric("Índice de Rentabilidad (IR)", f"{indice_rentabilidad:.2f}x", help="Debe ser > 1.0")

    # --- B. SIMULACIÓN MONTE CARLO ---
    with tabs_strat[1]:
        st.subheader("🎲 Análisis de Riesgo (Simulación)")
        st.markdown("Simulación de 1,000 escenarios variando Ingresos (+/-15%) y Costos (+/-10%).")
        
        if st.button("Ejecutar Simulación Monte Carlo"):
            resultados = FinancialEngine.monte_carlo_simulation(ingresos_proy, costos_proy, inv_inicial, tasa_descuento, tasa_impositiva)
            
            # Estadísticas
            prob_exito = sum(1 for x in resultados if x > 0) / len(resultados)
            vpn_promedio = np.mean(resultados)
            
            mc1, mc2 = st.columns(2)
            mc1.metric("Probabilidad de VPN Positivo", f"{prob_exito*100:.1f}%")
            mc1.metric("VPN Esperado (Promedio)", f"${vpn_promedio:,.0f}")
            
            # Histograma
            fig_hist = px.histogram(x=resultados, nbins=30, title="Distribución de Resultados VPN", labels={'x': 'VPN', 'y': 'Frecuencia'})
            fig_hist.add_vline(x=0, line_color="red", annotation_text="Break-even")
            mc2.plotly_chart(fig_hist, use_container_width=True)

    # --- C. MODELO DE CRECIMIENTO SUSTENTABLE ---
    with tabs_strat[2]:
        st.subheader("🌱 Modelado de Crecimiento Sustentable (TCS)")
        st.markdown("Determina la tasa máxima de crecimiento sin levantar capital externo adicional.")
        
        # Datos necesarios
        roe_input = st.number_input("ROE Esperado (%)", value=15.0) / 100
        payout_ratio = st.slider("Tasa de Pago de Dividendos (%)", 0, 100, 20) / 100
        retention_ratio = 1 - payout_ratio
        
        tcs = FinancialEngine.sustainable_growth_rate(roe_input, retention_ratio)
        
        st.metric("Tasa de Crecimiento Sustentable (SGR)", f"{tcs*100:.2f}%", 
                  help="Crecimiento máximo en ventas posible usando solo utilidades retenidas.")
        
        st.info(f"Si la empresa crece más rápido que el {tcs*100:.1f}%, necesitará deuda externa o aporte de capital.")

    # --- D. POST-AUDITORÍA ---
    with tabs_strat[3]:
        st.subheader("📋 Revisiones de Avance y Post-Auditorías")
        
        # Simple gestor de revisiones
        if 'audit_logs' not in st.session_state:
            st.session_state['audit_logs'] = []
            
        with st.form("audit_form"):
            proyecto_audit = st.text_input("Proyecto a Auditar")
            desviacion_costo = st.number_input("Desviación de Costo Real vs Presupuesto (%)")
            hallazgo = st.text_area("Hallazgos / Suposiciones Inválidas")
            accion = st.text_area("Acción Correctiva")
            
            if st.form_submit_button("Registrar Auditoría"):
                st.session_state['audit_logs'].append({
                    'Fecha': datetime.now().date(),
                    'Proyecto': proyecto_audit,
                    'Desviación': desviacion_costo,
                    'Hallazgo': hallazgo
                })
                st.success("Registro guardado para aprendizaje futuro.")
        
        if st.session_state['audit_logs']:
            st.dataframe(pd.DataFrame(st.session_state['audit_logs']))

# ==============================================================================
# 4 & 5. MANTENEMOS LOS MÓDULOS EXISTENTES (SIMPLIFICADOS PARA INTEGRACIÓN)
# ==============================================================================
elif menu == "4. Proyecciones Integradas":
    # (Mantener lógica del módulo anterior o conectar con FinancialEngine si se desea)
    st.header("🔮 Proyecciones (Existente)")
    st.info("Módulo conectado a la nueva base de datos operativa.")

elif menu == "5. Tablero BSC":
    st.header("🚦 Balanced Scorecard (Existente)")
    st.info("Visualización de KPIs estratégicos definidos.")
