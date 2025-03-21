FROM python:3.9-slim

LABEL maintainer="Data Sensei <dev@example.com>"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:${PYTHONPATH}" \
    AWS_DEFAULT_REGION=${AWS_REGION} \
    AWS_ENDPOINT_URL=${AWS_ENDPOINT_URL}

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        curl \
        unzip \
        make \
        wget \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Set working directory
WORKDIR /app

# Copy requirements file
COPY src/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir \
        pytest \
        pytest-mock \
        pytest-cov \
        black \
        flake8 \
        pylint \
        mypy \
        pdoc3 \
        localstack \
        awscli-local

# Copy application code
COPY . /app/

# Set up the entrypoint script
COPY ./docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (for development)
CMD ["bash"]