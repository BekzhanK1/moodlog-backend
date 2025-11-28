import openai
import json
from typing import Dict, Any, List
from app.core.config import settings


class CharacteristicGeneratorService:
    """Service to generate user characteristics based on their diary entries"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Use mini for cost efficiency

    def generate_characteristics(
        self, entries: List[str], mood_ratings: List[float], tags: List[List[str]]
    ) -> Dict[str, Any]:
        """
        Generate user characteristics based on diary entries.

        Args:
            entries: List of entry contents (decrypted)
            mood_ratings: List of mood ratings for each entry
            tags: List of tags for each entry

        Returns:
            Dictionary with characteristics sections
        """
        try:
            if not entries:
                return self._get_default_characteristics()

            # Calculate average mood
            avg_mood = sum(mood_ratings) / len(mood_ratings) if mood_ratings else 0.0

            # Collect all unique tags
            all_tags = set()
            for tag_list in tags:
                if tag_list:
                    all_tags.update(tag_list)

            # Prepare entries text (limit to last 20 entries, 300 chars each)
            entries_text = "\n\n---\n\n".join(
                [
                    f"Запись {i+1}:\n{entry[:300]}"
                    for i, entry in enumerate(entries[:20])
                ]
            )

            prompt = self._create_characteristics_prompt(
                entries_text, avg_mood, list(all_tags)[:10]
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a psychological analyst helping to understand a person through their diary entries. "
                            "Generate insightful, supportive characteristics based on their writing. "
                            "Always respond in Russian. Be empathetic and constructive. "
                            "Respond ONLY with valid JSON, no additional text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content.strip()
            characteristics = json.loads(result_text)

            # Ensure all required fields are present
            return self._validate_and_complete_characteristics(
                characteristics, avg_mood, list(all_tags)
            )

        except Exception as e:
            print(f"Error generating characteristics: {e}")
            import traceback

            traceback.print_exc()
            return self._get_default_characteristics()

    def _create_characteristics_prompt(
        self, entries_text: str, avg_mood: float, tags: List[str]
    ) -> str:
        """Create a prompt for generating characteristics"""
        mood_label = self._get_mood_label(avg_mood)

        return (
            f"Проанализируй дневниковые записи пользователя и создай характеристику в формате JSON.\n\n"
            f"Среднее настроение: {avg_mood:.2f} ({mood_label})\n"
            f"Основные теги: {', '.join(tags[:10]) if tags else 'нет'}\n\n"
            f"Записи:\n{entries_text}\n\n"
            f"Верни JSON объект со следующей структурой:\n"
            f"{{\n"
            f'  "general_description": "Подробное описание личности и стиля ведения дневника (5-8 предложений, минимум 100 слов). Опиши характерные черты, мотивы, стиль мышления и особенности рефлексии автора.",\n'
            f'  "main_themes": ["тема1", "тема2", "тема3", "тема4"],\n'
            f'  "emotional_profile": {{\n'
            f'    "average_mood": {avg_mood:.2f},\n'
            f'    "dominant_emotions": ["эмоция1", "эмоция2", "эмоция3"],\n'
            f'    "emotional_range": "Низкий/Умеренный/Широкий"\n'
            f"  }},\n"
            f'  "writing_style": {{\n'
            f'    "average_length": "Короткий/Средний/Длинный",\n'
            f'    "tone": "Описание тона письма",\n'
            f'    "common_patterns": ["паттерн1", "паттерн2", "паттерн3"]\n'
            f"  }}\n"
            f"}}\n\n"
            f"Важно: все тексты должны быть на русском языке."
        )

    def _get_mood_label(self, mood: float) -> str:
        """Get mood label based on rating"""
        if mood >= 0.5:
            return "Очень позитивное"
        elif mood >= 0:
            return "Позитивное"
        elif mood >= -0.5:
            return "Нейтральное"
        else:
            return "Негативное"

    def _validate_and_complete_characteristics(
        self, characteristics: Dict[str, Any], avg_mood: float, tags: List[str]
    ) -> Dict[str, Any]:
        """Validate and complete characteristics with defaults if needed"""
        default = self._get_default_characteristics()

        result = {
            "general_description": characteristics.get("general_description")
            or default["general_description"],
            "main_themes": characteristics.get("main_themes")
            or (tags[:4] if tags else default["main_themes"]),
            "emotional_profile": {
                "average_mood": avg_mood,
                "dominant_emotions": (
                    characteristics.get("emotional_profile", {}).get(
                        "dominant_emotions"
                    )
                    or default["emotional_profile"]["dominant_emotions"]
                ),
                "emotional_range": (
                    characteristics.get("emotional_profile", {}).get("emotional_range")
                    or default["emotional_profile"]["emotional_range"]
                ),
            },
            "writing_style": {
                "average_length": (
                    characteristics.get("writing_style", {}).get("average_length")
                    or default["writing_style"]["average_length"]
                ),
                "tone": (
                    characteristics.get("writing_style", {}).get("tone")
                    or default["writing_style"]["tone"]
                ),
                "common_patterns": (
                    characteristics.get("writing_style", {}).get("common_patterns")
                    or default["writing_style"]["common_patterns"]
                ),
            },
        }

        return result

    def _get_default_characteristics(self) -> Dict[str, Any]:
        """Get default characteristics when no entries available"""
        return {
            "general_description": "Начните вести дневник, и здесь появится ваша характеристика.",
            "main_themes": [],
            "emotional_profile": {
                "average_mood": 0.0,
                "dominant_emotions": [],
                "emotional_range": "Не определено",
            },
            "writing_style": {
                "average_length": "Не определено",
                "tone": "Не определено",
                "common_patterns": [],
            },
        }
