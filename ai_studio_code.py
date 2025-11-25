import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf
from io import BytesIO
from datetime import datetime, date, timedelta

# --- 1. CONFIGURACIÓN GLOBAL & DISEÑO PROFESIONAL ---
st.set_page_config(
    page_title="QD Corporate System",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# CSS PROFESIONAL Y CORRECCIÓN DE ERRORES VISUALES
st.markdown("""
<style>
    /* Importar fuente Inter para look moderno */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fondo General y Contenedores */
    .stApp {
        background-color: #0f172a; /* Slate 900 */
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* CORRECCIÓN DE TARJETAS MÉTRICAS (BLANK WINDOWS FIX) */
    div[data-testid="stMetric"] {
        background-color: #1e293b; /* Slate 800 - Fondo Oscuro */
        border: 1px solid #334155; /* Borde sutil */
        padding: 15px;
        border-radius: 8px;
        color: #f8fafc; /* Texto blanco */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    div[data-testid="stMetric"]:hover {
        border-color: #6366f1; /* Indigo hover */
        transform: translateY(-2px);
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important; /* Texto gris claro para etiquetas */
        font-size: 0.9rem;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff !important; /* Texto blanco puro para valores */
        font-weight: 700;
    }

    /* Tabs Estilizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #334155;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        font-size: 14px;
        font-weight: 500;
        color: #cbd5e1;
        border-radius: 6px;
        border: 1px solid transparent;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #1e293b;
        color: white;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #3b82f6; /* Blue 500 */
        color: white;
        border: none;
    }

    /* Inputs y Selectbox */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1e293b;
        color: white;
        border-color: #475569;
    }
    
    /* Botones */
    div.stButton > button:first-child {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    div.stButton > button:first-child:hover {
        background-color: #1d4ed8;
    }

    /* Tablas */
    [data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 8px;
    }

    h1, h2, h3 {
        color: #f8fafc;
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

    # D. CARTERA DE PROYECTOS (ESTRUCTURA ACTUALIZADA PARA ITEMS)
    if 'projects_db' not in st.session_state:
        # Se agrega columna 'Items' para guardar el detalle de costos
        st.session_state['projects_db'] = pd.DataFrame(columns=[
            'Nombre_Proyecto', 'Cliente', 'Estado', 'Ingresos_Est', 'Costos_Directos_Est', 'Margen_Est', 'Horas_Est', 'Items'
        ])
    
    # Asegurar que exista la columna Items si vienen datos viejos
    if 'Items' not in st.session_state['projects_db'].columns:
        st.session_state['projects_db']['Items'] = None

    # E. VARIABLES DE MARKETING
    if 'marketing_spend' not in st.session_state:
        st.session_state['marketing_spend'] = 1000000

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
    st.caption("v6.0 Professional Edition")
    
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
# MÓDULO 2: PRICING & CARTERA (MEJORADO: EDICIÓN + ACTUALIZACIÓN)
# =============================================================================
elif menu == "2. Pricing & Cartera":
    st.header("🏷️ Pricing & Gestión de Proyectos")
    
    tabs_price = st.tabs(["Calculadora de Precios", "Cartera de Proyectos", "Librería Costos"])
    
    # --- TAB 1: CALCULADORA (CON MODO EDICIÓN) ---
    with tabs_price[0]:
        # Selector de Modo
        col_mode, _ = st.columns([1, 2])
        mode = col_mode.radio("Modo de Trabajo", ["Crear Nuevo Proyecto", "Editar Proyecto Existente"], horizontal=True)
        
        project_to_edit = None
        default_items = []
        default_name = ""
        default_client = "Nuevo"
        default_hours = 100
        default_overhead = 20
        default_margin = 30
        
        # Lógica de Carga para Edición
        if mode == "Editar Proyecto Existente":
            df_projs = st.session_state['projects_db']
            if not df_projs.empty:
                selected_proj_name = st.selectbox("Seleccionar Proyecto a Editar", df_projs['Nombre_Proyecto'].unique())
                # Obtener datos del proyecto
                proj_data = df_projs[df_projs['Nombre_Proyecto'] == selected_proj_name].iloc[0]
                
                default_name = proj_data['Nombre_Proyecto']
                default_client = proj_data['Cliente']
                default_hours = int(proj_data['Horas_Est'])
                # Intentar recuperar items guardados
                if isinstance(proj_data['Items'], list):
                    default_items = proj_data['Items']
                # Recuperar margen y overhead aproximado si no se guardaron explícitamente (simplificación)
                default_margin = int(proj_data['Margen_Est'] * 100)
            else:
                st.warning("No hay proyectos para editar.")

        # Inicializar items temporales
        if 'temp_items' not in st.session_state:
            st.session_state['temp_items'] = []
            
        # Si cambiamos a modo editar y cargamos un proyecto, sobreescribir temp_items SOLO UNA VEZ al cargar
        # Para simplificar, usamos un botón de "Cargar Datos" si es edición, o limpiamos si es nuevo
        if mode == "Crear Nuevo Proyecto":
             if st.button("Limpiar Formulario", type="secondary"):
                 st.session_state['temp_items'] = []
        elif mode == "Editar Proyecto Existente" and project_to_edit is None:
             # Logic handled by selectbox above, but we need to push to session state
             pass

        # Si hay items default cargados del modo edición y la lista temp está vacía, llenarla
        if mode == "Editar Proyecto Existente" and default_items and not st.session_state['temp_items']:
             st.session_state['temp_items'] = default_items

        c1, c2 = st.columns([1, 1])
        with c1:
            with st.container(border=True):
                st.subheader("1. Configuración")
                p_nom = st.text_input("Nombre Proyecto", value=default_name)
                
                # Lista clientes dinámica
                lista_clientes = ["Nuevo"]
                if 'pipeline' in st.session_state and 'Cliente' in st.session_state['pipeline'].columns:
                    lista_clientes += st.session_state['pipeline']['Cliente'].unique().tolist()
                
                idx_cli = lista_clientes.index(default_client) if default_client in lista_clientes else 0
                cliente_p = st.selectbox("Cliente", lista_clientes, index=idx_cli)
                
                # Selector de recursos (Lee DIRECTO de la sesión para actualizarse)
                lib = st.session_state['cost_library']
                item_options = lib['Nombre'].tolist() if not lib.empty else ["Sin recursos"]
                item = st.selectbox("Agregar Recurso", item_options)
                
                qty = st.number_input("Cantidad", 1.0, step=0.5)
                
                if st.button("➕ Añadir Item"):
                    if not lib.empty:
                        row = lib[lib['Nombre']==item].iloc[0]
                        st.session_state['temp_items'].append({
                            'Item': item, 
                            'Costo_Unit': float(row['Costo_Unitario']),
                            'Cantidad': qty,
                            'Costo_Total': float(row['Costo_Unitario']) * qty
                        })
                    else:
                        st.error("Librería vacía")
                
                # Mostrar items actuales
                if st.session_state['temp_items']:
                    st.dataframe(pd.DataFrame(st.session_state['temp_items']), height=150, use_container_width=True)
                    if st.button("Limpiar Items"):
                        st.session_state['temp_items'] = []

        with c2:
            with st.container(border=True):
                st.subheader("2. Rentabilidad")
                
                # Cálculos
                items = st.session_state['temp_items']
                costo_dir = sum([x['Costo_Total'] for x in items])
                
                # Visualización de tarjeta oscura corregida por CSS global
                st.metric("Costo Directo Total", f"${costo_dir:,.0f}")
                
                overhead = st.slider("Overhead / Indirectos %", 0, 50, default_overhead)
                margen = st.slider("Margen Objetivo %", 10, 80, default_margin)
                
                costo_full = costo_dir * (1 + overhead/100)
                precio = costo_full / (1 - margen/100) if margen < 100 else 0
                margen_neto_val = precio - costo_full
                
                st.metric("Precio Venta Sugerido", f"${precio:,.0f}")
                st.metric("Margen Neto Estimado", f"${margen_neto_val:,.0f}", delta=f"{margen}% Rentabilidad")
                
                horas_est = st.number_input("Horas Totales Estimadas", value=default_hours)
                
                btn_label = "💾 Actualizar Proyecto" if mode == "Editar Proyecto Existente" else "💾 Guardar Proyecto"
                
                if st.button(btn_label, type="primary"):
                    new_p = {
                        'Nombre_Proyecto': p_nom, 
                        'Cliente': cliente_p,
                        'Estado': 'Evaluación', 
                        'Ingresos_Est': precio, 
                        'Costos_Directos_Est': costo_dir,
                        'Margen_Est': margen/100, 
                        'Horas_Est': horas_est,
                        'Items': items # Guardamos el detalle
                    }
                    
                    df_current = st.session_state['projects_db']
                    
                    if mode == "Editar Proyecto Existente":
                        # Eliminar el anterior y poner el nuevo (Update simple)
                        df_current = df_current[df_current['Nombre_Proyecto'] != p_nom]
                        df_updated = pd.concat([df_current, pd.DataFrame([new_p])], ignore_index=True)
                        st.session_state['projects_db'] = df_updated
                        st.success(f"Proyecto '{p_nom}' actualizado exitosamente.")
                    else:
                        st.session_state['projects_db'] = pd.concat([df_current, pd.DataFrame([new_p])], ignore_index=True)
                        st.success(f"Proyecto '{p_nom}' creado exitosamente.")
                    
                    st.session_state['temp_items'] = [] # Limpiar tras guardar

    # --- TAB 2: CARTERA ---
    with tabs_price[1]:
        st.subheader("Cartera de Proyectos")
        df_p = st.session_state['projects_db']
        
        if not df_p.empty:
            # Sanitización de datos
            cols_numericas = ['Ingresos_Est', 'Margen_Est', 'Horas_Est']
            for col in cols_numericas:
                if col in df_p.columns:
                    df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0)
            
            df_p['Size_Plot'] = df_p['Horas_Est'].apply(lambda x: max(float(x), 1.0))
            
            st.dataframe(df_p.drop(columns=['Size_Plot', 'Items'], errors='ignore'), use_container_width=True)
            
            try:
                fig_bub = px.scatter(
                    df_p, x="Ingresos_Est", y="Margen_Est", size="Size_Plot", 
                    color="Estado", title="Mapa de Valor vs Rentabilidad",
                    hover_data=['Nombre_Proyecto', 'Horas_Est'],
                    labels={'Size_Plot': 'Esfuerzo'}
                )
                fig_bub.update_layout(template="plotly_dark") # Tema oscuro para gráfico
                st.plotly_chart(fig_bub, use_container_width=True)
            except Exception:
                st.warning("Datos insuficientes para graficar.")
        else:
            st.info("No hay proyectos guardados.")

    # --- TAB 3: LIBRERÍA ---
    with tabs_price[2]:
        st.subheader("Base de Costos y Recursos")
        render_bulk_loader('cost_library', ['Nombre', 'Unidad', 'Costo_Unitario', 'Categoria'], "Librería")
        
        # Edición en vivo
        edited_lib = st.data_editor(st.session_state['cost_library'], num_rows="dynamic", use_container_width=True)
        # Actualizar sesión inmediatamente al editar
        if not edited_lib.equals(st.session_state['cost_library']):
            st.session_state['cost_library'] = edited_lib
            st.rerun() # Forzar recarga para que el dropdown de la Tab 1 se actualice

# =============================================================================
# MÓDULO 3: CRM & PIPELINE
# =============================================================================
elif menu == "3. CRM & Pipeline":
    st.header("🚀 CRM & Inteligencia de Ventas")
    
    tabs_crm = st.tabs(["KPIs Ventas & CAC", "Pipeline Visual", "Gestión Datos"])
    df_pipe = st.session_state['pipeline']
    
    with tabs_crm[0]:
        st.subheader("Indicadores de Eficiencia Comercial")
        with st.expander("Configuración Métricas", expanded=False):
            marketing_spend = st.number_input("Gasto Marketing Mensual", value=st.session_state['marketing_spend'])
            avg_lifespan = st.number_input("Vida Promedio Cliente (Meses)", value=12)
        
        ganados = df_pipe[df_pipe['Etapa'] == 'Ganado']
        cerrados = df_pipe[df_pipe['Etapa'].isin(['Ganado', 'Perdido'])]
        nuevos_clientes = len(ganados)
        conversion_rate = (len(ganados) / len(cerrados) * 100) if len(cerrados) > 0 else 0
        cac = marketing_spend / nuevos_clientes if nuevos_clientes > 0 else 0
        ticket_promedio = ganados['Valor'].mean() if nuevos_clientes > 0 else 0
        clv = ticket_promedio * avg_lifespan
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tasa Conversión", f"{conversion_rate:.1f}%")
        k2.metric("CAC", f"${cac:,.0f}")
        k3.metric("Ticket Promedio", f"${ticket_promedio:,.0f}")
        k4.metric("CLV Estimado", f"${clv:,.0f}")

    with tabs_crm[1]:
        funnel_df = df_pipe.groupby('Etapa')['Valor'].sum().reset_index()
        orden = ["Lead", "Propuesta", "Negociación", "Ganado", "Perdido"]
        funnel_df['Etapa'] = pd.Categorical(funnel_df['Etapa'], categories=orden, ordered=True)
        funnel_df = funnel_df.sort_values('Etapa')
        
        fig_funnel = px.funnel(funnel_df, x='Valor', y='Etapa', title="Embudo de Ventas")
        fig_funnel.update_layout(template="plotly_dark")
        st.plotly_chart(fig_funnel, use_container_width=True)

    with tabs_crm[2]:
        render_bulk_loader('pipeline', ['Cliente', 'Proyecto', 'Etapa', 'Valor', 'Probabilidad', 'Fecha_Cierre', 'Horas_Est'], "Pipeline")
        st.data_editor(st.session_state['pipeline'], num_rows="dynamic", use_container_width=True)

# =============================================================================
# MÓDULO 4: FINANZAS (EEFF)
# =============================================================================
elif menu == "4. Finanzas (EEFF)":
    st.header("📊 Estados Financieros")
    
    df = st.session_state['ledger'].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Periodo'] = df['Fecha'].dt.to_period('M').astype(str)
    
    tabs_fin = st.tabs(["Indicadores Clave", "Estado de Resultados", "Balance General", "Flujo de Caja"])
    
    with tabs_fin[0]:
        st.subheader("KPIs Financieros Corporativos")
        
        activos_cte = df[(df['Tipo']=='Activo') & (df['Clasificacion_NIC'].isin(['Efectivo y Equivalentes', 'Cuentas por Cobrar']))]['Monto'].sum()
        pasivos_cte = abs(df[(df['Tipo']=='Pasivo') & (df['Clasificacion_NIC'].isin(['Cuentas por Pagar', 'Impuestos por Pagar']))]['Monto'].sum())
        total_activos = df[df['Tipo']=='Activo']['Monto'].sum()
        total_pasivos = abs(df[df['Tipo']=='Pasivo']['Monto'].sum())
        patrimonio = abs(df[df['Tipo']=='Patrimonio']['Monto'].sum())
        ingresos = df[df['Tipo']=='Ingreso']['Monto'].sum()
        costos_venta = abs(df[df['Clasificacion_NIC']=='Costo de Ventas']['Monto'].sum())
        gastos_op = abs(df[df['Clasificacion_NIC'].isin(['Gastos de Administración', 'Gastos de Ventas'])]['Monto'].sum())
        utilidad_bruta = ingresos - costos_venta
        ebitda = utilidad_bruta - gastos_op 
        utilidad_neta = ebitda 
        
        liquidez = activos_cte / pasivos_cte if pasivos_cte > 0 else 0
        apalancamiento = total_pasivos / patrimonio if patrimonio > 0 else 0
        margen_bruto = (utilidad_bruta / ingresos * 100) if ingresos > 0 else 0
        margen_neto = (utilidad_neta / ingresos * 100) if ingresos > 0 else 0
        roi = (utilidad_neta / (total_activos if total_activos > 0 else 1)) * 100
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Margen Bruto", f"{margen_bruto:.1f}%")
        col2.metric("EBITDA", f"${ebitda:,.0f}")
        col3.metric("Margen Neto", f"{margen_neto:.1f}%")
        col4.metric("ROI", f"{roi:.1f}%")
        col5.metric("Ingresos Totales", f"${ingresos:,.0f}")
        
        col6, col7 = st.columns(2)
        col6.metric("Liquidez Corriente", f"{liquidez:.2f}", delta="Meta > 1.0")
        col7.metric("Apalancamiento", f"{apalancamiento:.2f}", delta="Meta < 2.0", delta_color="inverse")

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
# MÓDULO 5: ESTRATEGIA & EVALUACIÓN
# =============================================================================
elif menu == "5. Estrategia & Evaluación":
    st.header("♟️ Ingeniería Financiera de Proyectos")
    
    tabs_strat = st.tabs(["Evaluación Proyectos (VPN/TIR)", "Simulación Riesgo"])
    
    with tabs_strat[0]:
        st.subheader("Evaluación desde Cartera")
        col_sel, col_calc = st.columns([1, 2])
        
        with col_sel:
            proyectos_db = st.session_state['projects_db']
            if not proyectos_db.empty:
                seleccion = st.selectbox("Proyecto a Evaluar", proyectos_db['Nombre_Proyecto'].unique())
                datos_proy = proyectos_db[proyectos_db['Nombre_Proyecto'] == seleccion].iloc[0]
                inv_sug = datos_proy['Costos_Directos_Est']
                ing_sug = datos_proy['Ingresos_Est']
                st.info(f"Costo Est: ${inv_sug:,.0f}\nVenta Est: ${ing_sug:,.0f}")
            else:
                st.warning("No hay proyectos en cartera.")
                inv_sug, ing_sug = 10000000, 15000000

        with col_calc:
            with st.container(border=True):
                c1, c2 = st.columns(2)
                inv = c1.number_input("Inversión Inicial", value=float(inv_sug))
                years = c2.slider("Duración (Años)", 1, 10, 5)
                flujo_est = c1.number_input("Flujo Neto Anual Estimado", value=float(ing_sug * 0.2)) 
                tasa = c2.number_input("Tasa Descuento (WACC) %", 12.0) / 100
                
                if st.button("Calcular Indicadores", type="primary"):
                    vpn, tir = FinancialEngine.calculate_dcf(inv, [flujo_est]*years, tasa)
                    k1, k2, k3 = st.columns(3)
                    k1.metric("VPN", f"${vpn:,.0f}", delta="Viable" if vpn>0 else "No Viable")
                    k2.metric("TIR", f"{tir*100:.2f}%")
                    k3.metric("Payback", f"{(inv/flujo_est):.1f} Años")

    with tabs_strat[1]:
        st.subheader("Simulación Monte Carlo")
        if st.button("Ejecutar S
