# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]