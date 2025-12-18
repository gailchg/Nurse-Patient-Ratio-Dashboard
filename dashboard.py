import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nurse to Patient Ratio Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS  ---
st.markdown("""
<style>
    /* 1. LOAD FONT */
    @import url('https://fonts.googleapis.com/css2?family=Karla:wght@400;600;700&display=swap');

    /* 2. APPLY FONT TO TEXT ONLY (Not Icons) */
    html, body, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .metric-value, .metric-label {
        font-family: 'Karla', sans-serif !important;
    }
            
    /* 3. BACKGROUND & CARDS */
    .stApp {
        background-color: #f4f6f9;
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #eaeaea;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Remove top padding */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('Final_Dashboard_Data_v3.csv')
    # Handle DD/MM/YYYY format correctly
    df['D.O.A'] = pd.to_datetime(df['D.O.A'], dayfirst=True)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Error: 'Final_Dashboard_Data_v3.csv' not found.")
    st.stop()

# --- 4. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🏥 Control Panel")
    st.markdown("Use these tools to filter the dashboard views.")
    st.divider()
    
    # DATE FILTER
    st.subheader("📅 Date Range")
    min_dt = df['D.O.A'].min().date()
    max_dt = df['D.O.A'].max().date()
    
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start", min_dt, min_value=min_dt, max_value=max_dt)
    end_date = c2.date_input("End", max_dt, min_value=min_dt, max_value=max_dt)
    
    if start_date > end_date:
        st.error("Start Date cannot be after End Date.")
        st.stop()

    st.divider()
    
    # RISK FILTER
    st.subheader("⚠️ Risk Filter")
    st.caption("Filter out 'safe' days to focus on overcrowding.")
    min_ratio = st.slider(
        "Show only days with Ratio > X", 
        1.0, 5.0, 1.0, 0.1
    )
    
    if min_ratio >= 4.0:
        st.error("Showing only CRITICAL days.")
    elif min_ratio > 1.0:
        st.warning(f"Hiding days with ratio < {min_ratio}")
    else:
        st.info("Showing ALL data.")

# FILTER LOGIC
mask = (df['D.O.A'].dt.date >= start_date) & (df['D.O.A'].dt.date <= end_date)
df_filtered = df.loc[mask]
df_filtered = df_filtered[df_filtered['Patients_Per_Nurse'] >= min_ratio]

# --- 5. DASHBOARD HEADER (YOUR EXACT TOPIC) ---
st.markdown("# Nurse-to-Patient Ratio Monitor")
st.markdown("### *Real-time staffing visualization against patient influx*")
st.markdown("---")

# Logic to handle empty data
if len(df_filtered) == 0:
    st.warning("No data found for these filters! Try lowering the Risk Filter.")
    st.stop()

# --- 6. METRIC CARDS ---
avg_patients = round(df_filtered['Patient_Count'].mean(), 1)
avg_nurses = round(df_filtered['Estimated_Nurse_Count'].mean(), 1)
avg_ratio = round(df_filtered['Patients_Per_Nurse'].mean(), 2)
risk_days = len(df_filtered[df_filtered['Patients_Per_Nurse'] > 4.0])

c1, c2, c3, c4 = st.columns(4)

def card(col, label, value, suffix=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

card(c1, "Avg Daily Patients", avg_patients)
card(c2, "Avg Nurse Staffing", avg_nurses)
card(c3, "Nurse-to-Patient Ratio", f"1:{avg_ratio}")
card(c4, "High Risk Days", risk_days, " Days")

st.markdown("##")

# --- 7. MAIN AREA CHART ---
st.subheader("📈 Patient Influx vs. Nurse Supply")

fig_main = go.Figure()

# Patients Area (Soft Blue)
fig_main.add_trace(go.Scatter(
    x=df_filtered['D.O.A'], 
    y=df_filtered['Patient_Count'],
    mode='lines',
    name='Patient Demand',
    line=dict(width=0, color='#3498db'),
    stackgroup='one',
    fillcolor='rgba(52, 152, 219, 0.3)'
))

# Nurses Line (Sharp Red)
fig_main.add_trace(go.Scatter(
    x=df_filtered['D.O.A'], 
    y=df_filtered['Estimated_Nurse_Count'],
    mode='lines',
    name='Nurse Supply',
    line=dict(width=3, color='#e74c3c'),
))

fig_main.update_layout(
    font=dict(family="Karla, sans-serif", size=14, color="#2c3e50"),
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=0, r=0, t=30, b=0),
    height=450,
    showlegend=True, 
    legend=dict(orientation="h", y=1.1, x=1)
)
st.plotly_chart(fig_main, use_container_width=True)

# --- 8. BOTTOM CHARTS ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📋 Ratio Frequency")
    fig_hist = px.histogram(
        df_filtered, 
        x="Patients_Per_Nurse", 
        nbins=20,
        color_discrete_sequence=['#3498db']
    )
    fig_hist.update_layout(
        font=dict(family="Karla, sans-serif"),
        template="plotly_white",
        xaxis_title="Patients per Nurse",
        yaxis_title="Days Occurred",
        bargap=0.2
    )
    fig_hist.add_vline(x=4.0, line_dash="dash", line_color="#e74c3c", annotation_text="Danger Zone")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_right:
    st.subheader("🌡️ Occupancy Heatmap")
    fig_scatter = px.scatter(
        df_filtered, 
        x="Occupancy_Rate", 
        y="Patients_Per_Nurse",
        size="Patient_Count",
        color="Patients_Per_Nurse",
        color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
    )
    fig_scatter.update_layout(
        font=dict(family="Karla, sans-serif"),
        template="plotly_white",
        xaxis_title="Bed Occupancy (%)",
        yaxis_title="Nurse Ratio (1:X)",
        coloraxis_showscale=False 
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- 9. DATA SOURCE & METHODOLOGY (PROJECT FOOTER) ---
st.markdown("---")
with st.expander("📝 Data Source & Methodology Note (Click to Expand)", expanded=True):
    st.markdown("""
    **Data Source:** Original patient admission data was sourced from the [Hospital Admissions Dataset (Kaggle)](https://www.kaggle.com/datasets/ashishsahani/hospital-admissions-data).
    
    **Methodology & Enrichment:** The original dataset contained patient timestamps (`D.O.A`) and volume (`Patient_Count`) but lacked specific nurse staffing logs. 
    To enable this analysis, **Nurse Counts** were enriched using a standard 1:5 nurse-to-patient ratio model to simulate realistic staffing requirements based on daily patient influx.
    
    *Note: This data enrichment method for simulation purposes was explicitly approved by the course instructor.*
    """)