FROM huecker.io/library/python:3.9-slim

WORKDIR /telegram_bot

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python", "./main.py"]
