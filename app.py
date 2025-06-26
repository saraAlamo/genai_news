import os
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
from orchestrator import Orchestrator

from vertexai import init as vertex_init
from vertexai.preview.generative_models import GenerativeModel

# Option 1: Access GenerativeModel via preview.models
# This is often the path for the latest generative AI features.
from google.cloud.aiplatform import preview


# --- Configuración de la aplicación Flask ---
app = Flask(__name__)

# --- Cargar variables de entorno desde .env (si existe) ---
load_dotenv()

# --- Configuración de la API de Noticias ---
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = "https://newsapi.org/v2/everything"
print("GOOGLE_APPLICATION_CREDENTIALS =", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

# --- Configuración de Vertex AI (IA Generativa) ---
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
REGION = os.getenv('GCP_REGION')
vertex_init(project=PROJECT_ID, location=REGION)

GENERATIVE_MODEL = GenerativeModel("gemini-2.5-flash")

ORCHESTRATOR = Orchestrator(NEWS_API_KEY, GENERATIVE_MODEL)

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    """
    Ruta principal que sirve el archivo HTML de la interfaz.
    """
    return render_template('index.html')

@app.route('/get_news', methods=['POST'])
def get_news():
    data = request.json
    language = data.get('language', 'es')
    preferences = data.get('preferences', {})
    
    # EXTRAER LOS TEMAS DE INTERÉS DE LAS PREFERENCIAS
    topics = preferences.get('topics', [])
    
    # CONSTRUIR LA CONSULTA (Q) PARA NEWSAPI
    # Si hay temas seleccionados, unirlos con OR
    if topics:
        query_api = " OR ".join(topics)
    else:
        # Si no hay temas seleccionados, usar un tema por defecto (ej. "noticias generales" o "actualidad")
        # Esto es crucial para evitar el error 400 si no se selecciona ningún chip
        query_api = "noticias generales" 
        
    # Puedes añadir lógica para incorporar otras preferencias en la query si NewsAPI lo soporta
    # Por ejemplo, si tuvieras una preferencia de país y NewsAPI lo permitiera:
    # country = preferences.get('country', 'us') # Asumiendo que NewsAPI puede filtrar por país
    
    news_api_url = f"https://newsapi.org/v2/everything?q={query_api}&apiKey={NEWS_API_KEY}&language={language}&sortBy=relevancy"
    
    print(f"DEBUG: Llamando a NewsAPI con URL: {news_api_url}") # Para depuración
    
    try:
        response = requests.get(news_api_url)
        response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        news_data = response.json()
        
        articles = news_data.get('articles', [])
        # Filtrar artículos que no tienen título o descripción
        filtered_articles = [
            a for a in articles 
            if a.get('title') and a.get('description') and a.get('url')
        ]
        
        return jsonify({"success": True, "articles": filtered_articles})
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener noticias de NewsAPI: {e}")
        return jsonify({"success": False, "message": f"Error al obtener noticias: {e}"}), 400
    except Exception as e:
        print(f"Error inesperado en get_news: {e}")
        return jsonify({"success": False, "message": f"Error interno del servidor: {e}"}), 500


# La función transform_text (o process_request en el futuro) también necesitará acceder a 'preferences'
@app.route('/transform_text', methods=['POST'])
def transform_text():
    data = request.json
    text_to_transform = data.get('text')
    preferences = data.get('preferences', {}) # Asegúrate de obtener las preferencias aquí también

    if not text_to_transform:
        return jsonify({"success": False, "message": "No se proporcionó texto para transformar."}), 400

    # Aquí es donde integrarás tu lógica de LLM/Gemini para la transformación
    # y el uso de las 'preferences' para guiar la generación.
    # Por ahora, un ejemplo simple:
    
    # Construir un prompt básico usando las preferencias (EJEMPLO)
    prompt_parts = [f"Transforma la siguiente noticia: '{text_to_transform}'"]
    
    if preferences.get('tones'):
        prompt_parts.append(f"El tono debe ser: {', '.join(preferences['tones'])}.")
    if preferences.get('formats'):
        prompt_parts.append(f"El formato deseado es: {', '.join(preferences['formats'])}.")
    if preferences.get('avoid_sensationalism'):
        prompt_parts.append("Evita cualquier sensacionalismo o lenguaje amarillista.")
    
    final_prompt = " ".join(prompt_parts) + "\n\nNoticia:" # Combina las partes del prompt
    
    # Simula una transformación con un modelo (AQUÍ ES DONDE LLAMARÁS A GEMINI)
    # Por ahora, solo como placeholder:
    transformed_text = f"DEBUG: Texto original: '{text_to_transform}'\nDEBUG: Prompt generado: '{final_prompt}'\n\n[Esta es la noticia transformada con las preferencias.]"
    
    image_prompt = ""
    if preferences.get('suggest_image'):
        image_prompt = "DEBUG: [Prompt sugerido para la imagen basado en la noticia transformada y las preferencias.]" # Lógica para generar el prompt de imagen

    return jsonify({
        "success": True,
        "transformed_text": transformed_text,
        "image_prompt": image_prompt
    })

from orchestrator import Orchestrator                 # NUEVO

# Instancia global
ORCHESTRATOR = Orchestrator(NEWS_API_KEY, GENERATIVE_MODEL)

@app.route("/process_request", methods=["POST"])
def process_request():
    data = request.json
    preferences = data.get("preferences", {})
    language = data.get("language", "es")

    try:
        final_articles = ORCHESTRATOR.run(preferences, language)
        return jsonify({"success": True, "articles": final_articles})
    except Exception as e:
        print("ERROR orchestrator:", e)
        return jsonify({"success": False, "message": str(e)}), 500
@app.route('/get_news_custom', methods=['POST'])
def get_news_custom():
    data = request.json
    prefs = data.get('preferences', {})
    lang = data.get('language', 'es')

    # 1. Buscar noticias crudas
    raw_articles = ORCHESTRATOR.retriever.fetch(prefs, lang)

    # 2. Transformarlas según preferencias
    result = []
    for article in raw_articles[:5]:  # limitamos a 5 para evitar timeout
        transformed, _ = ORCHESTRATOR.transformer.transform(article, prefs)
        result.append({
            "title": article.get("title", "Sin título"),
            "url": article.get("url", ""),
            "transformed_text": transformed
        })

    return jsonify({ "articles": result })

if __name__ == '__main__':
    # Usar el puerto 8080 si está disponible, de lo contrario Flask elegirá otro
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), debug=True)

