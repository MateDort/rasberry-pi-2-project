"""
Bluetooth audio setup and configuration utilities.
"""
import subprocess
import logging
import re
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class BluetoothSetup:
    """Helper class for Bluetooth audio setup."""
    
    @staticmethod
    def check_bluetooth_available() -> bool:
        """Check if Bluetooth is available on the system."""
        try:
            result = subprocess.run(
                ['which', 'bluetoothctl'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking Bluetooth: {e}")
            return False
    
    @staticmethod
    def list_paired_devices() -> List[Dict[str, str]]:
        """
        List all paired Bluetooth devices.
        
        Returns:
            List of dictionaries with 'mac' and 'name' keys
        """
        devices = []
        
        if not BluetoothSetup.check_bluetooth_available():
            logger.warning("bluetoothctl not available")
            return devices
        
        try:
            result = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse output: "Device MAC_ADDRESS Device Name"
                pattern = r'Device\s+([0-9A-Fa-f:]{17})\s+(.+)'
                for line in result.stdout.split('\n'):
                    match = re.match(pattern, line)
                    if match:
                        devices.append({
                            'mac': match.group(1),
                            'name': match.group(2)
                        })
            
        except subprocess.TimeoutExpired:
            logger.error("bluetoothctl command timed out")
        except Exception as e:
            logger.error(f"Error listing paired devices: {e}")
        
        return devices
    
    @staticmethod
    def connect_device(mac_address: str) -> bool:
        """
        Connect to a Bluetooth device by MAC address.
        
        Args:
            mac_address: MAC address of the device
            
        Returns:
            True if connection successful, False otherwise
        """
        if not BluetoothSetup.check_bluetooth_available():
            logger.error("bluetoothctl not available")
            return False
        
        try:
            # Power on Bluetooth
            subprocess.run(
                ['bluetoothctl', 'power', 'on'],
                capture_output=True,
                timeout=5
            )
            
            # Connect to device
            result = subprocess.run(
                ['bluetoothctl', 'connect', mac_address],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 or 'successful' in result.stdout.lower():
                logger.info(f"Connected to Bluetooth device: {mac_address}")
                return True
            else:
                logger.error(f"Failed to connect to {mac_address}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Bluetooth connection timed out")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Bluetooth device: {e}")
            return False
    
    @staticmethod
    def set_bluetooth_sink(mac_address: Optional[str] = None) -> bool:
        """
        Set Bluetooth device as default audio sink using PulseAudio.
        
        Args:
            mac_address: MAC address of Bluetooth device (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if pactl is available
            result = subprocess.run(
                ['which', 'pactl'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("pactl not found, cannot set Bluetooth sink")
                return False
            
            # List sinks
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sinks'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Failed to list audio sinks")
                return False
            
            # Find Bluetooth sink
            sinks = result.stdout.split('\n')
            bluetooth_sink = None
            
            for sink in sinks:
                if sink and ('bluez' in sink.lower() or 
                           (mac_address and mac_address.replace(':', '_').lower() in sink.lower())):
                    # Extract sink name (first field)
                    bluetooth_sink = sink.split('\t')[1] if '\t' in sink else sink.split()[1]
                    break
            
            if bluetooth_sink:
                # Set as default sink
                result = subprocess.run(
                    ['pactl', 'set-default-sink', bluetooth_sink],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Set Bluetooth sink as default: {bluetooth_sink}")
                    return True
                else:
                    logger.error(f"Failed to set default sink: {result.stderr}")
                    return False
            else:
                logger.warning("Bluetooth audio sink not found")
                return False
                
        except Exception as e:
            logger.error(f"Error setting Bluetooth sink: {e}")
            return False
    
    @staticmethod
    def get_audio_sinks() -> List[Dict[str, str]]:
        """
        List all available audio sinks.
        
        Returns:
            List of dictionaries with 'name' and 'description' keys
        """
        sinks = []
        
        try:
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sinks'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            sinks.append({
                                'name': parts[1],
                                'description': parts[1]  # Simplified
                            })
        except Exception as e:
            logger.error(f"Error listing audio sinks: {e}")
        
        return sinks

