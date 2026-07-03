from kedro.pipeline import Pipeline, node, pipeline
from .nodes import preparar_datos_ml, entrenar_modelo, evaluar_modelo

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=preparar_datos_ml,
                inputs=["demo_raw", "bpx_raw", "bmx_raw"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="preparar_datos_ml_node",
            ),
            node(
                func=entrenar_modelo,
                inputs=["X_train", "y_train"],
                outputs="modelo_hipertension",
                name="entrenar_modelo_node",
            ),
            node(
                func=evaluar_modelo,
                inputs=["modelo_hipertension", "X_test", "y_test"],
                outputs=None,
                name="evaluar_modelo_node",
            ),
        ]
    )