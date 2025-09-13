FROM python:3.10-slim

# Install system dependencies (FreeSans included here)
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    ffmpeg \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Expose port (Render sets PORT automatically, default 10000)
EXPOSE 10000

# Run the bot
CMD ["python", "caribbean_meme_bot.py"]
