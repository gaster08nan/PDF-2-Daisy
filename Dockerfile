# Use a PyTorch runtime with CUDA support as a parent image
FROM python:3.12.11-slim

# Add metadata labels
LABEL Author="HDThang"
LABEL version="0.1.0"
LABEL description="Python application for converting PDFs to DAISY format"

# Update package lists and install PortAudio development libraries

RUN pip install lxml
     
RUN apt-get update \
    && apt-get install -y \
    ffmpeg \
    lame \
    libasound-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/* \
    pip install pyaudio 

# Set the working directory in the container
WORKDIR /app

# Copy the new requirements file to the working directory
COPY requirements.docker.txt .

# Install any needed packages specified in requirements.docker.txt
# RUN pip install --no-cache-dir -r requirements.docker.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.docker.txt

# Copy the project files into the container
COPY src/ ./src/
COPY app.py .
COPY server.py .
COPY start.sh .

# Make the start script executable
RUN chmod +x start.sh

# Expose the ports for the backend and the UI
EXPOSE 4567 8501

# Define a volume for the output data
VOLUME /app/data

# Run the start script when the container launches
CMD ["./start.sh"]