FROM python:3.11-slim

# Install system dependencies, including jq for parsing JSON
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# --- FIXED SECTION: Install Chrome and a matching Chromedriver ---
# 1. Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable && rm -rf /var/lib/apt/lists/*

# 2. Install the correct Chromedriver in a single command layer
RUN CHROME_VERSION=$(google-chrome --product-version | cut -d. -f1-3) && \
    DRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | jq -r ".versions[] | select(.version | startswith(\"${CHROME_VERSION}\")) | .downloads.chromedriver[] | select(.platform == \"linux64\") | .url" | head -n 1) && \
    wget -q --continue -P /tmp/ ${DRIVER_URL} && \
    unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver-linux64.zip
# --- END FIXED SECTION ---

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY strathmore_password_reset.py .
COPY .env .

# Create passwords directory
RUN mkdir -p passwords

# Run the script
CMD ["python", "strathmore_password_reset.py"]