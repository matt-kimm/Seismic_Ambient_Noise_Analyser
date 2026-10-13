import json
import folium
import pandas as pd
import numpy as np
import scipy.signal as signal
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. DATA LOADING & CONFIG ---
with open(r"D:\data\MAP\ActiveFault.geojson", "r", encoding="utf-8") as f:
    faults_data = json.load(f)

df_new_eq = pd.read_csv("C:/Users/matve/OneDrive/Desktop/earthquakes.csv", sep=None, engine="python")
df_stations = pd.read_csv(r"D:\data\MAP\points.csv", sep=None, engine="python")

df_stations.columns = df_stations.columns.str.strip()
df_new_eq.columns = df_new_eq.columns.str.strip()

for col in ["lat", "lon", "K"]:
    if col in df_new_eq.columns and df_new_eq[col].dtype == "object":
        df_new_eq[col] = df_new_eq[col].astype(str).str.replace(",", ".").astype(float)


# --- 2. SEISMIC SIGNAL & PSD ANALYSIS GENERATION ---
def generate_psd_analysis_html():
    """
    Генерирует интерактивный график сейсмограммы и PSD анализа.
    В реальном сценарии сюда передаются загруженные данные прибора (time, amplitude).
    """
    # Создаем синтетический сейсмический сигнал (частота дискретизации 100 Гц, 10 секунд)
    fs = 100.0  
    t = np.arange(0, 10, 1/fs)
    
    # Моделируем затухающую волну (P/S) + фоновый микросейсмический шум
    signal_wave = 5.0 * np.exp(-1.5 * t) * np.sin(2 * np.pi * 5.0 * t)  # Основной толчок на 5 Гц
    signal_wave += 2.0 * np.exp(-0.5 * t) * np.sin(2 * np.pi * 12.0 * t) # Высокочастотный резонанс 12 Гц
    noise = np.random.normal(0, 0.3, size=len(t))                     # Белый шум
    seismogram = signal_wave + noise

    # Расчет Спектра плотности мощности (PSD) методом Велча
    frequencies, psd = signal.welch(seismogram, fs, nperseg=256)

    # Построение интерактивного графика с помощью Plotly
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Seismogram (Time Series)", "Power Spectral Density (PSD)"))
    
    # 1. Временной сигнал
    fig.add_trace(go.Scatter(x=t, y=seismogram, mode='lines', name='Amplitude', line=dict(color='#2c3e50')), row=1, col=1)
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="Velocity (counts)", row=1, col=1)
    
    # 2. График PSD
    fig.add_trace(go.Scatter(x=frequencies, y=10 * np.log10(psd), mode='lines', name='PSD', line=dict(color='#e74c3c')), row=2, col=1)
    fig.update_xaxes(title_text="Frequency (Hz)", row=2, col=1)
    fig.update_yaxes(title_text="Power (dB/Hz)", row=2, col=1)
    
    fig.update_layout(height=450, width=550, showlegend=False, title_text="Seismic Signal PSD Analysis", title_x=0.5)
    
    # Конвертируем график во встраиваемый HTML-код
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


# --- 3. STYLING FUNCTIONS ---
def get_fault_color(activity):
    if not activity: return "#7f8c8d"
    activity = activity.lower()
    if "аномально высокая" in activity or "abnormally high" in activity: return "#d63031"
    elif "высокая" in activity or "high" in activity: return "#e17055"
    elif "умеренная" in activity or "средняя" in activity or "moderate" in activity or "medium" in activity: return "#fdcb6e"
    else: return "#7f8c8d"

def style_faults(feature):
    return {"color": get_fault_color(feature["properties"].get("Activity_degree", "")), "weight": 3, "opacity": 0.75}

def get_eq_color(ms):
    if ms >= 7.0: return "#FF0000"
    elif ms >= 5.5: return "#FF4500"
    elif ms >= 4.0: return "#FF8C00"
    else: return "#FFA500"


# --- 4. MAP INITIALIZATION ---
m = folium.Map(location=[53.5, 106.0], zoom_start=6, tiles="OpenStreetMap")


