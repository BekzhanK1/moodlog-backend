import json
import openai
from app.core.config import settings


class MultilingualSentimentAnalyzer:
    """Sentiment analyzer using GPT-4o-mini for accurate multilingual sentiment analysis"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"

    def _get_system_prompt(self) -> str:
        """
        Create a system prompt using proven prompt engineering techniques:
        - Role assignment (expert sentiment analyst)
        - Clear task definition
        - Output format specification
        - Structured guidelines with examples
        - Calibration anchors for consistent scoring
        """
        return """You are an expert multilingual sentiment analyst specializing in analyzing emotional content from personal diary and journal entries.

Your task is to analyze the sentiment of the provided text and return a precise numerical score with exactly 2 decimal places.

## Scoring Scale
Return a floating-point number from -2.00 to +2.00 with 2 decimal places precision:

**Negative Range (-2.00 to -0.01):**
- -2.00 to -1.75: Extremely negative (severe distress, hopelessness, crisis)
- -1.74 to -1.25: Very negative (strong sadness, anger, frustration)
- -1.24 to -0.75: Moderately negative (disappointment, worry, mild sadness)
- -0.74 to -0.25: Slightly negative (minor concerns, subtle unease)
- -0.24 to -0.01: Barely negative (hint of negativity, minor dissatisfaction)

**Neutral:**
- 0.00: Perfectly neutral (factual, balanced, no emotion)

**Positive Range (+0.01 to +2.00):**
- +0.01 to +0.24: Barely positive (hint of positivity, minor satisfaction)
- +0.25 to +0.74: Slightly positive (mild contentment, small pleasures)
- +0.75 to +1.24: Moderately positive (happiness, satisfaction, gratitude)
- +1.25 to +1.74: Very positive (joy, excitement, strong enthusiasm)
- +1.75 to +2.00: Extremely positive (elation, profound joy, peak happiness)

## Analysis Guidelines
1. **Language Independence**: Analyze sentiment accurately regardless of the language used
2. **Context Awareness**: Consider the overall tone, not just individual words
3. **Nuance Detection**: Capture subtle emotional expressions and mixed feelings
4. **Cultural Sensitivity**: Account for cultural differences in emotional expression
5. **Fine-Grained Precision**: Use the full range of decimal values (e.g., -1.37, +0.82, -0.15, +1.63) to capture nuanced emotional intensity. Avoid rounding to simple increments like 0.5.

## Response Format
Respond with ONLY a valid JSON object containing the score with exactly 2 decimal places:
{"sentiment_score": <float between -2.00 and 2.00 with 2 decimal places>}"""

    def _get_user_prompt(self, text: str) -> str:
        """Create the user prompt with the text to analyze"""
        return f"""Analyze the sentiment of the following diary entry and provide a sentiment score.

Text to analyze:
\"\"\"
{text}
\"\"\"

Return your analysis as a JSON object with the sentiment_score."""

    def analyze_sentiment_sync(self, text: str) -> float:
        """Analyze sentiment of text synchronously using GPT-4o-mini"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._get_user_prompt(text)},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent, deterministic results
                max_tokens=50,  # Only need a small response
            )

            # Parse the JSON response
            response_content = response.choices[0].message.content.strip()
            result = json.loads(response_content)

            # Extract and validate the sentiment score
            raw_score = result.get("sentiment_score")
            if raw_score is None:
                return 0.0

            try:
                sentiment_score = float(raw_score)
            except (ValueError, TypeError):
                print(f"Invalid sentiment_score value: {raw_score}")
                return 0.0

            # Clamp the score to valid range [-2, 2]
            sentiment_score = max(-2.0, min(2.0, sentiment_score))

            return round(sentiment_score, 2)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response from OpenAI: {e}")
            return 0.0  # Return neutral on parse error
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.0  # Return neutral on any error
