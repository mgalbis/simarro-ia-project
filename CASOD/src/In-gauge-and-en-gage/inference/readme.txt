cd "C:\RUTA_FICHERO_python"
pip install -r requirements.txt
python .\infer_classroom_occupancy_json.py


El script busca automáticamente cualquier modelo que empiece con:
best_*.joblib

La salida se va a mostrar por pantalla y además se guardará en:
inference_results_classroom.csv
