FROM python:3.11-slim

WORKDIR /app

RUN pip install uv --quiet

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .

EXPOSE 7860

CMD ["uv", "run", "chainlit", "run", "app.py", "--port", "7860", "--host", "0.0.0.0"]
