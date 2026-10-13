# Interactive Tectonic & Seismic Activity Map

An interactive web map built with **Python**, **Folium**, and **Plotly** designed to visualize active geological faults, historical and modern earthquake data, and scientific observation stations with integrated **Power Spectral Density (PSD)** analysis.

## 🌟 Features

- **Active Faults Layer:** Visualizes geological fault lines color-coded by their activity degree (from moderate to abnormally high) with detailed popups.
- **Seismic Catalog Visualization:** Plots modern earthquake events from CSV data, dynamically scaling the markers based on the energy class (\(K\)-class) converted to Richter magnitude (\(M_s\)) using the Rautian formula.
- **Scientific Stations & PSD Analysis:** Displays observation stations with interactive popups containing a time-series seismogram and its corresponding **Power Spectral Density (PSD)** spectrum computed via Welch's method.
- **Layer Control & Interactive Legend:** Easily toggle layers on/off and view a clean, styled map legend.

## 🛠️ Requirements

Make sure you have the following Python packages installed:

```bash
pip install pandas numpy scipy folium plotly openpyxl
```

## 📂 Data Structure

The script expects the following local files and paths (update them in the code if needed):
- `D:\data\MAP\ActiveFault.geojson` — GeoJSON file containing fault geometries and `Activity_degree` properties.
- `D:\data\MAP\earthquakes.csv` — CSV file with columns: `lat`, `lon`, `K`, and a timestamp column.
- `D:\data\MAP\points.csv` — CSV file containing observation stations with fields: `lat`, `lon`, `name`, `alias`, and `methods`.

## 🚀 Usage

Simply run the main Python script:

```bash
python main.py
```

This will generate an interactive HTML file named `tectonics_and_all_earthquakes.html` in your working directory. You can open it in any modern web browser or display it directly inside a Jupyter Notebook (`m`).

## 📊 Scientific Methodology

1. **Magnitude Conversion:** Modern earthquake energy classes (\(K\)) are converted to \(M_s\) using the standard seismological equation:
   \[M_s = \frac{K - 4.6}{1.5}\]
2. **Spectral Analysis:** The Power Spectral Density (PSD) is calculated using **Welch's method** (`scipy.signal.welch`) to analyze the signal's dominant frequencies in the frequency domain, with power expressed in decibels (\(dB/Hz\)).
