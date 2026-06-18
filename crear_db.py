import sqlite3
import pandas as pd

# 1. Creamos y nos conectamos a la base de datos SQLite
conn = sqlite3.connect("data/01_raw/diccionario_medico.db")

# 2. Inventamos nuestra tabla de categorías médicas
data = {
    "id_categoria": [1, 2, 3, 4],
    "categoria_imc": ["Bajo peso", "Normal", "Sobrepeso", "Obesidad"],
    "imc_min": [0.0, 18.5, 25.0, 30.0],
    "imc_max": [18.4, 24.9, 29.9, 100.0]
}
df_categorias = pd.DataFrame(data)

# 3. Guardamos la tabla dentro de la base de datos SQL
df_categorias.to_sql("categorias_imc", conn, if_exists="replace", index=False)
conn.close()

print("¡Base de datos SQL creada con éxito!")