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

Your task is to analyze the sentiment of the provided text and return a precise numerical score.

## Scoring Scale
Return a floating-point number from -2.0 to +2.0:
- **-2.0**: Extremely negative (severe distress, hopelessness, crisis)
- **-1.5**: Very negative (strong sadness, anger, frustration)
- **-1.0**: Moderately negative (disappointment, worry, mild sadness)
- **-0.5**: Slightly negative (minor concerns, subtle unease)
- **0.0**: Neutral (factual, balanced, no strong emotion)
- **+0.5**: Slightly positive (mild contentment, small pleasures)
- **+1.0**: Moderately positive (happiness, satisfaction, gratitude)
- **+1.5**: Very positive (joy, excitement, strong enthusiasm)
- **+2.0**: Extremely positive (elation, profound joy, peak happiness)

## Analysis Guidelines
1. **Language Independence**: Analyze sentiment accurately regardless of the language used
2. **Context Awareness**: Consider the overall tone, not just individual words
3. **Nuance Detection**: Capture subtle emotional expressions and mixed feelings
4. **Cultural Sensitivity**: Account for cultural differences in emotional expression
5. **Precision**: Use decimal values (e.g., -0.7, +1.3) for nuanced assessments

## Response Format
Respond with ONLY a valid JSON object:
{"sentiment_score": <float between -2.0 and 2.0>}"""

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

            return round(sentiment_score, 3)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response from OpenAI: {e}")
            return 0.0  # Return neutral on parse error
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.0  # Return neutral on any error
