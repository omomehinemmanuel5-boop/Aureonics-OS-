run:
	uvicorn app.main:app --reload

test:
	pytest -q

install:
	pip install -r requirements.txt
