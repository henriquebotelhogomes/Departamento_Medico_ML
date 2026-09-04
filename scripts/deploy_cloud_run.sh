#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# RadioAI — One-Command Deploy to Google Cloud Run (Scale-to-Zero / $0 Cost)
# ==============================================================================

SERVICE_NAME="radioai"
REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Google Cloud Project ID not set."
  echo "👉 Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo "🚀 Deploying RadioAI to Google Cloud Run..."
echo "📦 Project ID:  $PROJECT_ID"
echo "🌐 Region:      $REGION"
echo "⚙️  Service:     $SERVICE_NAME"
echo "💰 Policy:      Scale-to-Zero (min-instances=0 -> $0 cost when idle)"
echo "------------------------------------------------------------------"

# 1. Pull Git LFS model
echo "📥 Ensuring Git LFS model weights are present..."
git lfs pull

# 2. Build and submit to Cloud Build
echo "🐳 Building container image in Google Cloud..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" .

# 3. Deploy to Cloud Run
echo "⚡ Deploying container to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --port 8000

URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)')
echo "------------------------------------------------------------------"
echo "✅ RadioAI Live URL: $URL"
echo "🎉 Deployed successfully! Running with 0 minimum instances ($0/month)."
