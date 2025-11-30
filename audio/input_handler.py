"""
Audio input handler for microphone capture and voice activity detection.
"""
import pyaudio
import numpy as np
import logging
from typing import Optional, Callable
import time

logger = logging.getLogger(__name__)


class AudioInputHandler:
    """Handles microphone input and voice activity detection."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        input_device: Optional[int] = None,
        vad_threshold: float = 0.01,
        silence_duration: float = 1.5,
        min_speech_duration: float = 0.5
    ):
        """
        Initialize audio input handler.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 = mono)
            input_device: Audio device index (None = default)
            vad_threshold: Energy threshold for speech detection
            silence_duration: Seconds of silence before processing
            min_speech_duration: Minimum speech duration to process
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.input_device = input_device
        self.vad_threshold = vad_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_listening = False
        
        # VAD state
        self.speech_buffer = []
        self.last_speech_time = None
        self.speech_start_time = None
        
    def list_audio_devices(self):
        """List available audio input devices."""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        return devices
    
    def start_stream(self):
        """Start audio input stream."""
        if self.stream is not None:
            logger.warning("Stream already started")
            return
        
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=self.chunk_size
            )
            self.is_listening = True
            logger.info(f"Audio stream started (device: {self.input_device}, rate: {self.sample_rate}Hz)")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            raise
    
    def stop_stream(self):
        """Stop audio input stream."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.is_listening = False
        logger.info("Audio stream stopped")
    
    def _calculate_energy(self, audio_data: np.ndarray) -> float:
        """Calculate RMS energy of audio chunk."""
        return np.sqrt(np.mean(audio_data**2))
    
    def _is_speech(self, audio_data: np.ndarray) -> bool:
        """Detect if audio chunk contains speech based on energy threshold."""
        energy = self._calculate_energy(audio_data)
        return energy > self.vad_threshold
    
    def read_chunk(self) -> Optional[bytes]:
        """Read a single audio chunk from the stream."""
        if not self.is_listening or self.stream is None:
            return None
        
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            return data
        except Exception as e:
            logger.error(f"Error reading audio chunk: {e}")
            return None
    
    def capture_speech(
        self,
        on_speech_start: Optional[Callable] = None,
        on_speech_end: Optional[Callable] = None
    ) -> Optional[bytes]:
        """
        Continuously capture audio and return speech segment when silence detected.
        
        Args:
            on_speech_start: Callback when speech is detected
            on_speech_end: Callback when speech ends
            
        Returns:
            Audio data as bytes when speech segment is complete, None otherwise
        """
        if not self.is_listening:
            return None
        
        current_time = time.time()
        chunk = self.read_chunk()
        
        if chunk is None:
            return None
        
        # Convert to numpy array for processing
        audio_array = np.frombuffer(chunk, dtype=np.int16)
        is_speaking = self._is_speech(audio_array)
        
        if is_speaking:
            # Speech detected
            if self.speech_start_time is None:
                # Speech just started
                self.speech_start_time = current_time
                self.speech_buffer = []
                if on_speech_start:
                    on_speech_start()
                logger.debug("Speech detected")
            
            self.speech_buffer.append(chunk)
            self.last_speech_time = current_time
        
        elif self.speech_start_time is not None:
            # We were recording speech, check if silence is long enough
            silence_duration = current_time - self.last_speech_time
            
            if silence_duration >= self.silence_duration:
                # Silence duration met, process the speech
                speech_duration = self.last_speech_time - self.speech_start_time
                
                if speech_duration >= self.min_speech_duration:
                    # Valid speech segment
                    audio_data = b''.join(self.speech_buffer)
                    self.speech_buffer = []
                    self.speech_start_time = None
                    
                    if on_speech_end:
                        on_speech_end()
                    
                    logger.info(f"Speech segment captured ({speech_duration:.2f}s)")
                    return audio_data
                else:
                    # Too short, discard
                    logger.debug(f"Speech segment too short ({speech_duration:.2f}s), discarding")
                    self.speech_buffer = []
                    self.speech_start_time = None
        
        return None
    
    def capture_continuous(self, duration: float) -> bytes:
        """
        Capture audio for a fixed duration.
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Audio data as bytes
        """
        chunks = []
        num_chunks = int(self.sample_rate / self.chunk_size * duration)
        
        for _ in range(num_chunks):
            chunk = self.read_chunk()
            if chunk:
                chunks.append(chunk)
        
        return b''.join(chunks)
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_stream()
        if self.audio is not None:
            self.audio.terminate()
            self.audio = None
        logger.info("Audio input handler cleaned up")

