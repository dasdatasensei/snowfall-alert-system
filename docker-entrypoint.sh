#!/bin/bash
set -e

# Wait for LocalStack to be available if needed
if [ -n "$AWS_ENDPOINT_URL" ] && [[ "$AWS_ENDPOINT_URL" == *"localstack"* ]]; then
    echo "Waiting for LocalStack to be ready..."
    timeout=${LOCALSTACK_TIMEOUT}
    counter=0
    until awslocal lambda list-functions > /dev/null 2>&1
    do
        sleep 1
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            echo "Timed out waiting for LocalStack!"
            exit 1
        fi
    done
    echo "LocalStack is ready!"
fi

# Create a Python virtual environment in the container if it doesn't exist
if [ ! -d "/app/venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv /app/venv
    echo "Installing requirements..."
    /app/venv/bin/pip install -r /app/src/requirements.txt
    echo "Virtual environment setup complete!"
fi

# Function to deploy the lambda to LocalStack
deploy_to_localstack() {
    echo "Deploying Lambda function to LocalStack..."

    # Create deployment package
    mkdir -p /app/deployment/package
    cp -R /app/src/* /app/deployment/package/
    cd /app/deployment/package
    pip install -r /app/src/requirements.txt -t .
    zip -r /app/deployment/lambda_function.zip .
    cd /app

    # Create the Lambda function in LocalStack
    awslocal lambda create-function \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --runtime ${LAMBDA_RUNTIME} \
        --handler ${LAMBDA_HANDLER} \
        --zip-file fileb:///app/deployment/lambda_function.zip \
        --role ${LAMBDA_ROLE}

    # Create the CloudWatch Events rule to trigger the Lambda
    awslocal events put-rule \
        --name ${EVENT_RULE_NAME} \
        --schedule-expression "${EVENT_SCHEDULE}"

    # Add permission for CloudWatch Events to invoke the Lambda
    awslocal lambda add-permission \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --statement-id AllowEventBridgeToInvokeLambda \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn ${EVENT_RULE_ARN}

    # Create the target for the rule
    awslocal events put-targets \
        --rule ${EVENT_RULE_NAME} \
        --targets "Id"="1","Arn"="arn:aws:lambda:${AWS_REGION}:000000000000:function:${LAMBDA_FUNCTION_NAME}"

    echo "Lambda deployment to LocalStack complete!"
}

# Check if this is a development environment
if [ "$ENVIRONMENT" = "development" ]; then
    deploy_to_localstack
fi

# Execute the provided command
exec "$@"