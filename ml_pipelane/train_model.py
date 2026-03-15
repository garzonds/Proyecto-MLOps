from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from preprocess import load_data, preprocess_data
from model_utils import save_model_local, upload_model_to_minio


def train():
    print("Cargando datos desde PostgreSQL...")
    df = load_data()

    print(f"Filas cargadas: {len(df)}")

    print("Preprocesando datos...")
    X, y, df_processed = preprocess_data(df)

    print(f"Shape X: {X.shape}")
    print(f"Shape y: {y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Entrenando modelo...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    print("Evaluando modelo...")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred))

    print("Guardando modelo localmente...")
    model_path = save_model_local(model, "model.joblib")

    print("Subiendo modelo a MinIO...")
    result = upload_model_to_minio(
        model_path=model_path,
        bucket_name="models",
        object_name="forest_model.joblib"
    )

    print("Modelo subido correctamente:")
    print(result)


if __name__ == "__main__":
    train()
