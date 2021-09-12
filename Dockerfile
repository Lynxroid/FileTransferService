FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY ./App /app/app
COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


