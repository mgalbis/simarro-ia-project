from pathlib import Path
import zipfile

import pandas as pd
from ydata_profiling import ProfileReport


# =========================
# CONFIGURACIÓN
# =========================

ZIP_PATH = Path("UCI_Occupancy_Detection.zip")
OUTPUT_DIR = Path("outputs/eda_uci_occupancy")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INNER_ZIP_NAME = "UCI_Occupancy_Detection/occupancy_detection.zip"


# =========================
# FUNCIONES
# =========================

def read_uci_occupancy_from_zip(zip_path: Path) -> dict[str, pd.DataFrame]:
    """
    Lee el dataset UCI Occupancy Detection desde el ZIP proporcionado.

    El ZIP contiene otro ZIP interno con:
    - datatraining.txt
    - datatest.txt
    - datatest2.txt
    """

    if not zip_path.exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {zip_path}")

    dataframes = {}

    with zipfile.ZipFile(zip_path, "r") as outer_zip:
        with outer_zip.open(INNER_ZIP_NAME) as inner_zip_file:
            with zipfile.ZipFile(inner_zip_file, "r") as inner_zip:
                for filename in ["datatraining.txt", "datatest.txt", "datatest2.txt"]:
                    with inner_zip.open(filename) as file:
                        df = pd.read_csv(file)

                    df = clean_uci_dataframe(df)
                    dataframes[filename.replace(".txt", "")] = df

    return dataframes


def clean_uci_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza mínima del dataset:
    - Elimina columna índice si aparece como 'Unnamed: 0'
    - Convierte date a datetime
    - Ordena temporalmente
    """

    df = df.copy()

    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade variables temporales útiles para el análisis exploratorio.
    """

    df = df.copy()

    df["hour"] = df["date"].dt.hour
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    return df


def create_profile_report(df: pd.DataFrame, title: str, output_path: Path) -> None:
    """
    Genera un informe HTML de Auto-EDA.
    """

    profile = ProfileReport(
        df,
        title=title,
        explorative=True,
        correlations={
            "pearson": {"calculate": True},
            "spearman": {"calculate": True},
            "kendall": {"calculate": False},
            "phi_k": {"calculate": False},
            "cramers": {"calculate": False},
        },
        missing_diagrams={
            "bar": True,
            "matrix": True,
            "heatmap": False,
            "dendrogram": False,
        },
    )

    profile.to_file(output_path)
    print(f"Informe generado: {output_path}")


# =========================
# PROCESO PRINCIPAL
# =========================

def main() -> None:
    datasets = read_uci_occupancy_from_zip(ZIP_PATH)

    training = datasets["datatraining"]
    test1 = datasets["datatest"]
    test2 = datasets["datatest2"]

    # Añadimos columna para saber de qué partición viene cada fila
    training["split"] = "train"
    test1["split"] = "test1"
    test2["split"] = "test2"

    full_df = pd.concat([training, test1, test2], ignore_index=True)
    full_df = add_time_features(full_df)

    # Guardamos CSV limpio para próximos notebooks/modelos
    clean_csv_path = OUTPUT_DIR / "uci_occupancy_clean.csv"
    full_df.to_csv(clean_csv_path, index=False)
    print(f"CSV limpio generado: {clean_csv_path}")

    # Informe global
    create_profile_report(
        df=full_df,
        title="Auto-EDA - UCI Occupancy Detection - Dataset completo",
        output_path=OUTPUT_DIR / "eda_uci_occupancy_full.html",
    )

    # Informe solo entrenamiento
    create_profile_report(
        df=add_time_features(training),
        title="Auto-EDA - UCI Occupancy Detection - Training",
        output_path=OUTPUT_DIR / "eda_uci_occupancy_training.html",
    )

    # Resumen rápido por consola
    print("\nColumnas:")
    print(full_df.columns.tolist())

    print("\nDimensiones:")
    print(full_df.shape)

    print("\nBalance de clases Occupancy:")
    print(full_df["Occupancy"].value_counts())
    print(full_df["Occupancy"].value_counts(normalize=True).round(4))

    print("\nNulos por columna:")
    print(full_df.isna().sum())


if __name__ == "__main__":
    main()
