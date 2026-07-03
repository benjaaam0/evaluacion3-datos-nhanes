import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

def preparar_datos_ml(demo: pd.DataFrame, bpx: pd.DataFrame, bmx: pd.DataFrame):
    """
    Une los datos raw, limpia los nulos y crea la variable objetivo (Hipertensión).
    """
    # Unir las 3 tablas por el ID del paciente (SEQN)
    df = demo.merge(bpx, on="SEQN", how="inner").merge(bmx, on="SEQN", how="inner")
    
    # Seleccionar columnas clave y limpiar nulos (Técnica de limpieza)
    df = df[['RIDAGEYR', 'BMXBMI', 'BPXSY1', 'RIAGENDR']].dropna()
    
    # Crear variable objetivo: 1 si tiene hipertensión (sistólica >= 130), 0 si es normal
    df['hipertension'] = (df['BPXSY1'] >= 130).astype(int)
    
    # Definir características (X) y objetivo (y)
    X = df[['RIDAGEYR', 'BMXBMI', 'RIAGENDR']] # Edad, IMC y Género
    y = df['hipertension']
    
    # Dividir en datos de entrenamiento (80%) y prueba (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    return X_train, X_test, y_train, y_test


def entrenar_modelo(X_train: pd.DataFrame, y_train: pd.Series):
    """
    Entrena un modelo de clasificación Random Forest.
    """
    # Inicializar el modelo con hiperparámetros
    modelo_rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    modelo_rf.fit(X_train, y_train)
    
    return modelo_rf


def evaluar_modelo(modelo, X_test: pd.DataFrame, y_test: pd.Series):
    """
    Evalúa el modelo y muestra las métricas en la consola.
    """
    y_pred = modelo.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    reporte = classification_report(y_test, y_pred)
    
    logger = logging.getLogger(__name__)
    logger.info(f"🎯 Exactitud (Accuracy) del Modelo: {accuracy:.2f}")
    logger.info(f"📊 Reporte de Clasificación:\n{reporte}")