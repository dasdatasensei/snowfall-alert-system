#!/bin/bash
# LocalStack initialization script for Snowfall Alert System

echo "=== Initializing LocalStack AWS resources ==="

# Create Lambda role
awslocal iam create-role \
    --role-name lambda-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attach policies to the role
awslocal iam attach-role-policy \
    --role-name lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create CloudWatch Logs group
awslocal logs create-log-group --log-group-name /aws/lambda/SnowfallAlertFunction

# Wait for Lambda to be available
echo "Waiting for Lambda service to be available..."
sleep 5

echo "=== AWS resources initialized ==="