import requests
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

HF_TOKEN = settings.hf_token


class ThemeExtractionService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
        }
        
        # Predefined theme categories for mood logs with descriptions
        self.theme_categories = {
            "work": "work, job, career, office, meeting, project, deadline, boss, colleague, presentation, task",
            "family": "family, mom, dad, parent, sibling, brother, sister, relatives, home, household",
            "health": "health, exercise, gym, workout, running, yoga, diet, doctor, medicine, fitness, illness",
            "travel": "travel, vacation, trip, holiday, flight, hotel, sightseeing, adventure, journey, destination",
            "food": "food, restaurant, cooking, recipe, dinner, lunch, breakfast, meal, cuisine, eating",
            "relationships": "relationship, boyfriend, girlfriend, partner, ex, dating, love, breakup, marriage, couple, romance",
            "social": "friend, friends, social, party, hangout, gathering, community, networking, socializing",
            "hobby": "hobby, music, movie, book, game, art, photo, craft, sport, entertainment, leisure",
            "stress": "stress, anxiety, worry, tired, exhausted, overwhelmed, pressure, tense, nervous",
            "happy": "happy, excited, grateful, proud, accomplished, relaxed, joyful, cheerful, content",
            "learning": "study, learning, school, university, exam, test, course, skill, education, knowledge",
            "money": "money, finance, budget, expense, cost, salary, investment, shopping, purchase",
            "sleep": "sleep, rest, tired, exhausted, insomnia, nap, bedtime, dream, fatigue",
            "nature": "nature, outdoor, park, beach, mountain, weather, sunshine, rain, environment",
            "technology": "technology, computer, phone, internet, app, software, gadget, digital, online",
            "reflection": "reflection, thinking, meditation, mindfulness, personal growth, self-improvement, goals",
            "emotional": "emotional, feelings, hurt, pain, manipulation, toxic, healing, self-respect, boundaries",
            "personal": "personal, self, myself, growth, change, improvement, healing, self-care, boundaries"
        }
    
    def extract_themes(self, text: str, max_themes: int = None, min_similarity: float = 0.3) -> List[str]:
        """Extract themes from diary entry text using semantic similarity"""
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
            # Get embedding for the diary entry
            entry_embedding = self._get_embedding(text)
            if not entry_embedding:
                return self._fallback_keyword_extraction(text, max_themes)
            
            # Calculate similarities with theme categories
            theme_scores = []
            for theme, description in self.theme_categories.items():
                theme_embedding = self._get_embedding(description)
                if theme_embedding:
                    similarity = cosine_similarity([entry_embedding], [theme_embedding])[0][0]
                    theme_scores.append((theme, similarity))
            
            # Sort by similarity and filter by minimum threshold
            theme_scores.sort(key=lambda x: x[1], reverse=True)
            
            selected_themes = []
            for theme, score in theme_scores:
                if score >= min_similarity and len(selected_themes) < max_themes:
                    selected_themes.append(theme)
            
            # If no themes meet the threshold, use fallback
            if not selected_themes:
                return self._fallback_keyword_extraction(text, max_themes)
            
            return selected_themes
            
        except Exception as e:
            print(f"Error in theme extraction: {e}")
            return self._fallback_keyword_extraction(text, max_themes)
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text using Hugging Face API"""
        try:
            response = requests.post(
                API_URL, 
                headers=self.headers, 
                json={"inputs": text},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting embedding for text '{text[:50]}...': {e}")
            return []
    
    def _fallback_keyword_extraction(self, text: str, max_themes: int = 5) -> List[str]:
        """Enhanced fallback method using keyword extraction with theme mapping"""
        import re
        from collections import Counter
        
        # Common stop words
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 
            'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 
            'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 
            'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after', 'above', 
            'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 
            'very', 's', 't', 'can', 'will', 'just', 'should', 'now', 'today', 'yesterday', 'tomorrow'
        }
        
        # Clean and tokenize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter meaningful words
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        # Count word frequency
        word_counts = Counter(meaningful_words)
        
        # Map keywords to theme categories
        keyword_to_theme = {
            # Work related
            'work': 'work', 'job': 'work', 'career': 'work', 'office': 'work', 'meeting': 'work',
            'project': 'work', 'deadline': 'work', 'boss': 'work', 'colleague': 'work', 'presentation': 'work',
            'task': 'work', 'business': 'work', 'company': 'work', 'interview': 'work',
            
            # Family related
            'family': 'family', 'mom': 'family', 'dad': 'family', 'parent': 'family', 'sibling': 'family',
            'brother': 'family', 'sister': 'family', 'relatives': 'family', 'home': 'family', 'household': 'family',
            
            # Health related
            'health': 'health', 'exercise': 'health', 'gym': 'health', 'workout': 'health', 'running': 'health',
            'yoga': 'health', 'diet': 'health', 'doctor': 'health', 'medicine': 'health', 'fitness': 'health',
            'illness': 'health', 'sick': 'health', 'pain': 'health', 'hospital': 'health',
            
            # Travel related
            'travel': 'travel', 'vacation': 'travel', 'trip': 'travel', 'holiday': 'travel', 'flight': 'travel',
            'hotel': 'travel', 'sightseeing': 'travel', 'adventure': 'travel', 'journey': 'travel', 'destination': 'travel',
            
            # Food related
            'food': 'food', 'restaurant': 'food', 'cooking': 'food', 'recipe': 'food', 'dinner': 'food',
            'lunch': 'food', 'breakfast': 'food', 'meal': 'food', 'cuisine': 'food', 'eating': 'food',
            
            # Relationships related
            'relationship': 'relationships', 'boyfriend': 'relationships', 'girlfriend': 'relationships', 
            'partner': 'relationships', 'ex': 'relationships', 'dating': 'relationships', 'love': 'relationships',
            'breakup': 'relationships', 'marriage': 'relationships', 'couple': 'relationships', 'romance': 'relationships',
            'cheating': 'relationships', 'cheat': 'relationships', 'manipulation': 'relationships', 'manipulate': 'relationships',
            'manipulative': 'relationships', 'toxic': 'relationships', 'respect': 'relationships', 'boundaries': 'relationships',
            
            # Social related
            'friend': 'social', 'friends': 'social', 'social': 'social', 'party': 'social', 'hangout': 'social',
            'gathering': 'social', 'community': 'social', 'networking': 'social', 'socializing': 'social',
            
            # Hobby related
            'hobby': 'hobby', 'music': 'hobby', 'movie': 'hobby', 'book': 'hobby', 'game': 'hobby',
            'art': 'hobby', 'photo': 'hobby', 'craft': 'hobby', 'sport': 'hobby', 'entertainment': 'hobby',
            'leisure': 'hobby', 'reading': 'hobby', 'writing': 'hobby', 'drawing': 'hobby',
            
            # Stress related
            'stress': 'stress', 'anxiety': 'stress', 'worry': 'stress', 'tired': 'stress', 'exhausted': 'stress',
            'overwhelmed': 'stress', 'pressure': 'stress', 'tense': 'stress', 'nervous': 'stress',
            
            # Happy related
            'happy': 'happy', 'excited': 'happy', 'grateful': 'happy', 'proud': 'happy', 'accomplished': 'happy',
            'relaxed': 'happy', 'joyful': 'happy', 'cheerful': 'happy', 'content': 'happy', 'great': 'happy',
            'amazing': 'happy', 'wonderful': 'happy', 'fantastic': 'happy',
            
            # Learning related
            'study': 'learning', 'learning': 'learning', 'school': 'learning', 'university': 'learning',
            'exam': 'learning', 'test': 'learning', 'course': 'learning', 'skill': 'learning', 'education': 'learning',
            'knowledge': 'learning', 'class': 'learning', 'lesson': 'learning',
            
            # Money related
            'money': 'money', 'finance': 'money', 'budget': 'money', 'expense': 'money', 'cost': 'money',
            'salary': 'money', 'investment': 'money', 'shopping': 'money', 'purchase': 'money', 'buy': 'money',
            
            # Sleep related
            'sleep': 'sleep', 'rest': 'sleep', 'tired': 'sleep', 'exhausted': 'sleep', 'insomnia': 'sleep',
            'nap': 'sleep', 'bedtime': 'sleep', 'dream': 'sleep', 'fatigue': 'sleep',
            
            # Nature related
            'nature': 'nature', 'outdoor': 'nature', 'park': 'nature', 'beach': 'nature', 'mountain': 'nature',
            'weather': 'nature', 'sunshine': 'nature', 'rain': 'nature', 'environment': 'nature',
            
            # Technology related
            'technology': 'technology', 'computer': 'technology', 'phone': 'technology', 'internet': 'technology',
            'app': 'technology', 'software': 'technology', 'gadget': 'technology', 'digital': 'technology', 'online': 'technology',
            
            # Emotional related
            'emotional': 'emotional', 'feelings': 'emotional', 'hurt': 'emotional', 'pain': 'emotional',
            'healing': 'emotional', 'self-respect': 'emotional', 'self': 'emotional', 'myself': 'emotional',
            'heal': 'emotional', 'fix': 'emotional', 'cycle': 'emotional', 'backwards': 'emotional',
            'chapter': 'emotional', 'story': 'emotional', 'ending': 'emotional',
            
            # Personal growth related
            'personal': 'personal', 'growth': 'personal', 'change': 'personal', 'improvement': 'personal',
            'self-care': 'personal', 'goals': 'personal', 'reflection': 'personal', 'thinking': 'personal',
            'meditation': 'personal', 'mindfulness': 'personal',
            
            # Russian keywords
            'работа': 'work', 'работе': 'work', 'рабочий': 'work', 'офис': 'work', 'проект': 'work', 'работать': 'work',
            'семья': 'family', 'мама': 'family', 'папа': 'family', 'родители': 'family', 'брат': 'family', 'сестра': 'family',
            'здоровье': 'health', 'спорт': 'health', 'тренировка': 'health', 'бег': 'health', 'йога': 'health', 'зал': 'health',
            'путешествие': 'travel', 'отпуск': 'travel', 'поездка': 'travel', 'полет': 'travel', 'отель': 'travel', 'путешествовать': 'travel',
            'еда': 'food', 'ресторан': 'food', 'готовка': 'food', 'ужин': 'food', 'обед': 'food', 'завтрак': 'food', 'готовить': 'food',
            'отношения': 'relationships', 'парень': 'relationships', 'девушка': 'relationships', 'любовь': 'relationships',
            'расставание': 'relationships', 'измена': 'relationships', 'манипуляция': 'relationships', 'любить': 'relationships',
            'друзья': 'social', 'друг': 'social', 'вечеринка': 'social', 'встреча': 'social', 'встретился': 'social', 'встретиться': 'social',
            'хобби': 'hobby', 'музыка': 'hobby', 'фильм': 'hobby', 'книга': 'hobby', 'игра': 'hobby', 'слушать': 'hobby',
            'стресс': 'stress', 'тревога': 'stress', 'беспокойство': 'stress', 'усталость': 'stress', 'устал': 'stress', 'устала': 'stress',
            'счастье': 'happy', 'радость': 'happy', 'гордость': 'happy', 'благодарность': 'happy', 'весело': 'happy', 'радостно': 'happy',
            'учёба': 'learning', 'школа': 'learning', 'университет': 'learning', 'экзамен': 'learning', 'учиться': 'learning',
            'деньги': 'money', 'финансы': 'money', 'покупка': 'money', 'зарплата': 'money', 'покупать': 'money',
            'сон': 'sleep', 'отдых': 'sleep', 'усталость': 'sleep', 'бессонница': 'sleep', 'спать': 'sleep',
            'природа': 'nature', 'парк': 'nature', 'пляж': 'nature', 'погода': 'nature', 'солнце': 'nature',
            'технологии': 'technology', 'компьютер': 'technology', 'телефон': 'technology', 'интернет': 'technology', 'приложение': 'technology',
            'эмоции': 'emotional', 'чувства': 'emotional', 'боль': 'emotional', 'исцеление': 'emotional', 'чувствовать': 'emotional',
            'личность': 'personal', 'рост': 'personal', 'изменения': 'personal', 'цели': 'personal', 'личный': 'personal'
        }
        
        # Extract themes based on keyword mapping
        theme_counts = Counter()
        for word, count in word_counts.items():
            if word in keyword_to_theme:
                theme_counts[keyword_to_theme[word]] += count
        
        # Get themes from mapping
        themes = []
        for theme, count in theme_counts.most_common(max_themes):
            themes.append(theme)
        
        # If not enough themes from mapping, add top keywords
        if len(themes) < max_themes:
            for word, count in word_counts.most_common(max_themes * 2):
                if word not in keyword_to_theme and len(word) > 3:
                    themes.append(word)
                    if len(themes) >= max_themes:
                        break
        
        return themes[:max_themes]
    
    def get_theme_similarity_scores(self, text: str) -> Dict[str, float]:
        """Get similarity scores for all theme categories (useful for debugging)"""
        try:
            entry_embedding = self._get_embedding(text)
            if not entry_embedding:
                return {}
            
            scores = {}
            for theme, description in self.theme_categories.items():
                theme_embedding = self._get_embedding(description)
                if theme_embedding:
                    similarity = cosine_similarity([entry_embedding], [theme_embedding])[0][0]
                    scores[theme] = similarity
            
            return scores
        except Exception as e:
            print(f"Error getting similarity scores: {e}")
            return {}


# Global instance
theme_extraction_service = ThemeExtractionService()