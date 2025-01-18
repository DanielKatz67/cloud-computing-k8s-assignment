FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the Flask port
EXPOSE 8080

# Run the Flask app
CMD ["python", "app.py"]
