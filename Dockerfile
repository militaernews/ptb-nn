FROM python:3.12-slim

WORKDIR /bot

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /bot /bot
# maybe just copy bot and requirements

CMD ["python", "-m", "main.py"]