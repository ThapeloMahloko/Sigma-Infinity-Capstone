FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py config.py database.py mqtt_handler.py ui_components.py utils.py telegram_qr.png ./
COPY pages/*.py ./pages/

EXPOSE 7860

# Start Panel app - main.py contains the full Smart Farm Dashboard
CMD exec python -m panel serve main.py --address 0.0.0.0 --port "$PORT" --allow-websocket-origin="*"
