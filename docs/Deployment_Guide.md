# Deployment Guide

## Prerequisites
- Python 3.10+
- Docker & Docker Compose
- ngrok

## Local Setup
1. Clone the repository and install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in API keys.
3. Start Redis: `docker-compose up -d redis`
4. Run FastAPI: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Expose locally: `ngrok http 8000`

## Cloud Deployment (Railway/Render)
1. Link your GitHub repository to Railway or Render.
2. Provide the environment variables in the project dashboard.
3. The included `Dockerfile` will automatically build and deploy the app.
