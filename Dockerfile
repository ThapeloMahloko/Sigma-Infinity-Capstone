FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Start Panel app - main.py contains the full Smart Farm Dashboard
CMD python -m panel serve main.py --port 7860 --allow-websocket-origin="*"
