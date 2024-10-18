# Base image with CUDA support
FROM nvidia/cuda:12.6.2-cudnn-devel-ubuntu22.04

# Set environment variables
ENV LLM_HOST=0.0.0.0
ENV LLM_PORT=4003

# Install system dependencies
RUN apt-get update && apt-get install -y python3.9 python3-dev python3-pip build-essential
#RUN ln -s /usr/bin/python3.9 /usr/bin/python3
RUN rm -rf /var/lib/apt/lists/*

# Set up Python environment
RUN pip3 install --upgrade pip

# Copy the project files to the container
WORKDIR /app
COPY . /app

# Install Python dependencies (requirements.txt should list all your Python libraries)
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Command to run your Python project (replace 'app.py' with your script name)
CMD ["python3", "main.py"]