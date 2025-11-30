"""
Speech-to-text module using Vosk for offline speech recognition.
"""
import json
import logging
import os
from typing import Optional
import numpy as np

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logging.warning("Vosk not available. Install with: pip install vosk")

logger = logging.getLogger(__name__)


class SpeechToText:
    """Handles speech-to-text conversion using Vosk."""
    
    def __init__(self, model_path: str, sample_rate: int = 16000):
        """
        Initialize speech-to-text engine.
        
        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate (must match model's expected rate)
        """
        if not VOSK_AVAILABLE:
            raise ImportError("Vosk is not installed. Install with: pip install vosk")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, sample_rate)
            self.sample_rate = sample_rate
            logger.info(f"Vosk model loaded from: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            raise
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, mono)
            
        Returns:
            Transcribed text or None if recognition failed
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Process audio in chunks
            chunk_size = 4000
            text_result = None
            
            for i in range(0, len(audio_array), chunk_size):
                chunk = audio_array[i:i + chunk_size]
                chunk_bytes = chunk.tobytes()
                
                if self.recognizer.AcceptWaveform(chunk_bytes):
                    # Final result
                    result = json.loads(self.recognizer.Result())
                    if 'text' in result and result['text']:
                        text_result = result['text']
                else:
                    # Partial result
                    partial = json.loads(self.recognizer.PartialResult())
                    if 'partial' in partial and partial['partial']:
                        logger.debug(f"Partial: {partial['partial']}")
            
            # Get final result if not already obtained
            if text_result is None:
                final_result = json.loads(self.recognizer.FinalResult())
                if 'text' in final_result and final_result['text']:
                    text_result = final_result['text']
            
            if text_result:
                logger.info(f"Transcribed: {text_result}")
                return text_result.strip()
            else:
                logger.debug("No text recognized")
                return None
                
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    
    def reset(self):
        """Reset recognizer state (useful for continuous recognition)."""
        try:
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        except Exception as e:
            logger.error(f"Error resetting recognizer: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        # Vosk models don't need explicit cleanup
        logger.info("Speech-to-text handler cleaned up")

