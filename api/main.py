from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import pandas as pd
import os

# Creamos la API con documentación automática
app = FastAPI(
    title="API Predictiva NHANES",
    description="Servicio REST para predecir riesgo de hipertensión usando Machine Learning.",
    version="1.0.0"
)

# Ruta relativa para encontrar el modelo que Kedro guardó
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "data", "06_models", "modelo_final.pkl")
# Cargamos el modelo a la memoria
with open(MODEL_PATH, "rb") as f:
    modelo = pickle.load(f)

# Definimos qué datos debe enviarnos el usuario (Esquema de validación)
class Paciente(BaseModel):
    edad: float
    imc: float
    genero: float  # 1.0 para Hombres, 2.0 para Mujeres

@app.get("/")
def home():
    return {"mensaje": "API activa. Visita /docs para ver la documentación interactiva."}

@app.post("/predecir")
def predecir_hipertension(paciente: Paciente):
    """
    Endpoint documentado: Recibe edad, imc y género, y devuelve si hay riesgo de hipertensión.
    """
    # Transformamos el JSON recibido a un formato que el modelo de Pandas entienda
    datos_nuevos = pd.DataFrame([{
        'RIDAGEYR': paciente.edad,
        'BMXBMI': paciente.imc,
        'RIAGENDR': paciente.genero
    }])
    
    # Hacemos la predicción
    prediccion = modelo.predict(datos_nuevos)[0]
    probabilidades = modelo.predict_proba(datos_nuevos)[0]
    
    return {
        "riesgo_hipertension": bool(prediccion == 1),
        "diagnostico": "Alerta: Presión Alta" if prediccion == 1 else "Normal",
        "probabilidad_riesgo": f"{probabilidades[1]:.1%}"
    }