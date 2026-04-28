FROM python:3.11-slim
WORKDIR /app
COPY lex_aureon/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY lex_aureon /app/lex_aureon
COPY packages /app/packages
ENV PYTHONPATH=/app
CMD ["uvicorn", "lex_aureon.backend.governance_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
