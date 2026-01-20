
#!/bin/bash
# Generate GCP Credentials for GitHub Actions

SERVICE_ACCOUNT_NAME="github-deployer"
PROJECT_ID=$(gcloud config get-value project)

echo "Setting up auto-deploy for Project: $PROJECT_ID"

# 1. Create Service Account
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="GitHub Actions Deployer" || echo "Service account likely exists, continuing..."

# 2. Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin" # Sometimes needed for container registry

# 3. Create Key File
gcloud iam service-accounts keys create gcp_key.json \
    --iam-account="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo ""
echo "========================================================"
echo "✅ SUCCESS! Key generated: gcp_key.json"
echo "========================================================"
echo "Please set this as a secret in GitHub:"
echo "Name: GCP_SA_KEY"
echo "Secret: (Copy the entire content of gcp_key.json)"
echo "========================================================"
