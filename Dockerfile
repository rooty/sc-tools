FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir  --upgrade  -r /tmp/requirements.txt

WORKDIR /code
COPY ./app /code/app

CMD ["uvicorn", "app.tools:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
