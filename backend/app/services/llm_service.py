import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

def interpret_user_intent(message: str):
    prompt = f"""
        Eres un intérprete de instrucciones para un sistema de QA de datos.

        Tu única tarea es extraer qué validaciones quiere el usuario y devolver JSON puro.

        Tests disponibles (usa EXACTAMENTE estos valores):
        - "nulls"      → si menciona: nulos, valores vacíos, missings, null, NaN
        - "duplicates" → si menciona: duplicados, repetidos, filas duplicadas
        - "data_types" → si menciona: tipos, formato, columnas, tipo de dato
        - "outliers"   → si menciona: outliers, valores extremos, anomalías, atípicos
        - "balance"    → si menciona: balanceo, desbalanceo, clases, distribución, dataset balanceado, imbalance

        Reglas:
        1. Si pide UN test concreto → pon solo ese en requested_tests.
        2. Si pide VARIOS → ponlos todos.
        3. Si pide "analiza todo" o no especifica → deja requested_tests vacío [].
        4. Si el usuario pide analizar, revisar, validar o comprobar un dataset usa "validate_dataset".
        4. Si el usuario pide descargar/exportar/bajar el informe: intent = "download_report"

        Ejemplos:
        - "revisa nulos"              → requested_tests: ["nulls"]
        - "solo duplicados"           → requested_tests: ["duplicates"]
        - "comprueba nulos y outliers"→ requested_tests: ["nulls", "outliers"]
        - "revisa balanceo"            → requested_tests: ["balance"]
        - "analiza/valida el dataset"        → requested_tests: [], intent: "validate_dataset"
        - "dame el informe"    → requested_tests: [], intent: "download_report"

        Petición del usuario: "{message}"

        Responde ÚNICAMENTE con este JSON, sin explicaciones ni texto extra:
        {{
            "intent": "validate_dataset" o "download_report",
            "requested_tests": [],
            "excluded_columns": [],
            "critical_columns": []
        }}
        """
    try:
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        # Validación defensiva: filtrar valores inválidos que el LLM pueda inventar
        valid_tests = {"nulls", "duplicates", "data_types", "outliers", "balance"}
        result["requested_tests"] = [
            t for t in result.get("requested_tests", [])
            if t in valid_tests
        ]
        return result
        
    except Exception as e:
        print(f"Error IA Local: {e}")
        return {
            "intent": "validate_dataset",
            "requested_tests": [],
            "excluded_columns": [],
            "critical_columns": []
        }