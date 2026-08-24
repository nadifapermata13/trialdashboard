# pyrefly: ignore [missing-import
import os
# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as graph_objects
from datetime import datetime, date
import re
import base64


_BASE = os.path.dirname(os.path.abspath(__file__))

logo1 = os.path.join(_BASE, "gambar", "logo_dsb.png")
logo2 = os.path.join(_BASE, "gambar", "logo_ppsb.png")

# Set page configuration
st.set_page_config(
    page_title="Monitoring Stok Bahan Baku",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colors and Palette Definition (Green, Yellow, Gold)
PRIMARY_GOLD = "#D4AF37"
DEEP_GREEN = "#1B332B"
MEDIUM_GREEN = "#2E5A44"
LIGHT_GREEN = "#E8ECE9"
ACCENT_YELLOW = "#FFD700"
MUTED_GOLD = "#C5A028"

# Custom CSS for styling
st.markdown(f"""
<style>
    /* Main Layout Adjustments */
    .stApp {{
        background-color: #F4F7F5;
        color: #1B332B;
    }}
    
    /* Header styling */
    .dashboard-header {{
        background: linear-gradient(135deg, {DEEP_GREEN} 0%, {MEDIUM_GREEN} 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: #FCFBF7;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border-bottom: 5px solid {PRIMARY_GOLD};
    }}
    
    .dashboard-header h1 {{
        color: {PRIMARY_GOLD};
        margin: 0;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
    }}
    
    .dashboard-header p {{
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 300;
    }}

    /* Card Metrics Styling */
    .metric-card {{
        background-color: #FFFFFF;
        border-left: 5px solid {PRIMARY_GOLD};
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s ease-in-out;
    }}
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }}
    .metric-card.safe {{
        border-left: 5px solid #2E7D32;
    }}
    .metric-card.warning {{
        border-left: 5px solid #FBC02D;
    }}
    .metric-card.critical {{
        border-left: 5px solid #D32F2F;
    }}
    
    .metric-title {{
        font-size: 0.9rem;
        color: #556B5C;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {DEEP_GREEN};
        margin: 0.2rem 0;
    }}
    .metric-desc {{
        font-size: 0.8rem;
        color: #7A9080;
    }}

    /* Alert Banner Styling */
    .alert-banner {{
        background: linear-gradient(135deg, #FDF4E3 0%, #FAF0D7 100%);
        border: 1px solid {PRIMARY_GOLD};
        border-left: 8px solid {PRIMARY_GOLD};
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        color: #5C4308;
    }}
    .alert-banner-critical {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border: 1px solid #E53935;
        border-left: 8px solid #E53935;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        color: #B71C1C;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #E8ECE9;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        color: {DEEP_GREEN};
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {DEEP_GREEN} !important;
        color: white !important;
        border-bottom: 3px solid {PRIMARY_GOLD} !important;
    }}
</style>
""", unsafe_allow_html=True)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vROstfR4q2cYntbPuCY8BF2zBSSVa7RWKGTSU8CuiKKuEj70S9sq93S0WOYM7QGf-Pq8W3wQX0mD5Ov/pub?gid=2003469515&single=true&output=csv"

# Robust Parsing Helper Functions
def parse_id_number(val):
    if pd.isna(val) or val == '' or str(val).strip() == '':
        return 0.0
    val_str = str(val).strip()
    if ',' in val_str:
        # Indonesian format: e.g. "90.000,00" -> remove dot, replace comma with dot
        val_str = val_str.replace('.', '').replace(',', '.')
    else:
        # e.g. "226.352" -> remove dot (since it's a thousands separator with no decimals)
        val_str = val_str.replace('.', '')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def parse_id_date(date_str):
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if not date_str:
        return None
    
    months_map = {
        'januari': 1, 'jan': 1,
        'februari': 2, 'feb': 2,
        'maret': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'mei': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'agustus': 8, 'agt': 8, 'aug': 8,
        'september': 9, 'sep': 9,
        'oktober': 10, 'okt': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'desember': 12, 'des': 12, 'dec': 12
    }
    
    # Format "9-Mar-26"
    m = re.match(r'(\d+)-([A-Za-z]+)-(\d+)', date_str)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        if year < 100:
            year += 2000
        month = months_map.get(month_name, 1)
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
            
    # Format "11 Maret 2026"
    m2 = re.match(r'(\d+)\s+([A-Za-z]+)\s+(\d+)', date_str)
    if m2:
        day = int(m2.group(1))
        month_name = m2.group(2).lower()
        year = int(m2.group(3))
        month = months_map.get(month_name, 1)
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
            
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return None

# Load and process data
@st.cache_data(ttl=300)
def load_data():
    try:
        # Load directly from Google Sheet CSV
        df = pd.read_csv(CSV_URL, dtype=str)
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame()

    # Clean headers
    df.columns = df.columns.str.strip()
    
    # Filter empty rows
    df = df.dropna(subset=['Tanggal', 'Material'])
    df = df[df['Material'].str.strip() != '']
    
    # Parse numerical columns
    num_cols = [
        'Stock Awal', '100% Kedatangan', '0% Kedatangan',
        'Coverage days (100%)', 'Coverage days (0%)', 'Consumption',
        'Safety Stock (tonase)', 'Safety Stock (hari)'
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_id_number)
            
    # Parse dates
    df['ParsedDate'] = df['Tanggal'].apply(parse_id_date)
    df = df.dropna(subset=['ParsedDate'])
    
    # Clean status strings
    status_cols = ['Status (100%)', 'Status (0%)']
    for col in status_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').str.strip()
            
    df = df.sort_values(by=['ParsedDate', 'Material'])
    return df

df_raw = load_data()

if df_raw.empty:
    st.error("Data tidak dapat dimuat. Pastikan koneksi internet aktif dan link spreadsheet valid.")
else:
    # ------------------ SIDEBAR FILTER ------------------
    logo1 = os.path.join(_BASE, "gambar", "logo_dsb.png")
    logo2 = os.path.join(_BASE, "gambar", "logo_its.png")

    # Logo di atas sidebar
    col1, col2 = st.sidebar.columns([1, 2])

    col1.image(logo1, width=55)
    col2.image(logo2, width=75)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<h2 style='color:{DEEP_GREEN}; margin-top:0;'>Filter Dashboard</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    
    # Date selection
    unique_dates = sorted(df_raw['ParsedDate'].unique())
    unique_dates_formatted = [d.strftime('%Y-%m-%d') for d in unique_dates]
    
    # Determine default date (e.g. today's date in 2026 if exists, otherwise the latest available date)
    target_default = datetime(2026, 7, 15)
    default_idx = len(unique_dates) - 1 # Default to latest
    for i, d in enumerate(unique_dates):
        if d.year == target_default.year and d.month == target_default.month and d.day == target_default.day:
            default_idx = i
            break
            
    selected_date_str = st.sidebar.selectbox(
        "Pilih Tanggal Monitoring:",
        options=unique_dates_formatted,
        index=default_idx
    )
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
    
    # Material filter
    all_materials = sorted(df_raw['Material'].unique())
    selected_materials = st.sidebar.multiselect(
        "Filter Material:",
        options=all_materials,
        default=all_materials
    )
    
    if not selected_materials:
        st.warning("Silakan pilih minimal satu material.")
        st.stop()
        
    # Filter the main dataframe for the selected date
    df_date = df_raw[df_raw['ParsedDate'] == selected_date]
    df_date_filtered = df_date[df_date['Material'].isin(selected_materials)]
    
    # Filter raw data for trend charts (all dates for selected materials)
    df_trends = df_raw[df_raw['Material'].isin(selected_materials)]

    # ------------------ HEADER ------------------
    logo = os.path.join(_BASE, "gambar", "logo_ppsb.png")

    # Logo di atas banner
    col1, col2, col3 = st.columns([4,2,4])

    with col2:
        st.image(logo, width=300)

    st.markdown("""
        <div style="
            background:#234d39;
            padding:40px;
            border-radius:18px;
            border-bottom:6px solid #d4af37;">
            <h1 style="color:#d4af37;margin-bottom:10px;">
                MONITORING STOK BAHAN BAKU
            </h1>
            <p style="color:white;font-size:20px;">
                Sistem Deteksi Warning & Perencanaan Stok Bahan Baku
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ ALERTS & WARNINGS ------------------
    # Check if there are any warnings
    critical_100 = df_date_filtered[df_date_filtered['Status (100%)'] == 'Critical']['Material'].tolist()
    critical_0 = df_date_filtered[df_date_filtered['Status (0%)'] == 'Critical']['Material'].tolist()
    
    if critical_100 or critical_0:
        alert_msg = "<h4>⚠️ WARNING DETEKSI KRITIS STOK BAHAN BAKU:</h4><ul>"
        if critical_100:
            alert_msg += f"<li><b>Kondisi 100% Kedatangan:</b> Material <span style='font-weight:bold;'>{', '.join(critical_100)}</span> berstatus <b>CRITICAL</b>! Segera lakukan pemesanan atau atur jadwal ulang produksi.</li>"
        if critical_0:
            alert_msg += f"<li><b>Kondisi 0% Kedatangan (Skenario Terburuk):</b> Material <span style='font-weight:bold;'>{', '.join(critical_0)}</span> berstatus <b>CRITICAL</b>! Cadangan stok hampir habis atau di bawah batas aman.</li>"
        alert_msg += "</ul>"
        
        st.markdown(f"""
        <div class="alert-banner-critical">
            {alert_msg}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-banner">
            ✅ <b>Status Stok Aman:</b> Seluruh material terpilih berada dalam status <b>SAFE</b> untuk tanggal {selected_date.strftime('%d %B %Y')}.
        </div>
        """, unsafe_allow_html=True)

    # ------------------ KPI WIDGETS ------------------
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    # Calculate values
    total_stok_100 = df_date_filtered['100% Kedatangan'].sum()
    total_stok_0 = df_date_filtered['0% Kedatangan'].sum()
    avg_cov_100 = df_date_filtered['Coverage days (100%)'].mean()
    avg_cov_0 = df_date_filtered['Coverage days (0%)'].mean()
    critical_count = len(set(critical_100 + critical_0))
    
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Stok (100% Kedatangan)</div>
            <div class="metric-value">{total_stok_100:,.0f} ton</div>
            <div class="metric-desc">Proyeksi stok jika kedatangan lancar</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="metric-title">Total Stok (0% Kedatangan)</div>
            <div class="metric-value">{total_stok_0:,.0f} ton</div>
            <div class="metric-desc">Stok fisik aktual tanpa kiriman baru</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi3:
        st.markdown(f"""
        <div class="metric-card {'safe' if avg_cov_0 >= 30 else 'warning'}">
            <div class="metric-title">Rata-rata Coverage (0%)</div>
            <div class="metric-value">{avg_cov_0:.1f} hari</div>
            <div class="metric-desc">Ketahanan stok tanpa kiriman baru</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi4:
        st.markdown(f"""
        <div class="metric-card {'safe' if critical_count == 0 else 'critical'}">
            <div class="metric-title">Material Risiko Kritis</div>
            <div class="metric-value">{critical_count} Material</div>
            <div class="metric-desc">Butuh tindakan segera</div>
        </div>
        """, unsafe_allow_html=True)

    # ------------------ DETAILED MONITORING TABLE ------------------
    st.markdown(f"<h3 style='color:{DEEP_GREEN}; margin-top:1.5rem;'>📋 Detail Stok & Status Material</h3>", unsafe_allow_html=True)
    
    # Columns mapping and formatting
    display_df = df_date_filtered[[
        'Material',
        '100% Kedatangan',
        '0% Kedatangan',
        'Coverage days (100%)',
        'Coverage days (0%)',
        'Consumption',
        'Status (100%)',
        'Status (0%)',
        'Safety Stock (tonase)',
        'Safety Stock (hari)'
    ]].copy()
    
    # Rename columns to user requested names
    display_df.columns = [
        'Material',
        'Stock Bahan baku jika 100% Kedatangan',
        'Stock Bahan baku jika 0% Kedatangan',
        'Coverage days (100%)',
        'Coverage days (0%)',
        'Consumption',
        'Status (100%)',
        'Status (0%)',
        'Safety Stock (tonase)',
        'Safety Stock (hari)'
    ]
    
    # Set indices for better rendering
    display_df = display_df.reset_index(drop=True)
    
    # Custom Styler function to color the Streamlit dataframe rows/cells
    def style_dataframe(val):
        if val == 'Critical':
            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold; border-radius: 4px;'
        elif val == 'Safe':
            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold; border-radius: 4px;'
        return ''
        
    styled_display_df = display_df.style.map(
        style_dataframe, 
        subset=['Status (100%)', 'Status (0%)']
    ).format({
        'Stock Bahan baku jika 100% Kedatangan': '{:,.0f} ton',
        'Stock Bahan baku jika 0% Kedatangan': '{:,.0f} ton',
        'Coverage days (100%)': '{:.0f} hari',
        'Coverage days (0%)': '{:.0f} hari',
        'Consumption': '{:,.0f} ton/hari',
        'Safety Stock (tonase)': '{:,.0f} ton',
        'Safety Stock (hari)': '{:.0f} hari'
    })
    
    st.dataframe(
        styled_display_df,
        use_container_width=True,
        hide_index=True
    )

    # ------------------ CHARTS & VISUALIZATIONS ------------------
    st.markdown(f"<h3 style='color:{DEEP_GREEN}; margin-top:2rem;'>📊 Tren Proyeksi & Analisis Stok</h3>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📉 Proyeksi Tren Stok", "📆 Tren Coverage Days", "⚖️ Profil Konsumsi & Safety Stock"])
    
    with tab1:
        st.markdown(f"<h5 style='color:{MEDIUM_GREEN};'>Proyeksi Ketersediaan Stok dari Waktu ke Waktu (Ton)</h5>", unsafe_allow_html=True)
        # Select single material for detailed trend
        active_material = st.selectbox(
            "Pilih Material untuk Analisis Tren Detail:",
            options=selected_materials,
            key="trend_material_select"
        )
        
        df_mat_trend = df_trends[df_trends['Material'] == active_material].sort_values(by='ParsedDate')
        
        # Build interactive Plotly chart
        fig_stock = graph_objects.Figure()
        
        # 100% arrival
        fig_stock.add_trace(graph_objects.Scatter(
            x=df_mat_trend['ParsedDate'],
            y=df_mat_trend['100% Kedatangan'],
            name='Stok (100% Kedatangan)',
            line=dict(color='#2E7D32', width=3),
            mode='lines'
        ))
        
        # 0% arrival
        fig_stock.add_trace(graph_objects.Scatter(
            x=df_mat_trend['ParsedDate'],
            y=df_mat_trend['0% Kedatangan'],
            name='Stok (0% Kedatangan)',
            line=dict(color='#D32F2F', width=2, dash='dot'),
            mode='lines'
        ))
        
        # Safety Stock Line
        safety_stock_val = df_mat_trend['Safety Stock (tonase)'].iloc[0] if not df_mat_trend.empty else 0
        fig_stock.add_trace(graph_objects.Scatter(
            x=df_mat_trend['ParsedDate'],
            y=[safety_stock_val] * len(df_mat_trend),
            name=f'Safety Stock limit ({safety_stock_val:,.0f} ton)',
            line=dict(color=PRIMARY_GOLD, width=2, dash='dash'),
            mode='lines'
        ))
        
        # Add vertical line for "Selected Date"
        fig_stock.add_vline(x=selected_date.timestamp() * 1000, line_width=2, line_dash="dash", line_color=DEEP_GREEN)
        fig_stock.add_annotation(
            x=selected_date,
            y=df_mat_trend['100% Kedatangan'].max() * 0.9 if not df_mat_trend.empty else 100,
            text="Hari Terpilih",
            showarrow=True,
            arrowhead=1,
            arrowcolor=DEEP_GREEN,
            ax=40,
            ay=-30
        )
        
        fig_stock.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor='#ECEFF1'),
            yaxis=dict(showgrid=True, gridcolor='#ECEFF1', title="Jumlah Stok (Ton)")
        )
        
        st.plotly_chart(fig_stock, use_container_width=True)
        
    with tab2:
        st.markdown(f"<h5 style='color:{MEDIUM_GREEN};'>Ketahanan Stok dalam Jumlah Hari Kerja (Coverage Days)</h5>", unsafe_allow_html=True)
        
        # Use the same active material
        df_mat_trend2 = df_trends[df_trends['Material'] == active_material].sort_values(by='ParsedDate')
        
        fig_coverage = graph_objects.Figure()
        
        # 100% coverage
        fig_coverage.add_trace(graph_objects.Scatter(
            x=df_mat_trend2['ParsedDate'],
            y=df_mat_trend2['Coverage days (100%)'],
            name='Coverage (100% Kedatangan)',
            line=dict(color='#2E7D32', width=3),
            mode='lines'
        ))
        
        # 0% coverage
        fig_coverage.add_trace(graph_objects.Scatter(
            x=df_mat_trend2['ParsedDate'],
            y=df_mat_trend2['Coverage days (0%)'],
            name='Coverage (0% Kedatangan)',
            line=dict(color='#D32F2F', width=2, dash='dot'),
            mode='lines'
        ))
        
        # Safety Stock Days Line
        safety_days_val = df_mat_trend2['Safety Stock (hari)'].iloc[0] if not df_mat_trend2.empty else 0
        fig_coverage.add_trace(graph_objects.Scatter(
            x=df_mat_trend2['ParsedDate'],
            y=[safety_days_val] * len(df_mat_trend2),
            name=f'Batas Safety Stock ({safety_days_val:.0f} hari)',
            line=dict(color=PRIMARY_GOLD, width=2, dash='dash'),
            mode='lines'
        ))
        
        fig_coverage.add_vline(x=selected_date.timestamp() * 1000, line_width=2, line_dash="dash", line_color=DEEP_GREEN)
        
        fig_coverage.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor='#ECEFF1'),
            yaxis=dict(showgrid=True, gridcolor='#ECEFF1', title="Coverage Days (Hari)")
        )
        
        st.plotly_chart(fig_coverage, use_container_width=True)
        
    with tab3:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown(f"<h5 style='color:{MEDIUM_GREEN};'>Konsumsi Harian Terkini per Material</h5>", unsafe_allow_html=True)
            # Bar chart for consumption on the selected date
            fig_cons = px.bar(
                df_date_filtered,
                x='Material',
                y='Consumption',
                color='Material',
                color_discrete_map={
                    'Phospat Rock': '#1B332B',
                    'DAP': '#D4AF37',
                    'KCL': '#C5A028'
                },
                labels={'Consumption': 'Konsumsi Harian (ton)'}
            )
            fig_cons.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Material"),
                yaxis=dict(showgrid=True, gridcolor='#ECEFF1')
            )
            st.plotly_chart(fig_cons, use_container_width=True)
            
        with col_c2:
            st.markdown(f"<h5 style='color:{MEDIUM_GREEN};'>Batas Minimum Safety Stock (Hari)</h5>", unsafe_allow_html=True)
            # Safety stock days comparison
            fig_safety = px.bar(
                df_date_filtered,
                x='Material',
                y='Safety Stock (hari)',
                color='Material',
                color_discrete_map={
                    'Phospat Rock': '#1B332B',
                    'DAP': '#D4AF37',
                    'KCL': '#C5A028'
                },
                labels={'Safety Stock (hari)': 'Safety Stock (hari)'}
            )
            fig_safety.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Material"),
                yaxis=dict(showgrid=True, gridcolor='#ECEFF1')
            )
            st.plotly_chart(fig_safety, use_container_width=True)

    # ------------------ RECENT LOGS & WARNING TABLES ------------------
    st.markdown(f"<h3 style='color:{DEEP_GREEN}; margin-top:2rem;'>🛡️ Ringkasan Risiko & Manajemen Safety Stock</h3>", unsafe_allow_html=True)
    
    col_risk1, col_risk2 = st.columns(2)
    
    with col_risk1:
        st.markdown(f"""
        <div style='background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%; border-top: 4px solid {DEEP_GREEN};'>
            <h5 style='color: {DEEP_GREEN}; margin-top: 0;'>💡 Rekomendasi Mitigasi</h5>
            <p style='font-size: 0.95rem; line-height: 1.5;'>
                Sistem mendeteksi deviasi stok antara 100% kedatangan dan 0% kedatangan.
                Jika status pada <b>0% kedatangan</b> berada dalam kondisi <b>Critical</b>, hal ini berarti perusahaan
                sangat bergantung pada kedatangan terjadwal dalam waktu dekat. 
                <br><br>
                <b>Mitigasi yang Disarankan:</b>
                <ul>
                    <li>Pastikan komunikasi intensif dengan pemasok untuk material yang kritis.</li>
                    <li>Evaluasi rute logistik alternatif jika terjadi keterlambatan pengiriman.</li>
                    <li>Gunakan margin cadangan safety stock hari untuk toleransi keterlambatan maksimal.</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_risk2:
        # Show safety stock values table
        st.markdown(f"""
        <div style='background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); height: 100%; border-top: 4px solid {PRIMARY_GOLD};'>
            <h5 style='color: {DEEP_GREEN}; margin-top: 0;'>⚙️ Parameter Batas Aman (Safety Stock)</h5>
            <table style='width: 100%; border-collapse: collapse; margin-top: 0.5rem;'>
                <thead>
                    <tr style='border-bottom: 2px solid {LIGHT_GREEN}; text-align: left; color: #556B5C; font-size: 0.9rem;'>
                        <th style='padding: 8px;'>Material</th>
                        <th style='padding: 8px;'>Batas Tonase</th>
                        <th style='padding: 8px;'>Batas Hari</th>
                        <th style='padding: 8px;'>Konsumsi Aktual</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)
        
        for idx, row in df_date_filtered.iterrows():
            st.markdown(f"""
                    <tr style='border-bottom: 1px solid #ECEFF1; font-size: 0.95rem;'>
                        <td style='padding: 8px; font-weight: bold; color: {DEEP_GREEN};'>{row['Material']}</td>
                        <td style='padding: 8px;'>{row['Safety Stock (tonase)']:,.0f} ton</td>
                        <td style='padding: 8px;'>{row['Safety Stock (hari)']:.0f} hari</td>
                        <td style='padding: 8px;'>{row['Consumption']:,.0f} ton/hari</td>
                    </tr>
            """, unsafe_allow_html=True)
            
        st.markdown("""
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

# Footer info
st.markdown("---")
st.markdown(
    f"<h3 style='color:{DEEP_GREEN};'>📅 Rekapan Monitoring Semua Tanggal</h3>",
    unsafe_allow_html=True
)

summary_df = (
    df_raw
    .groupby("ParsedDate")
    .agg(
        Total_Stok_100=("100% Kedatangan","sum"),
        Total_Stok_0=("0% Kedatangan","sum"),
        Total_Consumption=("Consumption","sum"),
        Avg_Coverage=("Coverage days (0%)","mean"),
        Jumlah_Material=("Material","count")
    )
    .reset_index()
)

summary_df["Tanggal"] = summary_df["ParsedDate"].dt.strftime("%d-%m-%Y")

summary_df = summary_df[
    [
        "Tanggal",
        "Jumlah_Material",
        "Total_Stok_100",
        "Total_Stok_0",
        "Total_Consumption",
        "Avg_Coverage"
    ]
]

st.dataframe(
    summary_df.style.format({
        "Total_Stok_100":"{:,.0f} ton",
        "Total_Stok_0":"{:,.0f} ton",
        "Total_Consumption":"{:,.0f} ton",
        "Avg_Coverage":"{:.1f} hari"
    }),
    use_container_width=True,
    hide_index=True
)

fig = px.line(
    summary_df,
    x="Tanggal",
    y=["Total_Stok_100","Total_Stok_0"],
    markers=True,
    title="Rekapan Total Stock Semua Tanggal"
)

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig, use_container_width=True)