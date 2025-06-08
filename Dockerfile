FROM python:3.13-slim

RUN apt-get update && apt-get install -y fontconfig  && rm -rf /var/lib/apt/lists/*
COPY fonts /usr/share/fonts/truetype
RUN fc-cache -f -v

WORKDIR /bot
COPY /bot .
RUN pip install --no-cache-dir -r ./requirements.txt

CMD ["python", "-m", "main"]