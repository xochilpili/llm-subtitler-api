# Base image with CUDA support
FROM nvidia/cuda:12.6.2-cudnn-runtime-ubuntu22.04

# Set environment variables
ENV LLM_HOST=0.0.0.0
ENV LLM_PORT=4003
ENV DEBIAN_FRONTEND=noninteractive 
# Install system dependencies
RUN apt update -y && apt upgrade -y && \
    apt-get install -y wget build-essential checkinstall libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev ffmpeg && \
    cd /usr/src && \
    wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tgz && \
    tar xzf Python-3.9.9.tgz && \
    cd Python-3.9.9 && \
    ./configure --enable-optimizations && \
    make install

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