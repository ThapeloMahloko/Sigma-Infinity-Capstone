FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Use the PORT environment variable set by Hugging Face Spaces at runtime.
CMD ["sh", "-c", "python main.py --port ${PORT}"]
