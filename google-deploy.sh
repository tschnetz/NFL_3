#!/bin/bash

# Ensure gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "gcloud could not be found, please install it first."
    exit 1
fi

# Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found, please install it first."
    exit 1
fi

# Set variables
PROJECT_ID="nfl-data-2024"
IMAGE_NAME="nfl-dash"
REGION="us-east1"


# Set the project
gcloud config set project $PROJECT_ID

# Build the Docker image
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Submit the build to Google Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Deploy to Google Cloud Run
gcloud run deploy $IMAGE_NAME --image gcr.io/$PROJECT_ID/$IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated

echo "Deployment to Google Cloud Run completed successfully."