from datetime import date, datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from sqlmodel import Session
from app.crud import entry as entry_crud


class AnalyticsService:

    def get_data_points_for_mood_trend(
        self,
        session: Session,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        # Offset in hours (e.g., 5 for UTC+5)
        user_timezone_offset: Optional[int] = None,
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
                data_points.append(
                    {
                        "date": day,
                        "mood_rating": round(avg_rating, 2),
                        "num_entries": data.get("num_entries", 0),
                    }
                )
        return data_points

    def get_main_themes(
        self,
        session: Session,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
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
            result.append(
                {
                    "tag": tag,
                    "frequency": frequency,
                    "relative_percentage": relative_percentage,
                }
            )
        return result[:5]

    def _sort_entries_by_mood_rating(self, entries):
        sorted_entries = sorted(
            entries,
            key=lambda x: x.mood_rating if x.mood_rating is not None else 0,
            reverse=True,
        )
        return sorted_entries

    def get_best_and_worst_entries_by_mood_rating(
        self,
        session: Session,
        user_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        entries = entry_crud.get_entries_by_date_range(
            session=session, user_id=user_id, start_date=start_date, end_date=end_date
        )

        if not entries:
            return []

        sorted_entries = self._sort_entries_by_mood_rating(entries)
        best_entry = sorted_entries[0]
        worst_entry = sorted_entries[-1]

        return {
            "best_entry": {
                "id": best_entry.id,
                "mood_rating": best_entry.mood_rating,
                "tags": best_entry.tags,
                "created_at": best_entry.created_at,
                "updated_at": best_entry.updated_at,
                "ai_processed_at": best_entry.ai_processed_at,
            },
            "worst_entry": {
                "id": worst_entry.id,
                "mood_rating": worst_entry.mood_rating,
                "tags": worst_entry.tags,
                "created_at": worst_entry.created_at,
                "updated_at": worst_entry.updated_at,
                "ai_processed_at": worst_entry.ai_processed_at,
            },
        }

    def compare_current_and_previous_month_mood_rating(
        self, session: Session, user_id: UUID
    ):
        now = datetime.now()
        current_month = now.month
        current_year = now.year

        previous_month, previous_year = self._get_previous_month_and_year(
            current_month, current_year
        )

        start_date, end_date = self._get_month_date_range(current_year, current_month)
        previous_start_date, previous_end_date = self._get_month_date_range(
            previous_year, previous_month
        )

        current_entries = self._get_valid_entries_for_month(
            session, user_id, start_date, end_date
        )
        previous_entries = self._get_valid_entries_for_month(
            session, user_id, previous_start_date, previous_end_date
        )

        current_mood_rating = self._calculate_average_mood_rating(current_entries)
        previous_mood_rating = self._calculate_average_mood_rating(previous_entries)

        mood_rating_difference = None
        if current_mood_rating is not None and previous_mood_rating is not None:
            mood_rating_difference = current_mood_rating - previous_mood_rating

        return {
            "current_mood_rating": (
                round(current_mood_rating, 2)
                if current_mood_rating is not None
                else None
            ),
            "previous_mood_rating": (
                round(previous_mood_rating, 2)
                if previous_mood_rating is not None
                else None
            ),
            "mood_rating_difference": (
                round(mood_rating_difference, 2)
                if mood_rating_difference is not None
                else None
            ),
        }

    def _get_previous_month_and_year(self, current_month, current_year):
        if current_month == 1:
            return 12, current_year - 1
        else:
            return current_month - 1, current_year

    def _get_month_date_range(self, year, month):
        import calendar

        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        return start_date, end_date

    def _get_valid_entries_for_month(self, session, user_id, start_date, end_date):
        entries = entry_crud.get_entries_by_date_range(
            session=session, user_id=user_id, start_date=start_date, end_date=end_date
        )
        valid_entries = [
            entry
            for entry in entries
            if entry.mood_rating is not None and not entry.is_draft
        ]
        return valid_entries

    def _calculate_average_mood_rating(self, entries):
        if not entries:
            return None
        return sum(entry.mood_rating for entry in entries) / len(entries)


analytics_service = AnalyticsService()
