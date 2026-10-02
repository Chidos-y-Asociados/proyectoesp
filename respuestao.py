import requests

def preguntar_a_ollama(prompt):
    respuesta = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=30,
    )
    datos = respuesta.json()
    return datos["response"]

if __name__ == "__main__":
    print(preguntar_a_ollama("Responde solo con 'ok' si me escuchas."))