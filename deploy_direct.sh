#!/bin/bash
# Direct Deployment Script for Amz AI Replica (With ENV Auto-Injection)

SERVICE_NAME="amz-ai-replica"
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

echo "========================================================"
echo "🚀 Deploying $SERVICE_NAME to Google Cloud Run (With Forced Env Vars)..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "========================================================"

# Read .env file and format as comma-separated string
if [ -f .env ]; then
  echo "Found .env file, preparing environment variables..."
  # Export variables from .env for use in this script
  export $(grep -v '^#' .env | xargs)
  
  # Construct env var string, handling potential spaces in values if needed (simple version)
  # But for safety, we simply pass them explicitly to avoid parsing issues
  ENV_VARS="SMTP_USER=$SMTP_USER,SMTP_PASSWORD=${SMTP_PASSWORD// /},OPENROUTER_API_KEY=$OPENROUTER_API_KEY,SMTP_PORT=465,SMTP_SERVER=smtp.gmail.com"
else
  echo "❌ Error: .env file not found! Deployment will lack credentials."
  exit 1
fi

echo "Deploying with forced environment variables..."

# Deploy using source
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars "$ENV_VARS"

echo ""
echo "========================================================"
if [ $? -eq 0 ]; then
    echo "✅ Deployment Successful!"
else
    echo "❌ Deployment Failed."
fi
echo "========================================================"
