# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY deployment/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 bot
USER bot

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "src/bot.py"] 