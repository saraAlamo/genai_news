from typing import Dict, Tuple
from vertexai.preview.generative_models import GenerativeModel

class NewsTransformer:
    def __init__(self, model: GenerativeModel):
        self.model = model

    def _build_prompt(self, article: Dict, prefs: Dict) -> str:
        description = article.get("description", "")
        base = f"Transforma esta noticia manteniendo los hechos clave:\n\n{description.strip()}"

        if prefs.get("tones"):
            base += f"\n\nTono: {', '.join(prefs['tones'])}."
        if prefs.get("formats"):
            base += f"\nFormato: {', '.join(prefs['formats'])}."
        if prefs.get("ideology"):
            base += f"\nPerspectiva política: {', '.join(prefs['ideology'])}."

        base += "\nHazlo en español y evita titulares sensacionalistas si no se ha pedido explícitamente."
        return base

    def transform(self, article: Dict, prefs: Dict) -> Tuple[str, str]:
        prompt = self._build_prompt(article, prefs)
        print(prompt)
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
            }
        )
        transformed_text = response.text

        image_prompt = ""
        if prefs.get("suggest_image"):
            image_prompt = f"Prompt de imagen basado en: {transformed_text[:200]}..."

        return transformed_text, image_prompt
