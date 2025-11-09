import openai
from app.core.config import settings


class AIInsightsService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.mini_model = "gpt-4o-mini"
        self.pro_model = "gpt-4o"


ai_insights_service = AIInsightsService()
