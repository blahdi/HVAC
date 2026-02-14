# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
# tinytuya: for device communication
# paho-mqtt: for Home Assistant integration
# python-dotenv: to read your .env file
RUN pip install --no-cache-dir tinytuya paho-mqtt python-dotenv

# Copy everything from the current folder into the container
COPY . .

# Run the script
CMD ["python", "bridge.py"]
