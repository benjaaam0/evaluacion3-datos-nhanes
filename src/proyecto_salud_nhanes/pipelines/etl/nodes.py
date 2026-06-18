import pandas as pd
import requests

def fetch_weather_api() -> pd.DataFrame:
    """
    Consume la API REST de Open-Meteo para obtener datos climáticos 
    y cumple con la Fuente 2 de la rúbrica.
    """
    # Coordenadas de ejemplo (Nueva York, Los Ángeles, Chicago, Miami)
    ciudades = [
        {"ciudad": "New York", "lat": 40.71, "lon": -74.00},
        {"ciudad": "Los Angeles", "lat": 34.05, "lon": -118.24},
        {"ciudad": "Chicago", "lat": 41.87, "lon": -87.62},
        {"ciudad": "Miami", "lat": 25.76, "lon": -80.19}
    ]
    
    clima_data = []
    
    for c in ciudades:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&current_weather=true"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            clima_data.append({
                "ciudad": c["ciudad"],
                "temperatura_actual": data["current_weather"]["temperature"],
                "velocidad_viento": data["current_weather"]["windspeed"]
            })
            
    # Convertimos los datos de la API directamente a un DataFrame de Pandas
    df_clima = pd.DataFrame(clima_data)
    return df_clima

import sqlite3

def leer_base_sql() -> pd.DataFrame:
    """
    Se conecta a la base de datos SQLite y extrae la tabla de categorías,
    cumpliendo con la Fuente 3 de la rúbrica.
    """
    conn = sqlite3.connect("data/01_raw/diccionario_medico.db")
    df_sql = pd.read_sql_query("SELECT * FROM categorias_imc", conn)
    conn.close()
    return df_sql