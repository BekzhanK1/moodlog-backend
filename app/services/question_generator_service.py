import openai
from typing import List
from app.core.config import settings


class QuestionGeneratorService:
    """Service to generate therapist-like questions based on recent entries"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Use mini for cost efficiency

    def generate_questions(
        self, recent_entries: List[str], max_entries: int = 5, num_questions: int = 3
    ) -> List[str]:
        """
        Generate multiple contextual, therapist-like questions based on recent entries.

        Args:
            recent_entries: List of recent entry contents (decrypted)
            max_entries: Maximum number of entries to analyze (default: 5)
            num_questions: Number of questions to generate (default: 3)

        Returns:
            A list of question strings in Russian
        """
        try:
            if not recent_entries:
                # Default questions if no entries
                return [
                    "О чем вы думали в последнее время?",
                    "Что вас сейчас волнует?",
                    "Как вы себя чувствуете сегодня?",
                ]

            # Limit to last N entries
            entries_to_analyze = recent_entries[:max_entries]

            prompt = self._create_questions_prompt(entries_to_analyze, num_questions)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a supportive, empathetic therapist helping someone with their journaling. "
                            "Generate thoughtful, open-ended questions that encourage reflection and self-exploration. "
                            "Questions should be warm, non-judgmental, and help the person explore their thoughts and feelings. "
                            "Always respond in Russian. Keep questions concise (one sentence, max 15 words). "
                            "Make questions feel personal and relevant to what they've been writing about recently. "
                            "Each question should be different and explore different aspects of their experience."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Slightly creative but still focused
                max_tokens=200,
            )

            questions_text = response.choices[0].message.content.strip()

            # Parse questions - they might be separated by newlines, numbers, or bullets
            questions = []
            for line in questions_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Remove numbering (1., 2., etc.) or bullets (-, •, etc.)
                line = line.lstrip("0123456789.-•) ")
                # Remove quotes if present
                line = line.strip('"').strip("'").strip()
                if line and line.endswith("?"):
                    questions.append(line)

            # If we didn't get enough questions, add defaults
            if len(questions) < num_questions:
                default_questions = [
                    "О чем вы думали в последнее время?",
                    "Что вас сейчас волнует?",
                    "Как вы себя чувствуете сегодня?",
                ]
                questions.extend(default_questions[: num_questions - len(questions)])

            return questions[:num_questions]  # Return only requested number

        except Exception as e:
            print(f"Error generating questions: {e}")
            # Fallback to default questions
            return [
                "О чем вы думали в последнее время?",
                "Что вас сейчас волнует?",
                "Как вы себя чувствуете сегодня?",
            ]

    def _create_questions_prompt(self, entries: List[str], num_questions: int) -> str:
        """Create a prompt for generating multiple contextual questions"""
        entries_text = "\n\n---\n\n".join(
            [
                f"Запись {i+1}:\n{entry[:500]}"  # Limit each entry to 500 chars
                for i, entry in enumerate(entries)
            ]
        )

        return (
            f"Проанализируй последние записи пользователя и создай {num_questions} разных вопроса, "
            f"которые помогут ему продолжить размышления. Каждый вопрос должен быть:\n"
            f"- Контекстуальным (связанным с тем, о чем он писал)\n"
            f"- Поддерживающим и эмпатичным\n"
            f"- Открытым (не требующим ответа да/нет)\n"
            f"- Побуждающим к саморефлексии\n"
            f"- Кратким (одно предложение, максимум 15 слов)\n"
            f"- Уникальным (каждый вопрос должен исследовать разные аспекты)\n\n"
            f"Если записи очень разные по темам, задай вопросы о разных аспектах его жизни. "
            f"Если есть повторяющиеся темы, задай вопросы, которые углубляют эту тему с разных сторон.\n\n"
            f"Последние записи:\n{entries_text}\n\n"
            f"Верни {num_questions} вопроса, каждый на отдельной строке, без нумерации и дополнительного текста:"
        )
