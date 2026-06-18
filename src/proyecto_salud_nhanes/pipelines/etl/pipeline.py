from kedro.pipeline import Pipeline, node, pipeline
from .nodes import fetch_weather_api, leer_base_sql

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=fetch_weather_api,
                inputs=None,
                outputs="clima_api_intermediate",
                name="obtener_datos_clima_node",
            ),
            node(
                func=leer_base_sql,
                inputs=None,
                outputs="categorias_sql_intermediate",
                name="leer_sql_node",
            )
        ]
    )