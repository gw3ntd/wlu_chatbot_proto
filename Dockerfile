FROM python:3.13

WORKDIR /app

EXPOSE 5000

RUN pip install uv

RUN apt-get update -qq && apt-get install ffmpeg -y

COPY . .

RUN uv sync
RUN uv pip install .

CMD ["uv", "run", "wlu_chatbot", "quickstart"]