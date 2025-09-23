FROM python:3.10-slim

# Install system dependencies (fonts, ffmpeg, etc.)
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
    pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Expose port (Render assigns $PORT)
EXPOSE 10000

# Start Flask app with Gunicorn (this also triggers your bot in background)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:10000", "caribbean_meme_bot:app"]
