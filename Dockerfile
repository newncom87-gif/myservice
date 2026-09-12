FROM python:3.11-slim

WORKDIR /app

COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY app ./app
COPY scripts/manage_users.py ./scripts/manage_users.py
COPY wsgi.py .

ENV BIBLE_PPT_DATA_DIR=/data
ENV HOST=0.0.0.0
ENV PORT=8765

EXPOSE 8765
VOLUME ["/data"]

CMD ["python", "wsgi.py"]
