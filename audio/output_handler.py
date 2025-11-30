"""
Audio output handler for text-to-speech and Bluetooth audio routing.
"""
import pyttsx3
import logging
import subprocess
import os
from typing import Optional

logger = logging.getLogger(__name__)


class AudioOutputHandler:
    """Handles text-to-speech and audio output routing."""
    
    def __init__(
        self,
        rate: int = 150,
        volume: float = 0.8,
        voice: Optional[str] = None,
        bluetooth_device: Optional[str] = None
    ):
        """
        Initialize audio output handler.
        
        Args:
            rate: Speech rate in words per minute
            volume: Volume level (0.0 to 1.0)
            voice: Voice name (None = default)
            bluetooth_device: Bluetooth device MAC address or name
        """
        self.rate = rate
        self.volume = volume
        self.voice = voice
        self.bluetooth_device = bluetooth_device
        
        # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self._configure_tts()
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
        
        # Configure Bluetooth audio if device specified
        if self.bluetooth_device:
            self._setup_bluetooth_audio()
    
    def _configure_tts(self):
        """Configure TTS engine settings."""
        # Set rate
        self.tts_engine.setProperty('rate', self.rate)
        
        # Set volume
        self.tts_engine.setProperty('volume', self.volume)
        
        # Set voice if specified
        if self.voice:
            voices = self.tts_engine.getProperty('voices')
            for v in voices:
                if self.voice.lower() in v.name.lower():
                    self.tts_engine.setProperty('voice', v.id)
                    logger.info(f"Voice set to: {v.name}")
                    break
        else:
            # Use default voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                logger.info(f"Using default voice: {voices[0].name}")
    
    def _setup_bluetooth_audio(self):
        """Set up Bluetooth audio output routing."""
        try:
            # Check if PulseAudio is available
            result = subprocess.run(
                ['which', 'pactl'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("pactl not found, Bluetooth audio routing may not work")
                return
            
            # List available sinks
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sinks'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                sinks = result.stdout
                # Look for Bluetooth sink
                if 'bluez' in sinks.lower() or self.bluetooth_device.lower() in sinks.lower():
                    logger.info("Bluetooth audio sink detected")
                    # Set as default sink
                    # Note: This may need adjustment based on actual device name
                    # User should configure this manually or via bluetooth_setup.py
                else:
                    logger.warning("Bluetooth audio sink not found, using default output")
            
        except Exception as e:
            logger.warning(f"Could not set up Bluetooth audio: {e}")
    
    def speak(self, text: str, wait: bool = True):
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            wait: If True, wait for speech to complete before returning
        """
        if not text or not text.strip():
            return
        
        try:
            logger.info(f"Speaking: {text[:50]}...")
            self.tts_engine.say(text)
            
            if wait:
                self.tts_engine.runAndWait()
            else:
                self.tts_engine.startLoop(False)
                self.tts_engine.iterate()
                self.tts_engine.endLoop()
                
        except Exception as e:
            logger.error(f"Error during TTS: {e}")
    
    def stop(self):
        """Stop current speech output."""
        try:
            self.tts_engine.stop()
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")
    
    def set_rate(self, rate: int):
        """Update speech rate."""
        self.rate = rate
        self.tts_engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Update volume level."""
        self.volume = max(0.0, min(1.0, volume))
        self.tts_engine.setProperty('volume', self.volume)
    
    def list_voices(self):
        """List available TTS voices."""
        voices = self.tts_engine.getProperty('voices')
        voice_list = []
        for voice in voices:
            voice_list.append({
                'id': voice.id,
                'name': voice.name,
                'languages': getattr(voice, 'languages', [])
            })
        return voice_list
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.tts_engine.stop()
        except:
            pass
        logger.info("Audio output handler cleaned up")

