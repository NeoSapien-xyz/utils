FROM python:3.13-slim

WORKDIR /app

# Copy everything except secrets (filtered via .dockerignore)
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7980
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7980"]

