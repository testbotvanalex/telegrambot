#!/bin/bash

PROJECT_ID=autoparts-bot-452089041705
SERVICE_NAME=telegram-bot
REGION=europe-west1

echo "📦 Builden image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "☁️ Deploy naar Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars $(grep -v '^#' .env | xargs)

echo "✅ Klaar! Ga naar $WEBHOOK_URL"
