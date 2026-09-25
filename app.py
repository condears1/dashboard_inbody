import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlalchemy as sa
from sqlalchemy import text

st.set_page_config(page_title="InBody Dashboard - Sebastian Conde", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS CSS: OCULTAR GITHUB, DEPLOY Y MENÚ ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Ocultar enlace/icono de GitHub en la barra superior */
    header a[href*="github"], [data-testid="stToolbar"] a[href*="github"] {
        display: none !important;
    }

    /* Ocultar botón de Deploy y menú principal */
    .stDeployButton {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }

    h1, h2, h3, h4, h5, h6, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        letter-spacing: 0.5px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .section-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #FAFAFA;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS ---
@st.cache_resource
def init_connection():
    return sa.create_engine(st.secrets["database_url"])

engine = init_connection()

def get_data():
    query = "SELECT * FROM fisico.evaluaciones_inbody ORDER BY fecha_test ASC"
    df = pd.read_sql(query, con=engine)
    return df

# --- SISTEMA DE AUTENTICACIÓN ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.sidebar.text_input("Contraseña de Administrador", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.sidebar.text_input("Contraseña de Administrador", type="password", on_change=password_entered, key="password")
        st.sidebar.error("Contraseña incorrecta")
        return False
    else:
        return True

# --- PANEL DE ADMINISTRACIÓN ---
st.sidebar.header("Panel de Control")

if check_password():
    st.sidebar.success("Acceso autorizado")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["password_correct"] = False
        st.rerun()
        
    # Formulario para nuevo registro
    with st.sidebar.form("form_nuevo_registro", clear_on_submit=True):
        st.subheader("Nueva Evaluación InBody")
        fecha_nueva = st.date_input("Fecha de la evaluación")
        peso_nuevo = st.number_input("Peso Total (kg)", min_value=50.0, max_value=150.0, step=0.1, format="%.1f")
        musculo_nuevo = st.number_input("Masa Muscular (kg)", min_value=20.0, max_value=80.0, step=0.1, format="%.1f")
        grasa_kg_nueva = st.number_input("Masa Grasa (kg)", min_value=5.0, max_value=80.0, step=0.1, format="%.1f")
        grasa_pct_nueva = st.number_input("Porcentaje Grasa (%)", min_value=5.0, max_value=50.0, step=0.1, format="%.1f")
        visceral_nueva = st.number_input("Nivel Grasa Visceral", min_value=1, max_value=30, step=1)
        agua_nueva = st.number_input("Agua Corporal Total (L)", min_value=20.0, max_value=80.0, step=0.1, format="%.1f")
        prot_nueva = st.number_input("Proteínas (kg)", min_value=5.0, max_value=30.0, step=0.1, format="%.1f")
        min_nuevo = st.number_input("Minerales (kg)", min_value=1.0, max_value=10.0, step=0.01, format="%.2f")
        imc_nuevo = st.number_input("IMC", min_value=15.0, max_value=50.0, step=0.1, format="%.1f")
        tmb_nuevo = st.number_input("TMB (kcal)", min_value=1000, max_value=4000, step=1)
        pts_nuevo = st.number_input("Puntuación InBody", min_value=1, max_value=120, step=1)
        
        btn_guardar = st.form_submit_button("Guardar en Base de Datos")
        
        if btn_guardar:
            try:
                insert_query = text("""
                    INSERT INTO fisico.evaluaciones_inbody 
                    (fecha_test, peso_total, masa_musculoesqueletica, masa_grasa, porcentaje_grasa, 
                     grasa_visceral, agua_corporal, proteinas, minerales, imc, tmb, puntuacion_inbody)
                    VALUES 
                    (:fecha, :peso, :musculo, :grasa, :pct_grasa, :visceral, :agua, :prot, :min, :imc, :tmb, :pts)
                """)
                with engine.connect() as conn:
                    conn.execute(insert_query, {
                        "fecha": fecha_nueva, "peso": peso_nuevo, "musculo": musculo_nuevo, 
                        "grasa": grasa_kg_nueva, "pct_grasa": grasa_pct_nueva, "visceral": visceral_nueva,
                        "agua": agua_nueva, "prot": prot_nueva, "min": min_nuevo, "imc": imc_nuevo, 
                        "tmb": tmb_nuevo, "pts": pts_nuevo
                    })
                    conn.commit()
                st.sidebar.success("Datos guardados correctamente.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error al guardar: {e}")

    # Sección de Eliminación de Registros por Fecha
    st.sidebar.divider()
    st.sidebar.subheader("Gestión de Registros")
    df_actual = get_data()
    if not df_actual.empty:
        opciones_borrar = {f"{row['fecha_test']} - {row['peso_total']} kg": row['fecha_test'] for _, row in df_actual.iterrows()}
        reg_seleccionado = st.sidebar.selectbox("Selecciona registro a eliminar", options=list(opciones_borrar.keys()))
        
        if st.sidebar.button("Eliminar Registro Seleccionado"):
            fecha_a_borrar = opciones_borrar[reg_seleccionado]
            try:
                delete_query = text("DELETE FROM fisico.evaluaciones_inbody WHERE fecha_test = :fecha_val")
                with engine.connect() as conn:
                    conn.execute(delete_query, {"fecha_val": fecha_a_borrar})
                    conn.commit()
                st.sidebar.success("Registro eliminado con éxito.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error al eliminar: {e}")
else:
    st.sidebar.info("Ingresa la contraseña para gestionar evaluaciones.")

# --- ENCABEZADO CON INFORMACIÓN DE USUARIO ---
st.title("Sebastian Conde | Análisis de Composición Corporal")
st.markdown("**Género:** Masculino | **Edad:** 25 años | **Altura:** 174 cm | **Objetivo:** 195 lbs (~88.45 kg)")
st.divider()

# --- LECTURA DE DATOS ---
df = get_data()

if df.empty:
    st.info("No hay datos registrados en la base de datos. Utiliza el panel izquierdo para ingresar tus primeras evaluaciones.")
else:
    # --- KPIS AMPLIADOS ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg> Estado Actual (Última Evaluación)</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    ultimo_peso_kg = float(df['peso_total'].iloc[-1])
    ultimo_peso_lbs = ultimo_peso_kg * 2.20462
    libras_restantes = ultimo_peso_lbs - 195
    
    if len(df) > 1:
        delta_peso = ultimo_peso_kg - float(df['peso_total'].iloc[-2])
        delta_grasa = float(df['porcentaje_grasa'].iloc[-1]) - float(df['porcentaje_grasa'].iloc[-2])
        delta_musculo = float(df['masa_musculoesqueletica'].iloc[-1]) - float(df['masa_musculoesqueletica'].iloc[-2])
        delta_masagrasa = float(df['masa_grasa'].iloc[-1]) - float(df['masa_grasa'].iloc[-2])
        delta_visceral = int(df['grasa_visceral'].iloc[-1]) - int(df['grasa_visceral'].iloc[-2])
    else:
        delta_peso = delta_grasa = delta_musculo = delta_masagrasa = delta_visceral = 0.0

    col1.metric("Peso Actual", f"{ultimo_peso_kg:.1f} kg", f"{delta_peso:.1f} kg", delta_color="inverse")
    col2.metric("Brecha Objetivo", f"{libras_restantes:.1f} lbs")
    col3.metric("Porcentaje Grasa", f"{df['porcentaje_grasa'].iloc[-1]:.1f}%", f"{delta_grasa:.1f}%", delta_color="inverse")
    col4.metric("Masa Muscular", f"{df['masa_musculoesqueletica'].iloc[-1]:.1f} kg", f"{delta_musculo:.1f} kg", delta_color="normal")
    col5.metric("Masa Grasa", f"{df['masa_grasa'].iloc[-1]:.1f} kg", f"{delta_masagrasa:.1f} kg", delta_color="inverse")
    col6.metric("Grasa Visceral", f"{int(df['grasa_visceral'].iloc[-1])}", f"{delta_visceral}", delta_color="inverse")

    st.divider()

    # --- GRÁFICAS DE TENDENCIA ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg> Análisis de Tendencias</div>', unsafe_allow_html=True)
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Scatter(x=df['fecha_test'], y=df['peso_total'], name="Peso (kg)", mode='lines+markers', line=dict(color='blue')), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df['fecha_test'], y=df['porcentaje_grasa'], name="% Grasa", mode='lines+markers', line=dict(color='red')), secondary_y=True)
        fig1.update_layout(title_text="Descenso de Peso y Porcentaje de Grasa")
        st.plotly_chart(fig1, use_container_width=True)

    with col_graf2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df['fecha_test'], y=df['masa_musculoesqueletica'], name='Músculo (kg)', marker_color='green'))
        fig2.add_trace(go.Bar(x=df['fecha_test'], y=df['masa_grasa'], name='Grasa (kg)', marker_color='orange'))
        fig2.update_layout(title_text="Comparativa Músculo vs Grasa Corporal", barmode='group')
        st.plotly_chart(fig2, use_container_width=True)

    # --- LECTURA DE HISTÓRICO COMPLETO ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg> Lectura de Evolución Histórica</div>', unsafe_allow_html=True)
    if len(df) > 1:
        total_peso_perdido = float(df['peso_total'].iloc[0]) - float(df['peso_total'].iloc[-1])
        total_grasa_perdida = float(df['masa_grasa'].iloc[0]) - float(df['masa_grasa'].iloc[-1])
        total_musculo_var = float(df['masa_musculoesqueletica'].iloc[-1]) - float(df['masa_musculoesqueletica'].iloc[0])
        st.info(f"""
        * **Resumen de Trayectoria:** Desde tu primera evaluación registrada el {pd.to_datetime(df['fecha_test'].iloc[0]).strftime('%d.%m.%Y')} hasta la fecha actual ({pd.to_datetime(df['fecha_test'].iloc[-1]).strftime('%d.%m.%Y')}):
          * Has logrado un descenso total de **{total_peso_perdido:.1f} kg** en tu peso corporal.
          * La masa grasa se redujo en **{total_grasa_perdida:.1f} kg**, demostrando efectividad en el objetivo de definición.
          * La variación de masa musculoesquelética muestra una fluctuación de **{total_musculo_var:+.1f} kg**, lo cual resalta la importancia de optimizar la ingesta proteica y el volumen de entrenamiento para proteger la ganancia magra en lo que resta del déficit.
        """)
    else:
        st.info("Se requieren al menos 2 evaluaciones registradas para generar la lectura comparativa de evolución.")

    st.divider()

    # --- COMPARATIVO SEGMENTAL ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Comparativo Segmental (Últimas 2 Evaluaciones)</div>', unsafe_allow_html=True)
    if len(df) >= 2:
        penúltima = df.iloc[-2]
        ultima = df.iloc[-1]
        
        col_seg1, col_seg2 = st.columns(2)
        with col_seg1:
            st.markdown(f"**Evaluación anterior ({pd.to_datetime(penúltima['fecha_test']).strftime('%d.%m.%Y')}):**")
            st.write(f"- Peso: {penúltima['peso_total']} kg | Grasa Corp: {penúltima['masa_grasa']} kg | Músculo Esquelético: {penúltima['masa_musculoesqueletica']} kg")
        with col_seg2:
            st.markdown(f"**Evaluación más reciente ({pd.to_datetime(ultima['fecha_test']).strftime('%d.%m.%Y')}):**")
            st.write(f"- Peso: {ultima['peso_total']} kg | Grasa Corp: {ultima['masa_grasa']} kg | Músculo Esquelético: {ultima['masa_musculoesqueletica']} kg")
            
        st.markdown("""
        > **Análisis Segmental:** El comparativo entre los últimos dos registros refleja una tendencia positiva en la oxidación de tejido adiposo. Se observa estabilidad en el tejido magro global, lo cual ratifica la correcta ejecución del protocolo de déficit e hipertrofia.
        """)
    else:
        st.warning("Se necesitan al menos dos registros en la base de datos para mostrar el comparativo segmental.")

    st.divider()

    # --- RECOMENDACIONES NUTRICIONALES SEGÚN TMB ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg> Guía Nutricional según Tasa Metabólica Basal (TMB)</div>', unsafe_allow_html=True)
    tmb_actual = float(df['tmb'].iloc[-1])
    tdee = tmb_actual * 1.55
    
    col_nut1, col_nut2, col_nut3 = st.columns(3)
    with col_nut1:
        st.markdown("### Déficit (Pérdida de Grasa)")
        st.write(f"**Calorías sugeridas:** ~{int(tdee - 500)} kcal/día")
        st.write("Enfoque prioritario para llegar a tus 195 lbs. Protege la masa muscular consumiendo alto valor proteico (2.0g - 2.2g por kg magro) y manteniendo creatina.")
    with col_nut2:
        st.markdown("### Mantenimiento")
        st.write(f"**Calorías sugeridas:** ~{int(tdee)} kcal/día")
        st.write("Ideal para recomposición corporal estable, permitiendo consolidar fuerza en tus sesiones de Arnold Split sin fatiga excesiva del sistema nervioso.")
    with col_nut3:
        st.markdown("### Volumen (Ganancia Muscular)")
        st.write(f"**Calorías sugeridas:** ~{int(tdee + 350)} kcal/día")
        st.write("Superávit controlado para maximizar la síntesis proteica una vez alcanzado el objetivo de peso ideal.")

    st.divider()

    # --- PRONÓSTICO DE DÉFICIT ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> Pronóstico y Proyección de Déficit (Meta: 195 lbs / 88.45 kg)</div>', unsafe_allow_html=True)
    peso_actual_lbs = ultimo_peso_lbs
    meta_lbs = 195.0
    diferencia_lbs = peso_actual_lbs - meta_lbs
    ritmo_perdida_mensual_lbs = 6.0
    meses_estimados = diferencia_lbs / ritmo_perdida_mensual_lbs
    
    st.info(f"""
    * **Resumen del Pronóstico:** Te encuentras a **{diferencia_lbs:.1f} lbs** de tu meta estipulada de 195 lbs. Manteniendo un déficit calórico constante y controlado de 500 kcal diarias junto a tu disciplina en el gimnasio, el tiempo estimado para alcanzar el objetivo es de aproximadamente **{meses_estimados:.1f} meses**.
    """)
    
    proyeccion_data = []
    peso_proyectado = peso_actual_lbs
    fecha_base = pd.to_datetime(df['fecha_test'].iloc[-1])
    
    for i in range(1, int(meses_estimados) + 2):
        fecha_proyectada = fecha_base + pd.DateOffset(months=i)
        peso_proyectado = max(meta_lbs, peso_proyectado - ritmo_perdida_mensual_lbs)
        proyeccion_data.append({
            "Mes Proyectado": fecha_proyectada.strftime('%B %Y'),
            "Peso Estimado (lbs)": round(peso_proyectado, 1),
            "Peso Estimado (kg)": round(peso_proyectado / 2.20462, 1),
            "Brecha Restante (lbs)": round(peso_proyectado - meta_lbs, 1)
        })
    
    st.dataframe(pd.DataFrame(proyeccion_data), use_container_width=True)

    st.divider()

    # --- RUTINA ARNOLD SPLIT ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6.5 6.5h11M6.5 17.5h11M3 12h18M6.5 2v4M17.5 2v4M6.5 18v4M17.5 18v4"/></svg> Rutina Actual: Arnold Split (6 Días por Semana)</div>', unsafe_allow_html=True)
    st.markdown("""
    * **Metodología:** Hipertrofia con sobrecarga progresiva, buscando el peso máximo al fallo absoluto en un rango de **6 a 10 repeticiones**. 
    * **Estructura de Series:** 3 series de trabajo efectivo al fallo por cada ejercicio listado.
    """)
    
    split_data = [
        {"Día": "Lunes / Jueves", "Grupo Muscular": "Pecho, Hombros, Tríceps", "Ejercicios": "Pecho (3), Hombro (2), Tríceps (2)", "Frecuencia": "2x por semana", "Recuperación": "72 horas"},
        {"Día": "Martes / Viernes", "Grupo Muscular": "Espalda, Bíceps, Antebrazo, Trapecio, Hombro Posterior", "Ejercicios": "Espalda (4), Bíceps (2), Antebrazo (1), Trapecio (1)", "Frecuencia": "2x por semana", "Recuperación": "72 horas"},
        {"Día": "Miércoles / Domingo", "Grupo Muscular": "Pierna Completa", "Ejercicios": "Cuádriceps (2), Isquiotibiales/Glúteo (2), Aductores (1), Pantorrilla (1)", "Frecuencia": "2x por semana", "Recuperación": "72 horas"}
    ]
    st.table(pd.DataFrame(split_data))

    st.divider()

    # --- HISTORIAL COMPLETO TABLA ---
    st.markdown('<div class="section-title"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg> Historial Completo de Evaluaciones</div>', unsafe_allow_html=True)
    df_display = df.copy()
    df_display['fecha_test'] = pd.to_datetime(df_display['fecha_test']).dt.strftime('%d.%m.%Y')
    st.dataframe(df_display, use_container_width=True)

# --- FIRMA Y PIE DE PÁGINA ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #888888; font-family: 'Rajdhani', sans-serif; font-size: 1.1em;">
    <p><b>SEBASTIAN CONDE</b> | 2027</p>
    <p><i>"Struggle, rage, contend! That's the only course left for us mortals!"</i> — Berserk</p>
</div>
""", unsafe_allow_html=True)