# --- 5. FAULTS LAYER ---
faults_group = folium.FeatureGroup(name="Active Faults").add_to(m)
folium.GeoJson(
    faults_data,
    style_function=style_faults,
    popup=folium.GeoJsonPopup(
        fields=["Name", "Activity_degree", "Slip_sense", "Potential_Ms_max"],
        aliases=["Fault Name:", "Activity Degree:", "Slip Sense:", "Potential Ms max:"],
        localize=True,
    ),
).add_to(faults_group)


# --- 6. MODERN EARTHQUAKES LAYER (CSV) ---
eq_csv_group = folium.FeatureGroup(name="Earthquakes from CSV (2020)").add_to(m)
date_col = df_new_eq.columns[0]

for idx, row in df_new_eq.iterrows():
    lat, lon, k_val = row["lat"], row["lon"], row["K"]
    ms_converted = round((k_val - 4.6) / 1.5, 1)
    radius = max(ms_converted * 2.5, 3)
    
    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 12px; min-width: 180px;">
        <b>Date/Time:</b> {row[date_col]}<br>
        <b>Class K:</b> {k_val}<br>
        <b>Calculated Ms:</b> {ms_converted}<br>
        <b>Coordinates:</b> {lat}, {lon}
    </div>
    """
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        fill=True,
        color=get_eq_color(ms_converted),
        fill_color=get_eq_color(ms_converted),
        fill_opacity=0.7,
        weight=1.2,
        popup=folium.Popup(popup_html, max_width=300),
    ).add_to(eq_csv_group)


# --- 7. OBSERVATION STATIONS LAYER (С графиками PSD в Popup) ---
stations_group = folium.FeatureGroup(name="Scientific Stations").add_to(m)

# Генерируем HTML-код анализа (в продакшене можно генерировать уникальный для каждой станции)
psd_chart_html = generate_psd_analysis_html()

for idx, row in df_stations.iterrows():
    lat, lon = row['lat'], row['lon']
    name = row.get('name', 'Unnamed')
    alias = row.get('alias', '-') if not pd.isna(row.get('alias')) else "-"
    methods = row.get('methods', 'Not specified') if not pd.isna(row.get('methods')) else "Not specified"
        
    # Объединяем метаданные станции и интерактивный PSD график в один Popup
    station_popup_html = f"""
    <div style="font-family: sans-serif; font-size: 12px; width: 560px;">
        <h4 style="margin: 0 0 5px 0; color: #2980b9;">Station: {name}</h4>
        <b>Alias:</b> {alias} | <b>Research Methods:</b> {methods}<br>
        <b>Coordinates:</b> {lat}, {lon}
        <hr style="border: 0; border-top: 1px solid #ccc; margin: 10px 0;">
        {psd_chart_html}
    </div>
    """
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(station_popup_html, max_width=600),
        tooltip=folium.Tooltip(f"Station: {name} (Click for PSD Analysis)", sticky=True),
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(stations_group)


# --- 8. INTERFACE AND LEGEND ---
folium.LayerControl(position="topright").add_to(m)

legend_html = """
<div style="position: fixed; bottom: 50px; left: 50px; width: 260px; height: 230px; border:2px solid grey; z-index:9999; font-size:12px; background-color:white; opacity: 0.95; padding: 10px; font-family: sans-serif;">
    <b>Fault Activity (lines):</b><br>
    <span style="color:#d63031; font-weight:bold;">―</span> Abnormally High<br>
    <span style="color:#e17055; font-weight:bold;">―</span> High<br>
    <span style="color:#fdcb6e; font-weight:bold;">―</span> Moderate / Medium<br>
    <br>
    <b>Earthquakes (circles):</b><br>
    <span style="display:inline-block; width:12px; height:12px; background:#FF0000; border-radius:50%;"></span> Great (Ms &ge; 7.0 / K &ge; 15)<br>
    <span style="display:inline-block; width:10px; height:10px; background:#FF4500; border-radius:50%;"></span> Strong (Ms 5.5-6.9 / K 13-14)<br>
    <span style="display:inline-block; width:8px; height:8px; background:#FF8C00; border-radius:50%;"></span> Moderate (Ms 4.0-5.4 / K 11-12)<br>
    <span style="display:inline-block; width:6px; height:6px; background:#FFA500; border-radius:50%;"></span> Weak (Ms &lt; 4.0 / K &lt; 11)<br>
    <small style="color:gray;">*Circle size depends on magnitude</small>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# --- 9. SAVE ---
m.save("tectonics_and_all_earthquakes.html")
