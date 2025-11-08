import openai
import json
from typing import List
from app.core.config import settings


class ThemeExtractionService:
    def __init__(self):
        """Initialize OpenAI client for theme extraction"""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"

    def lowercase_list(self, list: List[str]) -> List[str]:
        return [item.lower() for item in list]

    def extract_themes(self, text: str, max_themes: int = None, min_similarity: float = 0.3) -> List[str]:
        """Extract themes from diary entry text using OpenAI LLM"""
        # Dynamically determine max_themes based on text length
        if max_themes is None:
            word_count = len(text.split())
            if word_count <= 20:  # Short text
                max_themes = 2
            elif word_count <= 50:  # Medium text
                max_themes = 3
            else:  # Long text
                max_themes = 4

        try:
            # Use OpenAI to extract themes
            themes = self._extract_themes_with_openai(text, max_themes)
            if themes:
                return themes
            else:
                return []

        except Exception as e:
            print(f"Error in theme extraction: {e}")
            return []

    def _extract_themes_with_openai(self, text: str, max_themes: int) -> List[str]:
        """Extract themes from text using OpenAI LLM - generates themes freely"""
        try:
            # Create a prompt for theme extraction
            prompt = f"""Analyze the following diary entry and extract the most relevant themes.
                        Diary entry:
                        {text}

                        Instructions:
                        - Extract exactly {max_themes} themes that best represent the main topics, emotions, or subjects in this diary entry
                        - Generate concise, descriptive theme names (1-3 words each)
                        - Themes can be in any language that matches the diary entry's language
                        - Focus on the most important and relevant themes
                        - Consider emotions, activities, relationships, topics, and experiences mentioned
                        - Return themes as a JSON array of strings

                        Return your response as a JSON object with this structure:
                        {{
                        "themes": ["theme1", "theme2", ...]
                        }}

                        Make sure to return exactly {max_themes} themes."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts themes from diary entries in any language. Always respond with valid JSON. Generate themes that match the language of the diary entry."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.5,  # Slightly higher for more creative theme generation
                max_tokens=300
            )

            # Parse the response
            response_content = response.choices[0].message.content
            result = json.loads(response_content)

            themes = result.get("themes", [])

            themes = self.lowercase_list(themes)

            # Ensure themes are strings and limit to max_themes
            valid_themes = [str(theme).strip()
                            for theme in themes if theme and str(theme).strip()]

            # Limit to max_themes
            return self.lowercase_list(valid_themes[:max_themes])

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response from OpenAI: {e}")
            return []
        except Exception as e:
            print(
                f"Error extracting themes with OpenAI for text '{text[:50]}...': {e}")
            return []


theme_extraction_service = ThemeExtractionService()
