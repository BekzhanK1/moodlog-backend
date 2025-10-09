run:
	uvicorn app.main:app --reload

migrate-new:
	alembic revision -m "$$m" --autogenerate

migrate-up:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-stamp-head:
	alembic stamp head
