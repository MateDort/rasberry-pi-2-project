# Raspberry Pi Zero 2 W Voice Assistant

A lightweight voice assistant that continuously listens for questions via microphone, processes them with a quantized LLaMA model, and responds through Bluetooth audio output.

## Features

- **Offline Speech Recognition**: Uses Vosk for local, privacy-preserving speech-to-text
- **Lightweight LLM**: Runs quantized LLaMA models (TinyLlama, Phi-2) optimized for 1GB RAM
- **Local Text-to-Speech**: Uses pyttsx3 with espeak for offline voice synthesis
- **Bluetooth Audio**: Supports Bluetooth speakers and AirPods for audio output
- **Continuous Listening**: Always-on voice activity detection for hands-free operation

## Hardware Requirements

- Raspberry Pi Zero 2 W (1GB RAM)
- USB microphone (or compatible audio input)
- Bluetooth speaker or AirPods (for audio output)
- MicroSD card (16GB+ recommended)

## Software Requirements

### System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install audio dependencies
sudo apt install -y python3-pyaudio portaudio19-dev

# Install Bluetooth support
sudo apt install -y bluez pulseaudio-module-bluetooth

# Install TTS backend
sudo apt install -y espeak espeak-data

# Install Python build dependencies (for llama-cpp-python)
sudo apt install -y build-essential cmake
```

### Python Dependencies

Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

**Note**: `llama-cpp-python` may take a while to compile on the Pi. For faster installation, you can use pre-built wheels if available for your architecture.

## Model Setup

### 1. Download Vosk Speech Recognition Model

Download a lightweight Vosk model (recommended for 1GB RAM):

```bash
mkdir -p models
cd models

# Download small English model (~50MB)
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip
unzip vosk-model-small-en-us-0.22.zip
rm vosk-model-small-en-us-0.22.zip
```

### 2. Download LLM Model

Download a quantized LLaMA model suitable for 1GB RAM:

**Option A: TinyLlama (Recommended - ~700MB)**
```bash
cd models
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf
```

**Option B: Phi-2 (~800MB)**
```bash
cd models
wget https://huggingface.co/microsoft/phi-2-gguf/resolve/main/phi-2.Q4_K_M.gguf
```

**Note**: Ensure you have enough free space on your SD card. Models can be 700MB-1GB in size.

## Configuration

Edit `config.yaml` to configure your setup:

1. **Audio Input**: Set `input_device` if you need to specify a specific microphone
2. **Model Paths**: Update paths to your downloaded models
3. **Bluetooth**: Configure your Bluetooth device MAC address or name
4. **TTS Settings**: Adjust speech rate and volume

### Finding Audio Device Index

To find your microphone device index:

```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"
```

### Bluetooth Setup

1. **Pair your Bluetooth device**:
   ```bash
   bluetoothctl
   power on
   scan on
   # Wait for your device to appear, note the MAC address
   pair <MAC_ADDRESS>
   trust <MAC_ADDRESS>
   connect <MAC_ADDRESS>
   quit
   ```

2. **Update config.yaml** with your device's MAC address or name

3. **Test Bluetooth audio**:
   ```bash
   # List audio sinks
   pactl list short sinks
   
   # Set Bluetooth as default (if needed)
   pactl set-default-sink <BLUETOOTH_SINK_NAME>
   ```

## Usage

### Basic Usage

Run the assistant:

```bash
python3 main.py
```

The assistant will:
1. Initialize all components
2. Connect to Bluetooth device (if configured)
3. Start listening for questions
4. Process questions and respond via TTS

### Command Line Options

```bash
python3 main.py --config custom_config.yaml
```

### Stopping the Assistant

Press `Ctrl+C` to gracefully stop the assistant.

## Project Structure

```
rasberry-pi-2-project/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── main.py                  # Main application
├── audio/
│   ├── input_handler.py     # Microphone capture and VAD
│   └── output_handler.py    # TTS and audio output
├── stt/
│   └── speech_to_text.py    # Vosk speech recognition
├── llm/
│   └── llama_inference.py   # LLM inference
└── utils/
    └── bluetooth_setup.py   # Bluetooth utilities
```

## Troubleshooting

### Audio Input Issues

- **No microphone detected**: Check USB microphone connection and permissions
- **Permission denied**: Add user to `audio` group: `sudo usermod -a -G audio $USER`
- **Wrong device**: List devices and update `input_device` in config.yaml

### Bluetooth Issues

- **Device not connecting**: Ensure device is paired first with `bluetoothctl`
- **No audio output**: Check PulseAudio sink: `pactl list short sinks`
- **Audio routing**: Manually set sink: `pactl set-default-sink <SINK_NAME>`

### Model Loading Issues

- **Out of memory**: Use smaller quantized models (Q4_K_M or smaller)
- **Model not found**: Verify model paths in config.yaml
- **Slow inference**: This is normal on Pi Zero 2 W; responses may take 5-15 seconds

### Performance Tips

1. **Use smaller models**: Q4_K_M quantization is recommended for 1GB RAM
2. **Reduce context window**: Lower `context_window` in config if memory is tight
3. **Optimize VAD**: Adjust `silence_duration` to reduce false triggers
4. **Close other applications**: Free up RAM for the assistant

## Future Enhancements

- ElevenLabs voice integration (requires API key and internet)
- Wake word detection (Porcupine or similar)
- Conversation history and context
- Multiple language support
- Web interface for configuration

## License

This project is provided as-is for educational and personal use.

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) for efficient LLM inference
- [Vosk](https://alphacephei.com/vosk/) for offline speech recognition
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) for text-to-speech

