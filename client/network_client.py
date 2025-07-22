"""
ZedLink Network Client
Connects to ZedLink server and sends mouse commands.
"""

import socket
import json
import logging
import threading
import time
from typing import Optional, Callable

from shared.protocol import Protocol

class ZedLinkClient:
    """TCP client that sends mouse commands to ZedLink server"""
    
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = 9876):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        
        # Callbacks for connection events
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Connect to the ZedLink server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            
            self.logger.info(f"Connecting to {self.server_ip}:{self.server_port}...")
            self.socket.connect((self.server_ip, self.server_port))
            
            self.connected = True
            self.running = True
            
            # Send handshake
            handshake = Protocol.create_handshake({"client": "ZedLink"})
            self._send_message(handshake)
            
            self.logger.info("Connected to ZedLink server")
            
            if self.on_connected:
                self.on_connected()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.logger.info("Disconnected from server")
        
        if self.on_disconnected:
            self.on_disconnected()
    
    def send_mouse_move(self, x: float, y: float):
        """Send mouse movement command to server"""
        if not self.connected:
            return False
        
        message = Protocol.create_mouse_move(x, y)
        return self._send_message(message)
    
    def send_mouse_click(self, x: float, y: float, button: str, pressed: bool):
        """Send mouse click command to server"""
        if not self.connected:
            return False
        
        message = Protocol.create_mouse_click(x, y, button, pressed)
        return self._send_message(message)
    
    def _send_message(self, message: dict) -> bool:
        """Send a message to the server"""
        if not self.socket or not self.connected:
            return False
        
        try:
            data = Protocol.encode_message(message)
            self.socket.send(data)
            return True
        
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            self.disconnect()
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to server"""
        return self.connected
