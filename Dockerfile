FROM python:3.11-slim

# Install system and build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libvirt-dev \
    libxml2-dev \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libglib2.0-dev \
    libgnutls28-dev \
    libgcrypt20-dev \
    libz-dev \
    libreadline-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libcurl4-openssl-dev \
    python3-tk \
    libx11-6 \
    x11-apps \
    qemu-kvm \
    virtinst \
    libvirt-daemon-system \
    libvirt-clients \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for X11 GUI support
#ENV DISPLAY=:0
#ENV LIBVIRT_DEFAULT_URI=qemu+tcp://192.168.64.2/system

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the app
CMD ["python3", "app2.py"]
