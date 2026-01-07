#!/bin/bash

# AWS Lambda Deploy Script
# This script packages and deploys your Lambda function to AWS

set -e

# Configuration
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-my-lambda-function}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DEPLOYMENT_BUCKET="${DEPLOYMENT_BUCKET:-lambda-deployments}"

echo "🚀 Starting AWS Lambda deployment..."
echo "Function: $LAMBDA_FUNCTION_NAME"
echo "Region: $AWS_REGION"

# Create package directory
rm -rf package/
mkdir -p package/

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -t package/ --quiet

# Copy Lambda function
echo "📄 Copying Lambda function..."
cp lambda_function.py package/

# Create ZIP file
echo "📦 Creating deployment package..."
cd package/
zip -r ../lambda-deployment.zip . -q
cd ..

# Get file size
PACKAGE_SIZE=$(du -h lambda-deployment.zip | cut -f1)
echo "✅ Deployment package created: $PACKAGE_SIZE"

# Deploy to Lambda
echo "🚀 Deploying to AWS Lambda..."
aws lambda update-function-code \
  --function-name $LAMBDA_FUNCTION_NAME \
  --zip-file fileb://lambda-deployment.zip \
  --region $AWS_REGION

echo "⏳ Waiting for deployment to complete..."
aws lambda wait function-updated \
  --function-name $LAMBDA_FUNCTION_NAME \
  --region $AWS_REGION

# Publish version
echo "📝 Publishing Lambda version..."
VERSION=$(aws lambda publish-version \
  --function-name $LAMBDA_FUNCTION_NAME \
  --region $AWS_REGION \
  --query 'Version' \
  --output text)

echo "✨ Deployment successful!"
echo "Function: $LAMBDA_FUNCTION_NAME"
echo "Version: $VERSION"
echo "Region: $AWS_REGION"

# Cleanup
rm -rf package/
rm -f lambda-deployment.zip

echo "✅ Done!"
