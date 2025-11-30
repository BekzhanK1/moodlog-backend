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
                            "You are a supportive, empathetic therapist who has carefully read the user's journal entries. "
                            "Your questions must demonstrate that you have truly read and understood their entries. "
                            "Reference specific details, events, people, places, emotions, or situations mentioned in their writing. "
                            "Questions should be warm, non-judgmental, and show genuine engagement with their content. "
                            "Always respond in Russian. Keep questions concise (one sentence, max 20 words). "
                            "Make each question feel like you're continuing a conversation about something specific they wrote. "
                            "Avoid generic questions - if they mentioned work stress, ask about that specific situation. "
                            "If they wrote about a person, reference that person. If they mentioned a feeling, explore that feeling deeper. "
                            "Each question should reference different specific details from their entries to show you've read everything carefully."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Slightly creative but still focused
                max_tokens=250,  # Increased for more detailed questions
            )

            questions_text = response.choices[0].message.content.strip()
            print(f"Raw AI response: {questions_text}")

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
                # Check if line ends with ? or is a valid question
                if line and (line.endswith("?") or len(line) > 10):
                    questions.append(line)

            print(f"Parsed {len(questions)} questions from AI response: {questions}")

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
                # Limit each entry to 500 chars
                f"Запись {i+1}:\n{entry[:500]}"
                for i, entry in enumerate(entries)
            ]
        )

        return (
            f"Внимательно прочитай следующие записи пользователя. Твоя задача - создать {num_questions} конкретных вопроса, "
            f"которые показывают, что ты действительно прочитал и понял содержание записей.\n\n"
            f"КРИТИЧЕСКИ ВАЖНО: Каждый вопрос ДОЛЖЕН ссылаться на конкретные детали из записей:\n"
            f"- Упоминай конкретные события, ситуации, людей, места, которые были описаны\n"
            f"- Ссылайся на конкретные эмоции, переживания, мысли, которые были выражены\n"
            f"- Используй конкретные темы, проблемы, радости, которые были затронуты\n"
            f"- Покажи, что ты заметил важные детали и хочешь узнать больше именно об этом\n\n"
            f"Примеры ПРАВИЛЬНЫХ вопросов (если в записи упоминалась работа):\n"
            f"✓ 'Как сейчас обстоят дела с тем проектом, о котором вы писали?'\n"
            f"✓ 'Что изменилось в отношениях с коллегой, которого вы упоминали?'\n\n"
            f"Примеры НЕПРАВИЛЬНЫХ (слишком общих) вопросов:\n"
            f"✗ 'Как дела на работе?'\n"
            f"✗ 'Что вас волнует?'\n\n"
            f"Каждый вопрос должен быть:\n"
            f"- Конкретным (ссылаться на детали из записей)\n"
            f"- Поддерживающим и эмпатичным\n"
            f"- Открытым (не требующим ответа да/нет)\n"
            f"- Кратким (одно предложение, максимум 20 слов)\n"
            f"- Уникальным (каждый вопрос о разных конкретных деталях из записей)\n\n"
            f"Последние записи пользователя:\n{entries_text}\n\n"
            f"Создай {num_questions} конкретных вопроса, которые показывают, что ты внимательно прочитал записи. "
            f"Каждый вопрос должен ссылаться на конкретные детали из текста выше. "
            f"Верни только вопросы, каждый на отдельной строке, без нумерации и дополнительного текста:"
        )
