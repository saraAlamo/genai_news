import os
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
# --- Nuevas importaciones para los modelos generativos de Vertex AI ---
import vertexai
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

# --- Configuración de Vertex AI (IA Generativa) ---
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
REGION = os.getenv('GCP_REGION')

vertexai.init(project=PROJECT_ID, location=REGION) # <-- ¡Aquí el cambio!
GENERATIVE_MODEL = GenerativeModel("gemini-pro") # <-- ¡Aquí también!
# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    """
    Ruta principal que sirve el archivo HTML de la interfaz.
    """
    return render_template('index.html')

@app.route('/get_news', methods=['POST'])
def get_news():
    """
    Ruta para obtener noticias de la API pública.
    """
    data = request.json
    query = data.get('query', 'inteligencia artificial') # Término de búsqueda por defecto
    language = data.get('language', 'es') # Idioma por defecto

    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'language': language,
        'sortBy': 'relevancy'
    }
    
    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status() # Lanza una excepción para errores HTTP
        news_data = response.json()
        articles = news_data.get('articles', [])
        
        # Filtramos solo los campos relevantes para simplificar
        simplified_articles = []
        for article in articles:
            simplified_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'url': article.get('url')
            })
        
        return jsonify({'success': True, 'articles': simplified_articles})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f"Error al obtener noticias: {e}"}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error inesperado: {e}"}), 500


@app.route('/transform_text', methods=['POST'])
def transform_text():
    """
    Ruta para transformar texto usando el modelo de IA generativa de Vertex AI.
    """
    data = request.json
    text_to_transform = data.get('text')
    transformation_prompt = data.get('prompt', 'Reescribe este texto de forma más creativa.')

    if not text_to_transform:
        return jsonify({'success': False, 'message': 'No se proporcionó texto para transformar.'}), 400

    try:
        # Aquí es donde se le da la instrucción al modelo de IA
        # El 'prompt' incluye la instrucción y el texto a transformar
        prompt_content = f"{transformation_prompt}\n\nTexto:\n{text_to_transform}"
        
        # Generar contenido usando el modelo
        # Ajusta generation_config según tus necesidades (temperatura, etc.)
        response = GENERATIVE_MODEL.generate_content(
            prompt_content,
            generation_config={"temperature": 0.7, "max_output_tokens": 1024}
        )
        
        # La respuesta puede venir en bloques, los unimos
        transformed_text = "".join([part.text for part in response.candidates[0].content.parts])
        
        return jsonify({'success': True, 'transformed_text': transformed_text})

    except Exception as e:
        # Manejo de errores de la API de Vertex AI (cuotas, errores del modelo, etc.)
        print(f"Error al transformar texto con IAG: {e}")
        return jsonify({'success': False, 'message': f"Error al transformar texto: {e}"}), 500

# --- Ejecutar la aplicación ---
if __name__ == '__main__':
    # Esto es solo para pruebas locales. En App Engine, Gunicorn ejecutará la aplicación.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

