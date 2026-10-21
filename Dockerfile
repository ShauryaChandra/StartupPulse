# UNTESTED in the build environment - see README "Docker" section.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir pandas scikit-learn xgboost lightgbm prophet sqlalchemy \
    psycopg2-binary fastapi "uvicorn[standard]" streamlit requests
COPY src ./src
COPY app.py .
ENV STARTUPPULSE_API_KEY=dev-key
EXPOSE 8000 8501
