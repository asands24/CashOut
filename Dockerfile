# Minimal image for Streamlit deploys
FROM python:3.11-slim

WORKDIR /app

# System deps (optional: for faster pandas)
RUN pip install --no-cache-dir --upgrade pip

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8501
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_ENABLEXSRSFPROTECTION=false

CMD ["streamlit", "run", "app.py"]
