FROM python:3.12-slim

# Set working directory
WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5002"]
