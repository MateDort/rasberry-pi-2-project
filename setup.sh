#!/bin/bash
# Setup script for Raspberry Pi Voice Assistant

set -e

echo "Raspberry Pi Voice Assistant Setup"
echo "==================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-pyaudio \
    portaudio19-dev \
    bluez \
    pulseaudio \
    pulseaudio-module-bluetooth \
    espeak \
    espeak-data \
    build-essential \
    cmake

# Install Python dependencies
echo "Installing Python dependencies..."
echo "Note: llama-cpp-python compilation may take 10-20 minutes on Pi Zero 2 W"
pip3 install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p models
mkdir -p logs

# Set up PulseAudio for Bluetooth
echo "Configuring PulseAudio for Bluetooth..."
sudo usermod -a -G bluetooth $USER || true
sudo usermod -a -G audio $USER || true

# Enable PulseAudio Bluetooth module
if ! grep -q "load-module module-bluetooth-policy" /etc/pulse/default.pa; then
    echo "Adding Bluetooth module to PulseAudio..."
    sudo sed -i '/load-module module-bluetooth-policy/a load-module module-bluetooth-policy' /etc/pulse/default.pa || true
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Download Vosk model:"
echo "   cd models && wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip"
echo "   unzip vosk-model-small-en-us-0.22.zip && rm vosk-model-small-en-us-0.22.zip"
echo ""
echo "2. Download LLM model (choose one):"
echo "   wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
echo "   OR"
echo "   wget https://huggingface.co/microsoft/phi-2-gguf/resolve/main/phi-2.Q4_K_M.gguf"
echo ""
echo "3. Pair your Bluetooth device:"
echo "   bluetoothctl"
echo "   power on"
echo "   scan on"
echo "   pair <MAC_ADDRESS>"
echo "   trust <MAC_ADDRESS>"
echo ""
echo "4. Update config.yaml with model paths and Bluetooth device"
echo ""
echo "5. Run the assistant:"
echo "   python3 main.py"
echo ""




#Quick Setup Commands
# 1. Navigate to your project directory
cd /path/to/rasberry-pi-2-project

# 2. Make setup script executable (if you haven't already)
chmod +x setup.sh

# 3. Run the setup script to install all dependencies
./setup.sh

# 4. Download Vosk speech recognition model
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip
unzip vosk-model-small-en-us-0.22.zip
rm vosk-model-small-en-us-0.22.zip
cd ..

# 5. Download LLM model (choose one - TinyLlama recommended for 1GB RAM)
cd models
# Option A: TinyLlama (~700MB)
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf

# OR Option B: Phi-2 (~800MB)
# wget https://huggingface.co/microsoft/phi-2-gguf/resolve/main/phi-2.Q4_K_M.gguf

cd ..

# 6. Pair your Bluetooth device (replace with your device's MAC address)
bluetoothctl
# Then in bluetoothctl:
#   power on
#   scan on
#   (wait for your device, note the MAC address)
#   pair <MAC_ADDRESS>
#   trust <MAC_ADDRESS>
#   connect <MAC_ADDRESS>
#   quit

# 7. Update config.yaml with your Bluetooth device MAC address
# Edit config.yaml and set the bluetooth.device_mac field

# 8. Run the voice assistant
python3 main.py


#All-in-One Setup Script
#!/bin/bash
# Complete setup and run script for Raspberry Pi Voice Assistant

set -e

echo "=== Raspberry Pi Voice Assistant Setup ==="

# Navigate to project directory
cd "$(dirname "$0")"

# Step 1: Install system dependencies
echo "Step 1: Installing system dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3-pip \
    python3-pyaudio \
    portaudio19-dev \
    bluez \
    pulseaudio \
    pulseaudio-module-bluetooth \
    espeak \
    espeak-data \
    build-essential \
    cmake

# Step 2: Install Python packages
echo "Step 2: Installing Python packages (this may take 10-20 minutes)..."
pip3 install -r requirements.txt

# Step 3: Create directories
echo "Step 3: Creating directories..."
mkdir -p models logs

# Step 4: Download Vosk model
echo "Step 4: Downloading Vosk model..."
if [ ! -d "models/vosk-model-small-en-us-0.22" ]; then
    cd models
    wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip
    unzip -q vosk-model-small-en-us-0.22.zip
    rm vosk-model-small-en-us-0.22.zip
    cd ..
    echo "Vosk model downloaded"
else
    echo "Vosk model already exists"
fi

# Step 5: Download LLM model
echo "Step 5: Downloading LLM model..."
cd models
if [ ! -f "TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf" ]; then
    echo "Downloading TinyLlama (this may take a while)..."
    wget -q --show-progress https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf
    echo "LLM model downloaded"
else
    echo "LLM model already exists"
fi
cd ..

# Step 6: Configure PulseAudio for Bluetooth
echo "Step 6: Configuring PulseAudio..."
sudo usermod -a -G bluetooth $USER || true
sudo usermod -a -G audio $USER || true

# Step 7: Check config
echo ""
echo "=== Setup Complete ==="
echo ""
echo "IMPORTANT: Before running, you need to:"
echo "1. Pair your Bluetooth device:"
echo "   bluetoothctl"
echo "   power on"
echo "   scan on"
echo "   pair <MAC_ADDRESS>"
echo "   trust <MAC_ADDRESS>"
echo ""
echo "2. Update config.yaml with your Bluetooth device MAC address"
echo ""
echo "3. Then run: python3 main.py"
echo ""


#Daily Usage Commands
# Start the voice assistant
cd /path/to/rasberry-pi-2-project
python3 main.py

# Or with custom config
python3 main.py --config custom_config.yaml

# Check available audio devices
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"

# List paired Bluetooth devices
bluetoothctl devices

# Connect to Bluetooth device
bluetoothctl connect <MAC_ADDRESS>

# Check audio sinks
pactl list short sinks

# Set default audio sink (if needed)
pactl set-default-sink <SINK_NAME>


#Troubleshooting Commands
# Check if microphone is working
arecord -d 3 test.wav && aplay test.wav

# Test Bluetooth audio
pactl list short sinks | grep bluez

# Restart PulseAudio (if audio issues)
pulseaudio -k
pulseaudio --start

# Check Python dependencies
pip3 list | grep -E "llama|vosk|pyaudio|pyttsx3"

# View logs
tail -f logs/assistant.log

