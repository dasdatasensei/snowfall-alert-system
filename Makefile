# Snowfall Alert System Makefile
# ===================================
#
# This Makefile contains commands for development, testing, and deployment
# of the Snowfall Alert System.

.PHONY: help setup clean lint test test-unit test-integration deploy dev package docs check-env docker-build docker-dev docker-test docker-prod

# Shell to use for shell commands
SHELL := /bin/bash

# Python settings
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# AWS settings
AWS_REGION ?= $$(grep -m 1 "AWS_REGION" .env | cut -d '=' -f2 || echo "us-west-2")
LAMBDA_FUNCTION_NAME ?= SnowfallAlertFunction

# Docker settings
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_FILE := docker-compose.yml
DOCKER_COMPOSE_TEST_FILE := docker-compose.test.yml
DOCKER_COMPOSE_PROD_FILE := docker-compose.prod.yml

# Linting and code quality
PYLINT := $(VENV)/bin/pylint
BLACK := $(VENV)/bin/black
MYPY := $(VENV)/bin/mypy
FLAKE8 := $(VENV)/bin/flake8

# Deployment directory
DEPLOYMENT_DIR := deployment
PACKAGE_DIR := $(DEPLOYMENT_DIR)/package
ZIP_FILE := $(DEPLOYMENT_DIR)/lambda_function.zip

# Application directories
SRC_DIR := src
TESTS_DIR := tests

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help menu
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

check-env:  ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Create one based on README instructions."; \
		exit 1; \
	fi

$(VENV):  ## Create virtual environment if it doesn't exist
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

setup: $(VENV) check-env  ## Set up development environment
	$(PIP) install -r src/requirements.txt
	$(PIP) install -e .
	$(PIP) install pytest pytest-mock pytest-cov black flake8 pylint mypy
	@echo "Development environment set up successfully"

clean:  ## Remove build, cache, and environment directories
	rm -rf $(DEPLOYMENT_DIR)
	rm -rf build/
	rm -rf dist/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	@echo "Cleaned up build artifacts and cache files"

lint:  ## Run code linting and formatting checks
	$(BLACK) --check $(SRC_DIR) $(TESTS_DIR)
	$(FLAKE8) $(SRC_DIR) $(TESTS_DIR)
	$(PYLINT) $(SRC_DIR)
	$(MYPY) $(SRC_DIR)

format:  ## Format code using Black
	$(BLACK) $(SRC_DIR) $(TESTS_DIR)
	@echo "Code formatting complete"

test: test-unit test-integration  ## Run all tests

test-unit:  ## Run unit tests
	$(PYTHON_VENV) -m pytest $(TESTS_DIR) -k "not integration" -v

test-integration:  ## Run integration tests
	$(PYTHON_VENV) -m pytest $(TESTS_DIR)/test_integration.py -v

test-coverage:  ## Run tests with coverage report
	$(PYTHON_VENV) -m pytest --cov=$(SRC_DIR) --cov-report=term --cov-report=html $(TESTS_DIR)
	@echo "Coverage report generated in htmlcov/"

package: clean  ## Package the Lambda function for deployment
	mkdir -p $(PACKAGE_DIR)
	cp -R $(SRC_DIR)/* $(PACKAGE_DIR)/
	cd $(PACKAGE_DIR) && pip install -r ../$(SRC_DIR)/requirements.txt -t . && cd ../../
	find $(PACKAGE_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find $(PACKAGE_DIR) -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
	find $(PACKAGE_DIR) -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	cd $(PACKAGE_DIR) && zip -r ../lambda_function.zip . && cd ../../
	@echo "Lambda package created at $(ZIP_FILE)"

deploy: package  ## Deploy the Lambda function to AWS
	@echo "Deploying to AWS Lambda in region $(AWS_REGION)..."
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$(ZIP_FILE) \
		--region $(AWS_REGION)
	@echo "Deployment complete"

create-lambda:  ## Create a new Lambda function in AWS (run once)
	aws lambda create-function \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--runtime python3.9 \
		--handler lambda_function.lambda_handler \
		--zip-file fileb://$(ZIP_FILE) \
		--role arn:aws:iam::$(shell aws sts get-caller-identity --query 'Account' --output text):role/lambda-snowfall-alerts-role \
		--timeout 30 \
		--memory-size 128 \
		--region $(AWS_REGION) \
		--environment Variables="{$$(grep -v '^#' .env | xargs | sed 's/ /,/g')}"

dev:  ## Run a local development server
	$(PYTHON_VENV) -m src.local_development

docs:  ## Generate documentation
	$(PYTHON_VENV) -m pdoc --html --output-dir docs/api $(SRC_DIR)
	@echo "API documentation generated in docs/api/"

check-slack:  ## Test Slack integration by sending a test message
	$(PYTHON_VENV) -c "import requests, os; response = requests.post(os.environ.get('SLACK_WEBHOOK_URL'), json={'text': 'Test message from Snowfall Alert System'}); print(f'Status: {response.status_code}')"

verify-config:  ## Verify the configuration
	$(PYTHON_VENV) -c "from src.config import validate_config; missing = validate_config(); print(f'Missing configs: {missing}' if missing else 'All required configs present')"

update-schedule:  ## Update the Lambda CloudWatch Events schedule
	aws events put-rule \
		--name SnowfallAlertTrigger \
		--schedule-expression "rate($(shell grep -m 1 CHECK_FREQUENCY .env | cut -d '=' -f2 || echo "6") hours)" \
		--region $(AWS_REGION)
	@echo "CloudWatch schedule updated"

# Docker commands
docker-build:  ## Build the Docker image
	docker build -t snowfall-alert-system .

docker-dev:  ## Start the development environment using Docker
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "Development environment started. Connect to the app container with:"
	@echo "docker-compose exec app bash"

docker-test:  ## Run tests inside Docker
	@if [ ! -f .env.test ]; then \
		echo "Error: .env.test file not found. Please create it from the template."; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_TEST_FILE) up --build --abort-on-container-exit

docker-prod:  ## Deploy to production using Docker
	@if [ ! -f .env.prod ]; then \
		echo "Error: .env.prod file not found. Create one from .env.prod.example"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD_FILE) up -d

docker-down:  ## Stop all Docker containers
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_TEST_FILE) down
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD_FILE) down

docker-logs:  ## View logs from Docker containers
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f

docker-clean:  ## Remove all Docker containers, images, and volumes for this project
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down -v --rmi local
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_TEST_FILE) down -v --rmi local
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD_FILE) down -v --rmi local