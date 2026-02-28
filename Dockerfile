FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psutil jinja2 web3 python-dotenv
COPY . .
ENV PYTHONPATH=/app
CMD ["uvicorn", "bot.server:app", "--host", "0.0.0.0", "--port", "8000"]
