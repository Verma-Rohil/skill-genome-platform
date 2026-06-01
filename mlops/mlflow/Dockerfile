FROM python:3.12-slim

# Install MLflow and MySQL drivers
RUN pip install --no-cache-dir mlflow pymysql cryptography

EXPOSE 5000

# Entry point triggers MLflow server. uvicorn/gunicorn is wrapped inside it.
ENTRYPOINT ["mlflow", "server"]
