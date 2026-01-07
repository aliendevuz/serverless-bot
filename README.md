# AWS Lambda Deployment Guide

## Tayyorlash

### 1. AWS Credentials Setup
```bash
# AWS CLI ni o'rnating
aws configure

# yoki GitHub Actions uchun secrets qo'shing
```

### 2. GitHub Secrets Qo'shish
GitHub Repository Settings → Secrets and variables → Actions ga quyidagilarni qo'shing:

```
AWS_ROLE_TO_ASSUME: arn:aws:iam::YOUR_ACCOUNT_ID:role/github-lambda-role
```

### 3. Lambda Function Yaratish
AWS Console'da:
```bash
aws lambda create-function \
  --function-name my-lambda-function \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-role \
  --handler lambda_function.lambda_handler \
  --region us-east-1
```

## Deploy Qilish

### Variants 1: GitHub Actions (Automatic)
```bash
git push main  # Avtomatik deploy bo'ladi
```

### Variant 2: Manual Local Deployment
```bash
# Script orqali deploy qilish
bash deploy.sh

# Environment variables o'rnatish
export LAMBDA_FUNCTION_NAME=my-lambda-function
export AWS_REGION=us-east-1
bash deploy.sh
```

### Variant 3: AWS CLI orqali to'g'ridan-to'g'ri
```bash
# Dependencies o'rnatish
pip install -r requirements.txt -t package/

# Lambda function'ni qo'shish
cp lambda_function.py package/

# ZIP fayl yaratish
cd package && zip -r ../lambda-deployment.zip . && cd ..

# Deploy qilish
aws lambda update-function-code \
  --function-name my-lambda-function \
  --zip-file fileb://lambda-deployment.zip \
  --region us-east-1

# Version publish qilish
aws lambda publish-version --function-name my-lambda-function
```

## Testing

```bash
# Lambda function'ni test qilish
aws lambda invoke \
  --function-name my-lambda-function \
  --region us-east-1 \
  response.json

cat response.json
```

## Logs Ko'rish

```bash
# Recent logs
aws logs tail /aws/lambda/my-lambda-function --follow

# Specific stream
aws logs tail /aws/lambda/my-lambda-function --follow --log-stream-names [STREAM_NAME]
```

## Environment Variables

Deploy script'da quyidagi variables'ni o'rnatishingiz mumkin:

```bash
export LAMBDA_FUNCTION_NAME=my-function-name
export AWS_REGION=us-east-1
export DEPLOYMENT_BUCKET=my-bucket
```

## IAM Role Setup

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:PublishVersion",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*"
    }
  ]
}
```
