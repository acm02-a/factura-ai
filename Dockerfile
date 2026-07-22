# Imagen slim para un servicio liviano y reproducible.
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias primero para aprovechar la cache de capas de Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY factura_ai/ ./factura_ai/

EXPOSE 8000

# Arranca la API. La IA se activa sola si se pasa GROQ_API_KEY como variable de
# entorno; si no, corre el extractor determinístico.
CMD ["uvicorn", "factura_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
