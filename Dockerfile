FROM python:3.12-slim
LABEL authors="lukin"
WORKDIR /app

RUN apt update && apt install git -y

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app

CMD ["python", "main.py"]