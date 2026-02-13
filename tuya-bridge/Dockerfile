# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
# tinytuya: for device communication
# flask: for the web dashboard/API
# paho-mqtt: for Home Assistant integration
RUN pip install --no-cache-dir tinytuya flask paho-mqtt

# Copy the bridge script into the container
COPY bridge.py .

# Expose the web dashboard port
EXPOSE 5000

# Run the script
CMD ["python", "bridge.py"]
