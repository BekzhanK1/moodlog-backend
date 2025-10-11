from app.services.sentiment_service import MultilingualSentimentAnalyzer
from app.services.theme_extraction_service import theme_extraction_service


class MoodAnalysisService:
    """Complete mood analysis service combining sentiment and theme extraction"""
    
    def __init__(self):
        self.sentiment_analyzer = MultilingualSentimentAnalyzer()
        self.theme_extractor = theme_extraction_service
    
    def analyze_entry(self, content: str) -> dict:
        """Complete analysis: sentiment + themes"""
        try:
            # Analyze sentiment
            mood_rating = self.sentiment_analyzer.analyze_sentiment_sync(content)
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            mood_rating = 0.0  # Default neutral mood
        
        # Extract themes
        themes = self.theme_extractor.extract_themes(content)
        
        return {
            "mood_rating": mood_rating,
            "tags": themes
        }


# Services are now created lazily when needed
# No global instances to avoid slow module loading