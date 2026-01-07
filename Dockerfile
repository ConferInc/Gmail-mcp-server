# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Ensure output is sent directly to terminal (useful for docker logs)
ENV PYTHONUNBUFFERED=1

# Install system dependencies if needed (e.g. for some python packages)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src ./src
COPY .env.example .

# Expose the port the app runs on
EXPOSE 8000

# Define environment variables (can be overridden by Coolify)
ENV PORT=8000

# Run the FastMCP server with SSE transport
# Host 0.0.0.0 is crucial for Docker networking
CMD ["fastmcp", "run", "src/server.py", "--transport", "sse", "--port", "8000", "--host", "0.0.0.0"]
