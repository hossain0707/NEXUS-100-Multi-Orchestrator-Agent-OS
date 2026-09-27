FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
RUN useradd --create-home --uid 10001 nexus
COPY pyproject.toml ./
COPY nexus ./nexus
RUN pip install --no-cache-dir .
USER nexus
EXPOSE 8080
CMD ["sh","-c","uvicorn nexus.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
