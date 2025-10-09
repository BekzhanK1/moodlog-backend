# MoodLog Backend

A personal mood journal and diary web application backend built with FastAPI.

## AI Analysis Approach

**Important**: This backend is designed for AI-powered mood analysis, not manual mood input.

- **User Input**: Users only provide title, content, and optional tags
- **AI Analysis**: The system will automatically analyze:
  - `mood_rating`: Sentiment analysis (-1.0 to +1.0)
  - `tags`: AI-extracted themes and topics from content

This approach ensures more accurate and consistent mood tracking compared to manual user input.

## Features

- **User Management**: Register, login with JWT authentication
- **Diary Entries**: Create, read, update, delete mood journal entries
- **Security**: Password hashing with bcrypt, JWT tokens
- **Database**: SQLite for development, PostgreSQL for production
- **AI-Ready**: Designed to easily add AI features later

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLModel
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Authentication**: JWT + bcrypt
- **Migrations**: Alembic

## Project Structure

```
app/
├── main.py                 # FastAPI application
├── core/
│   ├── config.py          # Environment configuration
│   ├── security.py        # JWT and password hashing
│   └── deps.py           # Dependency injection
├── models/
│   ├── __init__.py       # Model imports
│   ├── user.py          # User model
│   └── entry.py         # Entry model
├── schemas/
│   ├── __init__.py       # Schema imports
│   ├── user.py          # User schemas
│   ├── entry.py         # Entry schemas
│   └── auth.py          # Auth schemas
├── api/
│   └── v1/
│       ├── routes/
│       │   ├── auth.py   # Authentication routes
│       │   └── entries.py # Diary entry routes
│       └── deps.py      # API router
└── db/
    └── session.py        # Database session
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the values in `.env`:
- `SECRET_KEY`: Change to a secure random string
- `DATABASE_URL`: SQLite for development
- `FRONTEND_ORIGIN`: Your frontend URL

### 3. Database Setup

The database will be created automatically on first run. For migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user info

### Diary Entries
- `POST /api/v1/entries/` - Create entry
- `GET /api/v1/entries/` - List entries (paginated)
- `GET /api/v1/entries/{id}` - Get specific entry
- `PUT /api/v1/entries/{id}` - Update entry
- `DELETE /api/v1/entries/{id}` - Delete entry

## AI Features (Future)

The system is designed to easily add AI features:

- **Sentiment Analysis**: Analyze mood from entry content
- **Theme Extraction**: Identify key topics and themes
- **Tag Suggestions**: AI-powered tag recommendations

All AI-related code is marked with `# TODO: AI` comments and placeholder functions.

## Development

### Adding New Features

1. Create models in `app/models/`
2. Add schemas in `app/schemas/`
3. Implement routes in `app/api/v1/routes/`
4. Update dependencies in `app/api/v1/deps.py`

### Database Changes

1. Modify models in `app/models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Configure `DATABASE_URL_PROD` for PostgreSQL
3. Use a secure `SECRET_KEY`
4. Update `FRONTEND_ORIGIN` to your production domain
5. Use a production ASGI server like Gunicorn with Uvicorn workers
