FROM python:3.12-slim

WORKDIR /app

COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

COPY web_app.py ./
COPY arquivos ./arquivos
COPY icones ./icones
COPY icones2 ./icones2

EXPOSE 8000

CMD ["python", "web_app.py", "--host", "0.0.0.0"]
