import requests
from app.core.config import settings
from app.services.theme_extraction_service import theme_extraction_service

API_URL = "https://router.huggingface.co/hf-inference/models/tabularisai/multilingual-sentiment-analysis"

HF_TOKEN = settings.hf_token


class MultilingualSentimentAnalyzer:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
        }

    def mood_rating_from_prediction(self, prediction: list) -> float:
        weights = {
            "Very Negative": -2,
            "Negative": -1,
            "Neutral": 0,
            "Positive": 1,
            "Very Positive": 2,
        }

        if isinstance(prediction, list) and isinstance(prediction[0], list):
            prediction = prediction[0]

        mood_score = sum(weights[item["label"]] * item["score"]
                         for item in prediction)
        return round(mood_score, 3)

    def analyze_sentiment_sync(self, text: str) -> float:
        """Analyze sentiment of text synchronously"""
        response = requests.post(
            API_URL, headers=self.headers, json={"inputs": text})
        response.raise_for_status()
        return self.mood_rating_from_prediction(response.json())
