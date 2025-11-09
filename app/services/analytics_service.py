
from datetime import date, timezone, timedelta
from typing import Optional
from uuid import UUID
from sqlmodel import Session
from app.core.crypto import decrypt_data
from app.crud import entry as entry_crud


class AnalyticsService:
    def __init__(self):
        pass

    def get_data_points_for_mood_trend(
        self,
        session: Session,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        # Offset in hours (e.g., 5 for UTC+5)
        user_timezone_offset: Optional[int] = None
    ):
        entries = entry_crud.get_entries_by_date_range(
            session, user_id=user_id, start_date=start_date, end_date=end_date
        )

        if not entries:
            return []

        user_tz = self._get_user_timezone(user_timezone_offset)
        daily_ratings = self._group_entries_by_local_date(entries, user_tz)
        data_points = self._prepare_mood_trend_data_points(daily_ratings)
        return data_points

    def _get_user_timezone(self, user_timezone_offset: Optional[int]):
        if user_timezone_offset is not None:
            return timezone(timedelta(hours=user_timezone_offset))
        return None

    def _group_entries_by_local_date(self, entries, user_tz):
        daily_ratings = {}
        for entry in entries:
            if entry.mood_rating is None or entry.is_draft:
                continue

            entry_dt = (
                entry.created_at.replace(tzinfo=timezone.utc)
                if entry.created_at.tzinfo is None
                else entry.created_at
            )

            local_dt = entry_dt.astimezone(user_tz) if user_tz else entry_dt
            date_key = local_dt.date().isoformat()
            if date_key not in daily_ratings:
                daily_ratings[date_key] = {
                    "mood_ratings": [],
                    "num_entries": 0,
                }
            daily_ratings[date_key]["mood_ratings"].append(entry.mood_rating)
            daily_ratings[date_key]["num_entries"] += 1
        return daily_ratings

    def _prepare_mood_trend_data_points(self, daily_ratings):
        data_points = []
        for day, data in sorted(daily_ratings.items()):
            ratings = data.get("mood_ratings", [])
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                data_points.append({
                    "date": day,
                    "mood_rating": round(avg_rating, 2),
                    "num_entries": data.get("num_entries", 0),
                })
        return data_points

    def get_main_themes(self, session: Session, user_id: UUID, start_date: Optional[date] = None, end_date: Optional[date] = None):
        entries = entry_crud.get_entries_by_date_range(
            session, user_id=user_id, start_date=start_date, end_date=end_date
        )

        if not entries:
            return []

        main_themes = self._get_main_themes(entries)
        return main_themes

    def _get_main_themes(self, entries):
        themes = {}
        total_tags = 0
        for entry in entries:
            if entry.tags is not None:
                for tag in entry.tags:
                    themes[tag] = themes.get(tag, 0) + 1
                    total_tags += 1

        # Avoid division by zero
        if total_tags == 0:
            return []

        # Prepare list of dicts with frequency and relative percentage
        result = []
        for tag, frequency in sorted(themes.items(), key=lambda x: x[1], reverse=True):
            relative_percentage = int(round((frequency / total_tags) * 100))
            result.append({
                "tag": tag,
                "frequency": frequency,
                "relative_percentage": relative_percentage
            })
        return result[:5]
