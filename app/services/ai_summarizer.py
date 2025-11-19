import openai
from typing import Optional
from app.core.config import settings


class AISummarizerService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Use mini for cost efficiency

    def summarize_entry(self, entry_text: str, max_words: int = 100) -> Optional[str]:
        """
        Summarize a diary entry to max_words while preserving key information.

        Args:
            entry_text: The full diary entry text
            max_words: Maximum words in the summary (default: 100)

        Returns:
            Summary string or None if summarization fails
        """
        try:
            if len(entry_text) < max_words:
                return entry_text

            prompt = self._create_summarization_prompt(entry_text, max_words)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise, meaningful summaries of diary entries. You preserve the emotional tone, key events, and important details while making the summary clear and readable. Always respond in the same language as the diary entry.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=200,  # Enough for ~100 word summary
            )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            print(f"Error summarizing entry: {e}")
            return None

    def _create_summarization_prompt(self, entry_text: str, max_words: int) -> str:
        """Create the summarization prompt"""
        prompt = f"""Summarize the following diary entry in approximately {max_words} words.

Diary Entry:
{entry_text}

Instructions:
- Create a concise summary that captures the essence of this diary entry
- Preserve the emotional tone and mood (positive, negative, neutral, mixed)
- Include key events, experiences, or thoughts mentioned
- Maintain important details about relationships, activities, or significant moments
- Keep the summary natural and readable, as if you're describing the entry to someone
- Write in the same language as the diary entry
- Focus on what makes this entry unique or meaningful
- If the entry is very short (less than {max_words} words), you may return a slightly condensed version

Summary (approximately {max_words} words):"""

        return prompt


ai_summarizer_service = AISummarizerService()
