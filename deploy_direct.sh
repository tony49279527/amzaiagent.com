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
  
  # Read .env line by line to handle spaces correctly
  while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # Export the variable
    export "$key=$value"
  done < .env
  
  # Manually construct the ENV_VARS string for gcloud
  # We use the exported variables which now contain the full values
  # Remove spaces from password for the actual API usage if needed, or keep them if the app handles it.
  # Config.py handles removal, but let's ensure we pass the full string.
  
  # Note: logic in config.py is `.replace(" ", "")`. So we pass the full string here.
  # We need to be careful with commas in gcloud --set-env-vars.
  
  # Build env vars strictly from .env values; avoid hardcoded credentials/tokens in scripts.
  CLEAN_PWD="${SMTP_PASSWORD// /}"
  ENV_VARS="SMTP_USER=$SMTP_USER,SMTP_PASSWORD=$CLEAN_PWD,SMTP_PORT=${SMTP_PORT:-465},SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com},N8N_CHECKOUT_WEBHOOK_URL=$N8N_CHECKOUT_WEBHOOK_URL,N8N_FREE_ANALYSIS_URL=$N8N_FREE_ANALYSIS_URL,N8N_PRO_ANALYSIS_URL=$N8N_PRO_ANALYSIS_URL,N8N_SEND_REPORT_URL=$N8N_SEND_REPORT_URL,N8N_ALLOWED_HOSTS=$N8N_ALLOWED_HOSTS,OPENROUTER_API_KEY=$OPENROUTER_API_KEY,SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY"
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
