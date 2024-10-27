#!/bin/bash

# Build the Docker image
docker build --platform linux/amd64 -t nfl-dash .

# Authenticate with Google Cloud
# gcloud auth login  # Uncomment if you need to authenticate

# Set the project ID
gcloud config set project nfl-data-2024

# Build and push the image to Container Registry
gcloud builds submit --tag gcr.io/nfl-data-2024/nfl-dash

# Deploy to Cloud Run
gcloud run deploy nfl-dash \
  --image gcr.io/nfl-data-2024/nfl-dash \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --port 8080 \
  --port 8001
