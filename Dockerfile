# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (FastMCP/Uvicorn default is often 8000)
EXPOSE 8000

# Run the server using Uvicorn
CMD ["uvicorn", "server:mcp", "--host", "0.0.0.0", "--port", "8000"]
