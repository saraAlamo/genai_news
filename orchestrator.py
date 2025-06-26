# backend/orchestrator.py
from typing import Dict, List
from agents.news_retriever import NewsRetriever
from agents.news_transformer import NewsTransformer

class Orchestrator:
    """
    Junta varios agentes en un único punto de entrada:
    1. Recupera noticias.
    2. Las transforma según preferencias.
    Retorna una lista de dicts con {title, url, transformed_text, image_prompt?}.
    """

    def __init__(self, news_api_key: str, generative_model):
        self.retriever = NewsRetriever(news_api_key)
        self.transformer = NewsTransformer(generative_model)

    def run(self, preferences: Dict, language: str = "es") -> List[Dict]:
        # 1. Buscar en NewsAPI
        raw_articles = self.retriever.fetch(preferences, language)

        # 2. Transformar cada artículo (puedes paralelizar más adelante)
        transformed = []
        for art in raw_articles[:2]:
            transformed_text, image_prompt = self.transformer.transform(
                art, preferences
            )
            art["transformed_text"] = transformed_text
            print(transformed_text)
            if image_prompt:
                art["image_prompt"] = image_prompt
            transformed.append(art)

        return transformed
