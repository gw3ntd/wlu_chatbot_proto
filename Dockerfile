FROM python:3.13

WORKDIR /app

EXPOSE 5000

COPY . .

RUN pip install uv

RUN uv sync

RUN apt-get update -qq && apt-get install ffmpeg -y

CMD ["uv", "run", "ucr_chatbot"]