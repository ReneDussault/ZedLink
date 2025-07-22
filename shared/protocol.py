"""
ZedLink Protocol Definitions
Shared message format and communication protocol between client and server.
"""

import json
import time
from typing import Dict, Any, Optional

class MessageType:
    """Message type constants"""
    MOUSE_MOVE = "mouse_move"
    MOUSE_DELTA = "mouse_delta"  # New: for relative movement
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    HANDSHAKE = "handshake"
    DISCONNECT = "disconnect"

class Protocol:
    """Handles message encoding/decoding for ZedLink communication"""
    
    @staticmethod
    def create_mouse_move(x: float, y: float) -> Dict[str, Any]:
        """Create a mouse movement message"""
        return {
            "type": MessageType.MOUSE_MOVE,
            "x": x,  # Relative coordinates 0.0-1.0
            "y": y,
            "timestamp": time.time()
        }
        
    @staticmethod
    def create_mouse_delta(dx: float, dy: float) -> Dict[str, Any]:
        """Create a relative mouse movement message"""
        return {
            "type": MessageType.MOUSE_DELTA,
            "dx": dx,  # Relative movement delta
            "dy": dy,
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_mouse_click(x: float, y: float, button: str, pressed: bool) -> Dict[str, Any]:
        """Create a mouse click message"""
        return {
            "type": MessageType.MOUSE_CLICK,
            "x": x,
            "y": y,
            "button": button,  # "left", "right", "middle"
            "pressed": pressed,  # True for press, False for release
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_handshake(client_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a handshake message"""
        return {
            "type": MessageType.HANDSHAKE,
            "client_info": client_info or {},
            "timestamp": time.time()
        }
    
    @staticmethod
    def encode_message(message: Dict[str, Any]) -> bytes:
        """Encode message to bytes for network transmission"""
        json_str = json.dumps(message)
        return json_str.encode('utf-8') + b'\n'  # Newline delimiter
    
    @staticmethod
    def decode_message(data: bytes) -> Dict[str, Any]:
        """Decode bytes to message dictionary"""
        json_str = data.decode('utf-8').strip()
        return json.loads(json_str)
