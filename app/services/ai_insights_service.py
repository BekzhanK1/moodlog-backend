from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
import openai
from sqlmodel import Session
from app.core.config import settings
from app.models.entry import Entry
from app.crud import entry as entry_crud
from app.crud import insight as insight_crud
from app.services.encryption_key_service import get_user_data_key
from app.core.crypto import encrypt_data, decrypt_data
import calendar
import json


class AIInsightsService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.mini_model = "gpt-4o-mini"
        self.pro_model = "gpt-4o"

    def generate_monthly_insights_report(
        self,
        session: Session,
        user_id: UUID,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        use_pro_model: bool = True,
    ) -> Optional[str]:
        now = datetime.now()
        year = target_year or now.year
        month = target_month or now.month
        start_date, end_date = self._get_month_date_range(year, month)
        entries = entry_crud.get_entries_by_date_range(
            session=session, user_id=user_id, start_date=start_date, end_date=end_date
        )
        if not entries:
            return None
        valid_entries = [e for e in entries if not e.is_draft]
        if not valid_entries:
            return None
        # Decrypt entries before generating insights
        data_key = get_user_data_key(session, user_id=user_id)
        insights_text = self._generate_monthly_insights(
            valid_entries, year, month, use_pro_model, data_key
        )
        if not insights_text:
            return None
        period_key = f"{year}-{month:02d}"
        period_label = f"{calendar.month_name[month]} {year}"
        # Encrypt content before saving (data_key already retrieved above)
        encrypted_content = encrypt_data(insights_text, data_key)
        # Persist as an Insight record
        insight_crud.create_or_update_insight(
            session=session,
            user_id=user_id,
            type="monthly",
            period_key=period_key,
            period_label=period_label,
            content=encrypted_content,
            start_date=start_date,
            end_date=end_date,
        )
        return insights_text

    def _generate_monthly_insights(
        self,
        entries: List[Entry],
        year: int,
        month: int,
        use_pro_model: bool = True,
        data_key: Optional[str] = None,
    ) -> Optional[str]:
        try:
            model = self.pro_model if use_pro_model else self.mini_model  # type: ignore
            prompt = self._get_monthly_insights_prompt(entries, year, month, data_key)
            response = self.client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a supportive therapist-like assistant. "
                            "Create balanced, compassionate monthly insights from diary entries as structured JSON. "
                            "Always speak directly to the user using 'you' (second person). Avoid third-person references."
                            "Be precise, non-judgmental, and practical."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.5,
                max_tokens=800,
            )
            raw = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(raw)
                insights = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                insights = raw
            return insights
        except Exception as e:
            print(f"Error generating monthly insights: {e}")
            return None

    def _get_monthly_insights_prompt(
        self,
        entries: List[Entry],
        year: int,
        month: int,
        data_key: Optional[str] = None,
    ) -> str:
        month_name = calendar.month_name[month]
        condensed = self._condense_entries(
            entries, max_entries=60, max_chars_per_entry=1500, data_key=data_key
        )
        schema = (
            f"{{\n"
            f'  "period": {{"type":"monthly","label":"{month_name} {year}","key":"{year}-{month:02d}"}},\n'
            f'  "language": string,\n'
            f'  "overview": string,\n'
            f'  "mood_trend": {{"summary": string}},\n'
            f'  "themes": [{{"tag": string, "note": string|null}}],\n'
            f'  "notable_moments": [{{"title": string|null, "date": string|null, "summary": string}}],\n'
            f'  "suggestions": [string],\n'
            f'  "meta": {{"tokens_used": number|null}}\n'
            f"}}"
        )
        return (
            f"Generate a concise monthly insights report for {month_name} {year} as a single valid JSON object. "
            f"IMPORTANT: Respond ONLY with JSON, no prose. IMPORTANT: Respond in the dominant language used in the entries.\n\n"
            f"Schema:\n{schema}\n\n"
            f"Guidelines:\n"
            f"- Address the user directly using 'you' (second person). Avoid third-person references.\n"
            f"- Keep it supportive, specific, and ~250–500 words across fields.\n"
            f"- Derive content from entries (use summary if present, otherwise content).\n\n"
            f"Entries:\n{condensed}"
        )

    def generate_weekly_insights_report(
        self,
        session: Session,
        user_id: UUID,
        iso_year: Optional[int] = None,
        iso_week: Optional[int] = None,
        use_pro_model: bool = True,
    ) -> Optional[str]:
        now = datetime.now()
        current_iso = now.isocalendar()
        year = iso_year or current_iso.year
        week = iso_week or current_iso.week

        start_date, end_date = self._get_week_date_range(year, week)
        entries = entry_crud.get_entries_by_date_range(
            session=session, user_id=user_id, start_date=start_date, end_date=end_date
        )
        if not entries:
            return None
        valid_entries = [e for e in entries if not e.is_draft]
        if not valid_entries:
            return None
        data_key = get_user_data_key(session, user_id=user_id)
        insights_text = self._generate_weekly_insights(
            valid_entries, year, week, use_pro_model, data_key
        )
        if not insights_text:
            return None
        period_key = f"{year}-W{week:02d}"
        period_label = f"Week {week}, {year}"
        encrypted_content = encrypt_data(insights_text, data_key)
        insight_crud.create_or_update_insight(
            session=session,
            user_id=user_id,
            type="weekly",
            period_key=period_key,
            period_label=period_label,
            content=encrypted_content,
            start_date=start_date,
            end_date=end_date,
        )
        return insights_text

    def _generate_weekly_insights(
        self,
        entries: List[Entry],
        iso_year: int,
        iso_week: int,
        use_pro_model: bool = True,
        data_key: Optional[str] = None,
    ) -> Optional[str]:
        try:
            model = self.pro_model if use_pro_model else self.mini_model  # type: ignore
            prompt = self._get_weekly_insights_prompt(
                entries, iso_year, iso_week, data_key
            )
            response = self.client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a supportive therapist-like assistant. "
                            "Create balanced, compassionate weekly insights from diary entries as structured JSON. "
                            "Always speak directly to the user using 'you' (second person). Avoid third-person references."
                            "Be precise, non-judgmental, and practical."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.5,
                max_tokens=700,
            )
            raw = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(raw)
                insights = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                insights = raw
            return insights
        except Exception as e:
            print(f"Error generating weekly insights: {e}")
            return None

    def _get_weekly_insights_prompt(
        self,
        entries: List[Entry],
        iso_year: int,
        iso_week: int,
        data_key: Optional[str] = None,
    ) -> str:
        week_label = f"Week {iso_week}, {iso_year}"
        condensed = self._condense_entries(
            entries, max_entries=40, max_chars_per_entry=1000, data_key=data_key
        )
        schema = (
            f"{{\n"
            f'  "period": {{"type":"weekly","label":"{week_label}","key":"{iso_year}-W{iso_week:02d}"}},\n'
            f'  "language": string,\n'
            f'  "overview": string,\n'
            f'  "mood_trend": {{"summary": string}},\n'
            f'  "themes": [{{"tag": string, "note": string|null}}],\n'
            f'  "notable_moments": [{{"title": string|null, "date": string|null, "summary": string}}],\n'
            f'  "suggestions": [string],\n'
            f'  "meta": {{"tokens_used": number|null}}\n'
            f"}}"
        )
        return (
            f"Generate a concise weekly insights report for {week_label} as a single valid JSON object. "
            f"IMPORTANT: Respond ONLY with JSON, no prose. IMPORTANT: Respond in the dominant language used in the entries.\n\n"
            f"Schema:\n{schema}\n\n"
            f"Guidelines:\n"
            f"- Address the user directly using 'you' (second person). Avoid third-person references.\n"
            f"- Keep it supportive, specific, and ~150–350 words across fields.\n"
            f"- Derive content from entries (use summary if present, otherwise content).\n\n"
            f"Entries:\n{condensed}"
        )

    def _condense_entries(
        self,
        entries: List[Entry],
        max_entries: int,
        max_chars_per_entry: int,
        data_key: Optional[str] = None,
    ) -> str:
        rows: List[str] = []
        for idx, entry in enumerate(sorted(entries, key=lambda e: e.created_at)):
            if idx >= max_entries:
                break
            # Decrypt entry content/summary if data_key is provided
            if data_key:
                encrypted_text = (
                    entry.encrypted_summary or entry.encrypted_content or ""
                )
                if encrypted_text:
                    try:
                        text = decrypt_data(encrypted_text, data_key)
                    except Exception as e:
                        print(f"Error decrypting entry {entry.id}: {e}")
                        text = "[Decryption error]"
                else:
                    text = ""
            else:
                # Fallback: use encrypted text (shouldn't happen in normal flow)
                text = entry.encrypted_summary or entry.encrypted_content or ""
            text = text.strip()
            if len(text) > max_chars_per_entry:
                text = text[: max_chars_per_entry - 3].rstrip() + "..."
            date_str = entry.created_at.date().isoformat()
            rating_str = (
                f"{entry.mood_rating:.2f}" if entry.mood_rating is not None else "N/A"
            )
            tags_str = ", ".join(entry.tags) if entry.tags else ""
            rows.append(f"- [{date_str}] mood={rating_str} tags=[{tags_str}]\n{text}")
        return "\n".join(rows)

    def _get_month_date_range(self, year: int, month: int) -> tuple[date, date]:
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        return start_date, end_date

    def _get_week_date_range(self, iso_year: int, iso_week: int) -> tuple[date, date]:
        # ISO: Monday=1, Sunday=7
        start_dt = datetime.fromisocalendar(iso_year, iso_week, 1)
        end_dt = datetime.fromisocalendar(iso_year, iso_week, 7)
        return start_dt.date(), end_dt.date()


ai_insights_service = AIInsightsService()
