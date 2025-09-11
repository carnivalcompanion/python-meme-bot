FROM python:3.10-slim

# Keep packages up to date & install system deps for Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install Python deps first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# (Optional) for clarity. Render sets PORT at runtime; Flask binds to it.
EXPOSE 10000

# Run the bot
CMD ["python", "caribbean_meme_bot.py"]
