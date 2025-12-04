#!/bin/bash
# Fix pyaudio installation on Raspberry Pi

echo "Installing system dependencies for pyaudio..."
sudo apt update
sudo apt install -y portaudio19-dev libportaudio2 libasound-dev

echo ""
echo "Reinstalling pyaudio..."
pip3 uninstall -y pyaudio
pip3 install pyaudio

echo ""
echo "Testing pyaudio import..."
python3 -c "import pyaudio; print('✓ pyaudio installed successfully!')" || echo "✗ pyaudio still not working"
