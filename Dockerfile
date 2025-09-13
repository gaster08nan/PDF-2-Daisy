# Use a PyTorch runtime with CUDA support as a parent image
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Set the working directory in the container
WORKDIR /app

# Copy the new requirements file to the working directory
COPY requirements.docker.txt .

# Install any needed packages specified in requirements.docker.txt
RUN pip install --no-cache-dir -r requirements.docker.txt

# Copy the project files into the container
COPY src/ ./src/
COPY app.py .
COPY server.py .
COPY start.sh .

# Make the start script executable
RUN chmod +x start.sh

# Expose the ports for the backend and the UI
EXPOSE 4567
EXPOSE 8501

# Define a volume for the output data
VOLUME /app/data

# Run the start script when the container launches
CMD ["./start.sh"]