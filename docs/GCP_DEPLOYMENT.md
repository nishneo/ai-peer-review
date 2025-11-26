# Deploying AI Peer Review to Google Cloud Platform

This guide walks you through deploying the backend to **Cloud Run** (free tier) and frontend to **Firebase Hosting** (free).

## Prerequisites

1. [Google Cloud account](https://cloud.google.com/) (free tier available)
2. [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed
3. [Firebase CLI](https://firebase.google.com/docs/cli) installed
4. Your OpenRouter API key

---

## Part 1: Deploy Backend to Cloud Run

### Step 1: Set up GCP Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create ai-peer-review --name="AI Peer Review"

# Set the project
gcloud config set project ai-peer-review

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Step 2: Build and Deploy

```bash
# Navigate to project root
cd /path/to/ai-peer-review

# Deploy to Cloud Run (this builds and deploys in one command)
gcloud run deploy ai-peer-review-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "CORS_ORIGINS=https://ai-peer-review.web.app"
```

### Step 3: Set OpenRouter API Key

```bash
# Add your API key as a secret
gcloud run services update ai-peer-review-api \
  --region us-central1 \
  --set-env-vars "OPENROUTER_API_KEY=sk-or-v1-your-key-here"
```

### Step 4: Get Your Backend URL

```bash
# Get the service URL
gcloud run services describe ai-peer-review-api \
  --region us-central1 \
  --format "value(status.url)"
```

Save this URL (e.g., `https://ai-peer-review-api-xxxxx-uc.a.run.app`)

---

## Part 2: Deploy Frontend to Firebase Hosting

### Step 1: Set up Firebase

```bash
# Login to Firebase
firebase login

# Initialize Firebase in your project
firebase init hosting

# When prompted:
# - Select "Use an existing project" → choose your GCP project
# - Public directory: frontend/dist
# - Single-page app: Yes
# - Don't overwrite index.html
```

### Step 2: Configure API URL

Create a `.env.production` file in the frontend directory:

```bash
# frontend/.env.production
VITE_API_URL=https://ai-peer-review-api-xxxxx-uc.a.run.app
```

Replace with your actual Cloud Run URL from Part 1.

### Step 3: Build and Deploy Frontend

```bash
# Build the frontend
cd frontend
npm install
npm run build

# Deploy to Firebase
cd ..
firebase deploy --only hosting
```

### Step 4: Update CORS on Backend

Update the backend to allow your Firebase URL:

```bash
gcloud run services update ai-peer-review-api \
  --region us-central1 \
  --set-env-vars "CORS_ORIGINS=https://ai-peer-review.web.app,https://your-project-id.web.app"
```

---

## Your App is Live! 🎉

- **Frontend:** https://ai-peer-review.web.app (or your Firebase URL)
- **Backend:** https://ai-peer-review-api-xxxxx-uc.a.run.app

---

## Cost Estimation

| Service | Free Tier | Your Expected Cost |
|---------|-----------|-------------------|
| Cloud Run | 2M requests/mo, 360K GB-seconds | **$0** (light usage) |
| Firebase Hosting | 10GB storage, 360MB/day transfer | **$0** |
| **Total** | | **$0/month** |

---

## Useful Commands

```bash
# View Cloud Run logs
gcloud run services logs read ai-peer-review-api --region us-central1

# Update backend code
gcloud run deploy ai-peer-review-api --source . --region us-central1

# Redeploy frontend
cd frontend && npm run build && cd .. && firebase deploy --only hosting

# Delete everything (cleanup)
gcloud run services delete ai-peer-review-api --region us-central1
firebase hosting:disable
```

---

## Troubleshooting

### CORS Errors
Make sure `CORS_ORIGINS` includes your Firebase hosting URL:
```bash
gcloud run services update ai-peer-review-api \
  --region us-central1 \
  --set-env-vars "CORS_ORIGINS=https://your-app.web.app"
```

### Cold Starts
Cloud Run may take 2-5 seconds on first request after inactivity. This is normal for the free tier.

### API Key Issues
Verify your OpenRouter API key is set:
```bash
gcloud run services describe ai-peer-review-api \
  --region us-central1 \
  --format "yaml(spec.template.spec.containers[0].env)"
```

