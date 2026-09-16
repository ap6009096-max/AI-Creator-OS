FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OUTPUT_DIR=outputs \
    PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p outputs

EXPOSE 8501

# Mount a host volume over /app/outputs to persist projects between runs.
# Cloud Run sets $PORT; local default is 8501.
CMD streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}
