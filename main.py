#!/usr/bin/env python3
"""
Raspberry Pi Zero 2 W Voice Assistant
Main application entry point.
"""
import yaml
import logging
import sys
import signal
import os
from pathlib import Path
import colorlog

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from audio.input_handler import AudioInputHandler
from audio.output_handler import AudioOutputHandler
from stt.speech_to_text import SpeechToText
from llm.llama_inference import LlamaInference
from utils.bluetooth_setup import BluetoothSetup
from utils.intent_classifier import classify_intent, IntentType
from utils.laptop_client import LaptopBackendConfig, send_laptop_task, download_screenshot
import uuid


class VoiceAssistant:
    """Main voice assistant application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the voice assistant with configuration."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize components
        self.audio_input = None
        self.audio_output = None
        self.stt = None
        self.llm = None
        self.laptop_config = None
        
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing configuration: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get('app', {}).get('log_level', 'INFO'))
        log_file = self.config.get('app', {}).get('log_file', None)
        
        # Create logs directory if needed
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Setup colorlog for console
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)s:%(name)s:%(message)s'
        ))
        
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(handler)
        
        # Add file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            root_logger.addHandler(file_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logging.info("Shutdown signal received, stopping...")
        self.running = False
    
    def _setup_bluetooth(self):
        """Setup Bluetooth audio if configured."""
        bluetooth_config = self.config.get('bluetooth', {})
        device_mac = bluetooth_config.get('device_mac')
        device_name = bluetooth_config.get('device_name')
        auto_connect = bluetooth_config.get('auto_connect', True)
        
        if not (device_mac or device_name):
            logging.info("No Bluetooth device configured, using default audio output")
            return
        
        if not BluetoothSetup.check_bluetooth_available():
            logging.warning("Bluetooth not available, using default audio output")
            return
        
        # List paired devices
        paired_devices = BluetoothSetup.list_paired_devices()
        logging.info(f"Found {len(paired_devices)} paired Bluetooth device(s)")
        
        target_device = None
        if device_mac:
            # Find device by MAC
            for device in paired_devices:
                if device['mac'].upper() == device_mac.upper():
                    target_device = device
                    break
        elif device_name:
            # Find device by name
            for device in paired_devices:
                if device_name.lower() in device['name'].lower():
                    target_device = device
                    break
        
        if target_device and auto_connect:
            logging.info(f"Connecting to Bluetooth device: {target_device['name']} ({target_device['mac']})")
            if BluetoothSetup.connect_device(target_device['mac']):
                # Set as default audio sink
                BluetoothSetup.set_bluetooth_sink(target_device['mac'])
        elif not target_device:
            logging.warning(f"Bluetooth device not found in paired devices")
            logging.info("Available paired devices:")
            for device in paired_devices:
                logging.info(f"  - {device['name']} ({device['mac']})")
    
    def _initialize_components(self):
        """Initialize all assistant components."""
        logging.info("Initializing components...")
        
        # Audio input
        audio_config = self.config.get('audio', {})
        vad_config = self.config.get('vad', {})
        
        self.audio_input = AudioInputHandler(
            sample_rate=audio_config.get('sample_rate', 16000),
            chunk_size=audio_config.get('chunk_size', 1024),
            channels=audio_config.get('channels', 1),
            input_device=audio_config.get('input_device'),
            vad_threshold=vad_config.get('threshold', 0.01),
            silence_duration=vad_config.get('silence_duration', 1.5),
            min_speech_duration=vad_config.get('min_speech_duration', 0.5)
        )
        
        # Speech-to-text
        stt_config = self.config.get('stt', {})
        stt_model_path = stt_config.get('model_path')
        if not stt_model_path:
            raise ValueError("STT model_path not specified in config")
        
        self.stt = SpeechToText(
            model_path=stt_model_path,
            sample_rate=audio_config.get('sample_rate', 16000)
        )
        
        # LLM
        llm_config = self.config.get('llm', {})
        llm_model_path = llm_config.get('model_path')
        if not llm_model_path:
            raise ValueError("LLM model_path not specified in config")
        
        self.llm = LlamaInference(
            model_path=llm_model_path,
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 150),
            top_p=llm_config.get('top_p', 0.9),
            repeat_penalty=llm_config.get('repeat_penalty', 1.1),
            context_window=llm_config.get('context_window', 2048)
        )
        
        # Audio output
        tts_config = self.config.get('tts', {})
        bluetooth_config = self.config.get('bluetooth', {})
        
        self.audio_output = AudioOutputHandler(
            rate=tts_config.get('rate', 150),
            volume=tts_config.get('volume', 0.8),
            voice=tts_config.get('voice'),
            bluetooth_device=bluetooth_config.get('device_mac')
        )
        
        # Serper client removed - using LLM for all intent classification
        
        # Initialize laptop backend config
        laptop_config = self.config.get('laptop', {})
        if laptop_config.get('host'):
            self.laptop_config = LaptopBackendConfig.from_config(self.config)
            logging.info(f"Laptop backend configured: {self.laptop_config.base_url}")
        else:
            logging.warning("Laptop backend not configured - laptop tasks disabled")
            self.laptop_config = None
        
        logging.info("All components initialized")
    
    def _process_question(self, question: str) -> str:
        """
        Process a question by classifying intent and routing to appropriate handler.
        
        Returns:
            Response text to speak, or None if no response
        """
        if not question or not question.strip():
            return None
        
        logging.info(f"Processing question: {question}")
        
        # Classify intent using LLM (pass self.llm instance)
        intent, confidence = classify_intent(question, self.llm)
        logging.info(f"Classified intent: {intent} (confidence: {confidence:.2f})")
        
        # Route to appropriate handler - simplified to just two paths
        if intent == "laptop_action":
            return self._handle_laptop_action(question)
        else:  # local_qa
            return self._handle_local_qa(question)
    
    def _handle_laptop_action(self, question: str) -> str:
        """Handle laptop GUI automation tasks."""
        if not self.laptop_config:
            return "Laptop backend is not configured. Please set laptop host and port in config.yaml."
        
        logging.info(f"Sending laptop task: {question}")
        
        try:
            task_id = str(uuid.uuid4())
            result = send_laptop_task(
                self.laptop_config,
                task_id=task_id,
                user_text=question,
                mode="gui_task",
                options={"send_screenshot": True},
            )
            
            if result["status"] == "done":
                message = result.get("message", "Task completed")
                screenshot_url = result.get("screenshot_url")
                
                # Optionally download screenshot (for future display)
                if screenshot_url:
                    screenshot_dir = Path("./screenshots")
                    screenshot_path = download_screenshot(screenshot_url, screenshot_dir)
                    if screenshot_path:
                        logging.info(f"Screenshot saved to {screenshot_path}")
                
                return f"Task completed: {message}"
            else:
                error_msg = result.get("message", "Unknown error")
                return f"Sorry, the laptop task failed: {error_msg}"
                
        except Exception as e:
            logging.error(f"Error handling laptop action: {e}", exc_info=True)
            return f"Sorry, I couldn't send that task to your laptop: {str(e)}"
    
    def _handle_local_qa(self, question: str) -> str:
        """Handle general questions using local LLM."""
        logging.info("Using local LLM for question")
        response = self.llm.generate(question)
        return response
    
    def run(self):
        """Run the main assistant loop."""
        try:
            # Setup Bluetooth if configured
            self._setup_bluetooth()
            
            # Initialize components
            self._initialize_components()
            
            # Start audio input stream
            self.audio_input.start_stream()
            
            self.running = True
            logging.info("Voice assistant started. Listening for questions...")
            logging.info("Press Ctrl+C to stop")
            
            # Main loop
            while self.running:
                try:
                    # Capture speech
                    audio_data = self.audio_input.capture_speech()
                    
                    if audio_data:
                        # Transcribe speech
                        question = self.stt.transcribe(audio_data)
                        
                        if question:
                            # Process question
                            response = self._process_question(question)
                            
                            if response:
                                # Speak response
                                self.audio_output.speak(response)
                            
                            # Reset STT for next question
                            self.stt.reset()
                        else:
                            logging.debug("No speech recognized")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}", exc_info=True)
                    # Continue running despite errors
        
        except Exception as e:
            logging.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources."""
        logging.info("Cleaning up...")
        
        if self.audio_input:
            self.audio_input.cleanup()
        
        if self.audio_output:
            self.audio_output.cleanup()
        
        if self.stt:
            self.stt.cleanup()
        
        if self.llm:
            self.llm.cleanup()
        
        logging.info("Cleanup complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Raspberry Pi Voice Assistant')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    assistant = VoiceAssistant(config_path=args.config)
    assistant.run()


if __name__ == '__main__':
    main()

