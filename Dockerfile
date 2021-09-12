FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY ./App /app/app
COPY ./requirements.txt /app

ENV FTS_BASE_DIR ./tmp
ENV FTS_DOWNLOAD_EXPIRE_SECONDS 180
ENV FTS_FILE_DELETE_TASK_INTERVAL 10
ENV FTS_FILE_DELETE_INTERVAL 300
ENV FTS_FILE_BUFFER_SIZE 65536

RUN pip install --no-cache-dir -r requirements.txt
