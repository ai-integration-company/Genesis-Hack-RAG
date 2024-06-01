FROM python:3.9

WORKDIR /vector

COPY requirements.txt ./

RUN apt-get update && apt-get install -y 

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["sh", "entrypoint.sh"]
