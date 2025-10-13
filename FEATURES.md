# 📝 Personal AI Journal – Feature List

## 🔐 1. Authentication & Security
- User registration (email + password)
- Secure login / logout (JWT-based sessions)
- Password hashing with bcrypt
- Optional OAuth (Google / GitHub)
- **End-to-end encryption:**
  - Each user’s diary entries are encrypted at rest
  - Encryption keys stored in DB (encrypted with `MASTER_KEY` from `.env`)
  - `MASTER_KEY` never stored in code or version control

## ✍️ 2. Journaling Core
- Create, read, update, delete diary entries
- Rich text support (Markdown or plain text)
- Optional title, mood rating (-2 to +2), and custom tags
- Auto-saved drafts
- Full history with timestamps (UTC, timezone-aware)

## 🧠 3. AI-Powered Insights _(Planned – not implemented yet)_
- Sentiment analysis: Auto-detect mood (positive/neutral/negative) + score (-1 to +1)
- Theme extraction: Identify key topics (e.g., "work", "nature", "anxiety")
- Smart writing prompts: Personalized questions based on recent entries
- Weekly AI summary: Narrative insights like “You felt more energized after outdoor activities”
- Voice-to-text (future): Record audio → transcribe → analyze

## 📊 4. Analytics & Visualization
- Mood trend graph (daily/weekly/monthly)
- Heatmap calendar with color-coded mood
- **Statistics:**
  - Average mood over time
  - Entry frequency (per day/week)
  - Top positive/negative days
  - Tag frequency & correlation with mood
- Export data (CSV / JSON)

## 🤖 5. Intelligent Features _(Planned – marked as # TODO: AI)_
- `/api/v1/ai/suggested-prompt` → returns empathetic writing prompt
- `/api/v1/analytics/summary` → returns AI-generated weekly recap
- Auto-suggested tags during entry creation
- “Good Days” archive for re-reading uplifting entries

## 📱 6. User Experience
- Clean, minimalist UI (light/dark mode)
- Responsive design (mobile + desktop)
- Quick search by tags, date, or mood
- Entry list + calendar view toggle
- Real-time word count & mood indicator

## 🛠️ 7. Technical & DevOps
- Backend: FastAPI (Python)
- Frontend: React + TypeScript + Tailwind CSS
- Database: PostgreSQL (production) / SQLite (local dev)
- ORM: SQLModel
- Encryption: AES-GCM for user data, keys encrypted with `MASTER_KEY`
- Deployment-ready: Docker support, `.env` config, CORS for `localhost:3000`
- Health check endpoint (`/health`)
- Alembic migrations (ready for future schema changes)

## 💡 8. Privacy by Design
- Server-side encryption (keys never exposed to frontend)
- No plaintext logging of user content
- HTTPS enforced in production
- Clear privacy policy: “We analyze your text only to generate insights — raw content is encrypted and never shared.”
