include .env
export

run:
	uvicorn app:app --reload --host 0.0.0.0 --port 8000

pretty:
	ruff format

lint:
	ruff check


plint: pretty lint
