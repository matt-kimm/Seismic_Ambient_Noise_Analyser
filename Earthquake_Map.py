import json
import folium
import pandas as pd

# --- 1. ЗАГРУЗКА ВСЕХ ДАННЫХ ---
# 1.1. Разломы (GeoJSON)
with open("D:\data\MAP\ActiveFault.geojson", "r", encoding="utf-8") as f:
    faults_data = json.load(f)

# 1.2. Исторические землетрясения (GeoJSON)
with open("D:\data\MAP\Earthquakes_old.geojson", "r", encoding="utf-8") as f:
    earthquakes_data = json.load(f)

# 1.3. Новые землетрясения (CSV со скриншота)
# Читаем файл, автоматически заменяя запятые в числах на точки
df_new_eq = pd.read_csv("C:/Users/matve/OneDrive/Desktop/earthquakes.csv", sep=None, engine="python")

# 1.4. Станции наблюдения (CSV со скриншота)
df_stations = pd.read_csv(r"D:\data\MAP\points.csv", sep=None, engine="python")
df_stations.columns = df_stations.columns.str.strip()

# Очищаем названия колонок от лишних пробелов, если они есть
df_new_eq.columns = df_new_eq.columns.str.strip()

# Принудительно конвертируем координаты и класс K в числа, заменяя запятые на точки
for col in ["lat", "lon", "K"]:
    if col in df_new_eq.columns and df_new_eq[col].dtype == "object":
        df_new_eq[col] = df_new_eq[col].astype(str).str.replace(",", ".").astype(float)


# --- 2. ФУНКЦИИ СТИЛИЗАЦИИ ---
def get_fault_color(activity):
    if not activity:
        return "#7f8c8d"
    activity = activity.lower()
    if "аномально высокая" in activity:
        return "#d63031"
    elif "высокая" in activity:
        return "#e17055"
    elif "умеренная" in activity or "средняя" in activity:
        return "#fdcb6e"
    else:
        return "#fffff"


def style_faults(feature):
    activity_degree = feature["properties"].get("Activity_degree", "")
    return {
        "color": get_fault_color(activity_degree),
        "weight": 3,
        "opacity": 0.75,
    }


def get_eq_color(ms):
    if ms >= 7.0:
        return "#FF0000"  # Яркий бардовый для катастрофических
    elif ms >= 5.5:
        return "#FF0000"  # Крансый для сильных
    elif ms >= 4.0:
        return "#FF0000"  # Темно оранжевый для ощутимых
    else:
        return "#FF0000"  # Оранжевй для слабых микроземлетрясений


# --- 3. ИНИЦИАЛИЗАЦИЯ КАРТЫ ---
m = folium.Map(location=[53.5, 106.0], zoom_start=6, tiles="OpenStreetMap")

# --- 4. ДОБАВЛЕНИЕ СЛОЯ РАЗЛОМОВ ---
faults_group = folium.FeatureGroup(name="Активные разломы").add_to(m)
folium.GeoJson(
    faults_data,
    style_function=style_faults,
    popup=folium.GeoJsonPopup(
        fields=["Name", "Activity_degree", "Slip_sense", "Potential_Ms_max"],
        aliases=["Разлом:", "Активность:", "Смещение:", "Потенц. Ms:"],
        localize=True,
    ),
).add_to(faults_group)


# --- 6. ДОБАВЛЕНИЕ СЛОЯ СОВРЕМЕННЫХ ЗЕМЛЕТРЯСЕНИЙ (CSV) ---
eq_csv_group = folium.FeatureGroup(
    name="Землетрясения из CSV (2020 г.)"
).add_to(m)

# Предполагаем, что первая колонка без названия содержит дату/время
date_col = df_new_eq.columns[0]

for idx, row in df_new_eq.iterrows():
    lat = row["lat"]
    lon = row["lon"]
    k_val = row["K"]

    # Перевод энергетического класса K в магнитуду Ms по формуле Раутиан
    ms_converted = round((k_val - 4.6) / 1.5, 1)

    # Задаем базовый радиус (не меньше 3 пикселей для слабых толчков)
    radius = max(ms_converted * 2.5, 3)

    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 12px; min-width: 180px;">
        <b>Дата/Время:</b> {row[date_col]}<br>
        <b>Класс K:</b> {k_val}<br>
        <b>Расчетная магнитуда Ms:</b> {ms_converted}<br>
        <b>Координаты:</b> {lat}, {lon}
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

# --- 8. СЛОЙ 4: СТАНЦИИ НАБЛЮДЕНИЯ (Новый CSV) ---
stations_group = folium.FeatureGroup(name="Научные станции").add_to(m)

for idx, row in df_stations.iterrows():
    lat = row['lat']
    lon = row['lon']
    name = row.get('name', 'Без названия')
    alias = row.get('alias', '-')
    methods = row.get('methods', 'Не указаны')
    
    # Заменяем значение NaN (если ячейка пустая), чтобы на карте отображалось корректно
    if pd.isna(alias) or alias == "": alias = "-"
    if pd.isna(methods) or methods == "": methods = "Не указаны"
    
    popup_html = f"""
    <div style="font-family: sans-serif; font-size: 12px; min-width: 200px;">
        <h4 style="margin: 0 0 5px 0; color: #2980b9;">Станция: {name}</h4>
        <b>Сокращение (Alias):</b> {alias}<br>
        <b>Методы исследований:</b> {methods}<br>
        <b>Координаты:</b> {lat}, {lon}
    </div>
    """
    
    # Добавляем маркер в виде классической синей булавки
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300),
        # Добавляем постоянную текстовую подсказку, которая видна сразу без клика
        tooltip=folium.Tooltip(f"Станция {name}", sticky=True),
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(stations_group)

# --- 7. ИНТЕРФЕЙС И ОКОНЧАТЕЛЬНАЯ ЛЕГЕНДА ---
folium.LayerControl(position="topright").add_to(m)

legend_html = """
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 260px; height: 230px; 
     border:2px solid grey; z-index:9999; font-size:12px;
     background-color:white; opacity: 0.95; padding: 10px; font-family: sans-serif;">
     
     <b>Активность разломов (линии):</b><br>
     <span style="color:#d63031; font-weight:bold;">―</span> Аномально высокая<br>
     <span style="color:#e17055; font-weight:bold;">―</span> Высокая<br>
     <span style="color:#fdcb6e; font-weight:bold;">―</span> Умеренная / Средняя<br>
     <br>
     <b>Землетрясения (круги):</b><br>
     <span style="display:inline-block; width:12px; height:12px; background:#FF0000; border-radius:50%;"></span> Сильнейшие (Ms &ge; 7.0 / K &ge; 15)<br>
     <span style="display:inline-block; width:10px; height:10px; background:#FF0000; border-radius:50%;"></span> Сильные (Ms 5.5-6.9 / K 13-14)<br>
     <span style="display:inline-block; width:8px; height:8px; background:#FF0000; border-radius:50%;"></span> Ощутимые (Ms 4.0-5.4 / K 11-12)<br>
     <span style="display:inline-block; width:6px; height:6px; background:#FF0000; border-radius:50%;"></span> Слабые (Ms &lt; 4.0 / K &lt; 11)<br>
     <small style="color:gray;">*Размер круга зависит от магнитуды</small>
     </div>
     """
m.get_root().html.add_child(folium.Element(legend_html))



# --- 8. СОХРАНЕНИЕ ---
m.save("tectonics_and_all_earthquakes.html")

# Отображаем в Jupyter
m
