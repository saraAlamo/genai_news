import requests
from typing import Dict, List

TOPIC_MAP = {
    "Deportes": {
        "keywords": ["deporte", "fútbol", "tenis", "baloncesto", "NBA", "gol", "atletismo"]
    },
    "Política": {
        "keywords": ["política", "elecciones", "gobierno", "parlamento", "diputado", "congreso", "presidente"]
    },
    "Economía": {
        "keywords": ["economía", "mercados", "finanzas", "inflación", "PIB", "banca", "hacienda"]
    },
    "Ciencia": {
        "keywords": ["investigación", "científico", "descubrimiento", "espacio", "nasa", "genética"]
    },
    "Tecnología": {
        "keywords": ["tecnología", "Google", "Apple", "IA", "ChatGPT", "software", "móvil"]
    },
    "Cultura": {
        "keywords": ["cine", "teatro", "libro", "música", "literatura", "arte", "exposición"]
    },
    "Salud": {
        "keywords": ["salud", "medicina", "hospital", "vacuna", "virus", "bienestar"]
    },
    "Medio Ambiente": {
        "keywords": ["clima", "cambio climático", "energía renovable", "contaminación", "naturaleza", "ecología"]
    },
}

class NewsRetriever:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://newsapi.org/v2/everything"  # category solo funciona en /top-headlines

    def fetch(self, prefs: Dict, language: str = "es") -> List[Dict]:
        topics = prefs.get("topics") or ["noticias"]
        topic = topics[0]  # solo uno por ahora
        topic_conf = TOPIC_MAP.get(topic, {"keywords": [topic]})

        keywords = topic_conf["keywords"]
        query = " OR ".join(keywords)

        params = {
            "q": query,
            "language": language,
            "sortBy": "relevancy",
            "apiKey": self.api_key
        }

        try:
            resp = requests.get(self.url, params=params, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print("Error en NewsAPI:", e)
            return []

        data = resp.json()
        articles = data.get("articles", [])

        # Filtrado post-fetch para limpiar basura no relacionada
        articles = [
            a for a in articles
            if a.get("title") and a.get("description") and a.get("url")
        ]

        keywords_lower = [k.lower() for k in keywords]
        articles = [
            a for a in articles
            if any(k in (a["title"] + a["description"]).lower() for k in keywords_lower)
        ]

        return articles
