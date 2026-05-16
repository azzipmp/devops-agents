# Test Runner Docker Image
# Base image for executing tests across all infrastructure

FROM python:3.11-slim

LABEL maintainer="DevOps Team <devops@company.com>"
LABEL description="Universal test runner for hybrid infrastructure"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for E2E tests
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Install Google Chrome for Selenium tests
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy test utilities
COPY test-utils/ /app/test-utils/

# Create directories for test results
RUN mkdir -p /app/results /app/reports /app/coverage

# Set up test user (don't run as root)
RUN useradd -m -s /bin/bash testrunner && \
    chown -R testrunner:testrunner /app

USER testrunner

# Default command
CMD ["/bin/bash"]
