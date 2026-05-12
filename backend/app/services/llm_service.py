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
    Eres un orquestador QA. Tu objetivo es mapear el mensaje del usuario a acciones técnicas.
    
    Acciones disponibles:
    - check_nulls (si pide analizar vacíos o nulos)
    - check_duplicates (si pide analizar repetidos)
    
    Mensaje: "{message}"
    
    Responde ESTRICTAMENTE en JSON con este formato:
    {{
        "intent": "run_validation",
        "actions": ["check_nulls", "check_duplicates"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } 
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error IA Local: {e}")
        return {"intent": "run_validation", "actions": ["check_nulls", "check_duplicates"]}