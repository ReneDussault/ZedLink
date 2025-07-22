"""
ZedLink Network Server
Handles incoming client connections and manages mouse control.
"""

import socket
import threading
import json
import logging
from typing import Optional

class ZedLinkServer:
    """TCP server that receives mouse commands and controls local mouse"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9876, mouse_controller=None):
        self.host = host
        self.port = port
        self.mouse_controller = mouse_controller
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.running = False
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the server and listen for connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.running = True
            self.logger.info(f"ZedLink Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.logger.info(f"Client connected from {addr}")
                    
                    # Handle one client at a time for now
                    if self.client_socket:
                        self.client_socket.close()
                    
                    self.client_socket = client_socket
                    
                    # Start handling client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle messages from connected client"""
        try:
            buffer = ""
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages (newline delimited)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._process_message(line.strip())
        
        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            client_socket.close()
            self.logger.info("Client disconnected")
    
    def _process_message(self, message: str):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "handshake":
                self.logger.info("Handshake received from client")
            elif msg_type == "mouse_move":
                # Move mouse to coordinates
                x, y = data.get("x", 0), data.get("y", 0)
                self.logger.debug(f"Mouse move: ({x:.3f}, {y:.3f})")
                if self.mouse_controller:
                    self.mouse_controller.move_to(x, y)
            elif msg_type == "mouse_click":
                # Handle mouse click
                button = data.get("button", "left")
                pressed = data.get("pressed", True)
                self.logger.debug(f"Mouse {button} {'press' if pressed else 'release'}")
                if self.mouse_controller:
                    self.mouse_controller.click(button, pressed)
            else:
                self.logger.warning(f"Unknown message type: {msg_type}")
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON received: {e}")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Server stopped")
