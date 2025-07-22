#!/usr/bin/env python3
"""
ZedLink Client - Main Entry Point
Controls remote PC mouse from this machine via edge triggers and hotkeys.
"""

import sys
import os
import time
import logging
import signal
from typing import Tuple

# Add shared module to path
shared_path = os.path.join(os.path.dirname(__file__), '..')
if shared_path not in sys.path:
    sys.path.append(shared_path)

# Add current directory for local imports  
current_path = os.path.dirname(__file__)
if current_path not in sys.path:
    sys.path.append(current_path)

from network_client import ZedLinkClient
from config import get_config, ZedLinkConfig
from edge_detector import EdgeDetector, TriggerEdge

# Import auto-discovery
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
try:
    from shared.auto_discovery import NetworkDiscovery
    AUTO_DISCOVERY_AVAILABLE = True
except ImportError:
    AUTO_DISCOVERY_AVAILABLE = False

class ZedLinkApp:
    """Main ZedLink application with edge detection and remote control"""
    
    def __init__(self):
        self.config = get_config()
        self.client = ZedLinkClient()
        self.edge_detector = None
        self.is_running = False
        self.is_remote_mode = False
        self._escape_pressed = False  # Flag to prevent duplicate escape handling
        
        # Setup logging
        level = logging.DEBUG if self.config.debug_mode else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
            
        # Initialize auto-discovery if available
        self.auto_discovery = None
        if AUTO_DISCOVERY_AVAILABLE:
            try:
                self.auto_discovery = NetworkDiscovery()
            except Exception as e:
                self.logger.warning(f"Auto-discovery initialization failed: {e}")
            
    def _try_auto_discovery(self) -> bool:
        """Try to auto-discover and configure server connection"""
        if not self.auto_discovery:
            return False
            
        try:
            self.logger.info("🔍 Attempting auto-discovery...")
            if self.config.show_notifications:
                print("🔍 Searching for ZedLink servers...")
                
            servers = self.auto_discovery.scan_for_zedlink_servers(timeout=0.5)
            
            if servers:
                ip, port = servers[0]
                self.logger.info(f"✅ Auto-discovered server: {ip}:{port}")
                
                # Update runtime config (don't save to file automatically)
                self.config.server_host = ip
                self.config.server_port = port
                
                if self.config.show_notifications:
                    print(f"✅ Auto-discovered server: {ip}:{port}")
                    
                return True
            else:
                self.logger.info("❌ No servers found via auto-discovery")
                return False
                
        except Exception as e:
            self.logger.error(f"Auto-discovery failed: {e}")
            return False
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.stop()
        
    def _get_screen_dimensions(self) -> Tuple[int, int]:
        """Get current screen dimensions"""
        try:
            import tkinter as tk
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height
        except Exception:
            # Fallback to common resolution
            self.logger.warning("Could not detect screen size, using 1920x1080")
            return 1920, 1080
            
    def _setup_edge_detector(self):
        """Initialize and configure the edge detector"""
        screen_width, screen_height = self._get_screen_dimensions()
        
        self.edge_detector = EdgeDetector(
            screen_width=screen_width,
            screen_height=screen_height,
            trigger_edge=TriggerEdge(self.config.trigger_edge),
            trigger_delay=self.config.trigger_delay,
            edge_threshold=self.config.edge_threshold
        )
        
        # Setup callbacks
        self.edge_detector.on_edge_triggered = self._on_edge_triggered
        self.edge_detector.on_edge_left = self._on_edge_left
        # Note: Not using on_mouse_move anymore - only delta movement
        self.edge_detector.on_mouse_delta = self._on_mouse_delta  # New: for relative movement
        self.edge_detector.on_mouse_click = self._on_mouse_click  # New: for clicks
        self.edge_detector.on_escape_pressed = self._on_escape_pressed  # New: for exiting remote mode
        
        self.logger.info(f"Edge detector configured: {screen_width}x{screen_height}, "
                        f"trigger={self.config.trigger_edge}, delay={self.config.trigger_delay}s")
        
    def _on_edge_triggered(self, edge: TriggerEdge, position: Tuple[int, int]):
        """Handle edge trigger activation"""
        if self.is_remote_mode:
            self.logger.debug("Already in remote mode, ignoring edge trigger")
            return
            
        self.logger.info(f"Edge triggered: {edge.value} at {position}")
        
        # Connect to server if not connected
        if not self.client.is_connected():
            if not self._connect_to_server():
                return
                
        # Enter remote control mode
        self._enter_remote_mode(position)
        
    def _on_edge_left(self):
        """Handle leaving edge area"""
        if self.is_remote_mode:
            self.logger.info("Left edge area, staying in remote mode")
            # Could implement return-to-local logic here
            
    def _on_mouse_move(self, x: int, y: int):
        """Handle mouse movement in remote mode"""
        if not self.is_remote_mode:
            return
            
        # Convert to relative coordinates and send to server
        if self.edge_detector:
            x_ratio = x / self.edge_detector.screen_width
            y_ratio = y / self.edge_detector.screen_height
            
            # Clamp to 0.0-1.0 range
            x_ratio = max(0.0, min(1.0, x_ratio))
            y_ratio = max(0.0, min(1.0, y_ratio))
            
            self.client.send_mouse_move(x_ratio, y_ratio)
            
    def _on_mouse_delta(self, dx: int, dy: int):
        """Handle relative mouse movement in remote mode"""
        if not self.is_remote_mode:
            return
            
        # Simple approach: send the current mouse position directly
        # Let the server map this to its screen coordinates
        if self.client.is_connected() and self.edge_detector:
            current_x, current_y = self.edge_detector.last_position
            
            # Convert to normalized coordinates (0.0 to 1.0)
            x_ratio = current_x / self.edge_detector.screen_width
            y_ratio = current_y / self.edge_detector.screen_height
            
            # Clamp to valid range
            x_ratio = max(0.0, min(1.0, x_ratio))
            y_ratio = max(0.0, min(1.0, y_ratio))
            
            # Send as absolute position - much simpler!
            success = self.client.send_mouse_move(x_ratio, y_ratio)
            self.logger.debug(f"Sent position: ({current_x}, {current_y}) -> ({x_ratio:.3f}, {y_ratio:.3f})")
            
    def _on_mouse_click(self, x: int, y: int, button: str, pressed: bool):
        """Handle mouse click in remote mode"""
        if not self.is_remote_mode:
            return
            
        self.logger.info(f"Mouse click detected: {button} {'press' if pressed else 'release'} at ({x}, {y})")
        
        # Convert to relative coordinates and send to server
        if self.edge_detector:
            x_ratio = x / self.edge_detector.screen_width
            y_ratio = y / self.edge_detector.screen_height
            
            # Clamp to 0.0-1.0 range
            x_ratio = max(0.0, min(1.0, x_ratio))
            y_ratio = max(0.0, min(1.0, y_ratio))
            
            success = self.client.send_mouse_click(x_ratio, y_ratio, button, pressed)
            self.logger.info(f"Sent click: {button} {'press' if pressed else 'release'} at ({x_ratio:.3f}, {y_ratio:.3f}) - Success: {success}")
            
    def _on_escape_pressed(self):
        """Handle escape key press to exit remote mode"""
        if self.is_remote_mode and not self._escape_pressed:
            self._escape_pressed = True  # Prevent duplicate handling
            self.logger.info("Escape pressed - exiting remote mode")
            self._exit_remote_mode()
            
            # Disconnect from server
            if self.client.is_connected():
                self.client.disconnect()
                
            if self.config.show_notifications:
                print("⌨️  Pressed Escape - remote control deactivated")
            
            # Reset escape flag after a short delay
            import threading
            def reset_escape():
                time.sleep(0.5)
                self._escape_pressed = False
            threading.Thread(target=reset_escape, daemon=True).start()
            
    def _connect_to_server(self) -> bool:
        """Connect to the ZedLink server with auto-discovery fallback"""
        self.logger.info(f"Connecting to server at {self.config.server_host}:{self.config.server_port}")
        
        # Try configured server first
        if self.client.connect(self.config.server_host, self.config.server_port):
            self.logger.info("✅ Connected to configured server")
            return True
        
        # If configured server fails, try auto-discovery
        self.logger.info("❌ Configured server failed, trying auto-discovery...")
        if self._try_auto_discovery():
            # Try connecting to auto-discovered server
            if self.client.connect(self.config.server_host, self.config.server_port):
                self.logger.info("✅ Connected to auto-discovered server")
                return True
        
        # Both failed
        self.logger.error("❌ Failed to connect to any server")
        if self.config.show_notifications:
            print("💡 Make sure the ZedLink server is running on the remote PC")
            print(f"💡 Tried: configured server and auto-discovery")
        return False
            
    def _enter_remote_mode(self, entry_position: Tuple[int, int]):
        """Enter remote control mode"""
        if not self.edge_detector:
            self.logger.error("Edge detector not initialized")
            return
            
        self.is_remote_mode = True
        self._escape_pressed = False  # Reset escape flag when entering remote mode
        self.edge_detector.enter_remote_mode()  # Switch edge detector to remote mode
        self.logger.info(f"🖱️  Entering remote mode at {entry_position}")
        
        if self.config.show_notifications:
            print(f"🔗 Remote control active - controlling {self.config.server_host}")
            
        # Don't send initial position - just start delta tracking to avoid conflicts
        
    def _exit_remote_mode(self):
        """Exit remote control mode"""
        if not self.is_remote_mode:
            return
            
        self.is_remote_mode = False
        if self.edge_detector:
            self.edge_detector.exit_remote_mode()  # Switch back to edge detection mode
        self.logger.info("🖱️  Exiting remote mode")
        
        if self.config.show_notifications:
            print("🔌 Remote control deactivated")
            
    def start(self):
        """Start the ZedLink application"""
        self.logger.info("🚀 Starting ZedLink Client")
        
        if self.config.show_notifications:
            print("🖱️  ZedLink Client v3.0")
            print(f"🎯 Trigger: {self.config.trigger_edge} edge")
            print(f"⏱️  Delay: {self.config.trigger_delay}s")
            print(f"🎯 Server: {self.config.server_host}:{self.config.server_port}")
            
        # Setup edge detection
        self._setup_edge_detector()
        
        if not self.edge_detector:
            self.logger.error("Failed to setup edge detector")
            return
        
        # Start monitoring
        try:
            self.logger.debug("About to start edge monitoring...")
            self.edge_detector.start_monitoring()
            self.logger.debug("Edge monitoring started successfully")
            self.is_running = True
            
            self.logger.info("✅ Edge detection active")
            if self.config.show_notifications:
                print("✅ Ready! Move mouse to screen edge to control remote PC")
                print("Press Ctrl+C to stop")
                
            # Main loop
            while self.is_running:
                time.sleep(0.1)
                
                # Could add periodic tasks here
                # - Connection health checks
                # - Configuration reload
                # - Statistics collection
                
        except Exception as e:
            import traceback
            self.logger.error(f"Error in main loop: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.stop()
            
    def stop(self):
        """Stop the ZedLink application"""
        if not self.is_running:
            return
            
        self.logger.info("🛑 Stopping ZedLink Client")
        self.is_running = False
        
        # Stop edge detection
        if self.edge_detector:
            self.edge_detector.stop_monitoring()
            
        # Disconnect from server
        if self.client.is_connected():
            self.client.disconnect()
            
        if self.config.show_notifications:
            print("👋 ZedLink Client stopped")


def test_basic_connection():
    """Test basic client-server communication (legacy test)"""
    print("🔗 Testing connection to ZedLink Server...")
    
    config = get_config()
    client = ZedLinkClient()
    
    # Try to connect
    if client.connect(config.server_host, config.server_port):
        print("✅ Connected successfully!")
        
        # Send a test mouse movement
        print("📍 Sending test mouse movement...")
        client.send_mouse_move(0.5, 0.5)  # Center of screen
        
        time.sleep(1)
        
        print("🔌 Disconnecting...")
        client.disconnect()
        print("✅ Test complete!")
    else:
        print("❌ Connection failed!")
        print("💡 Make sure the server is running first")

def main():
    """Main entry point for ZedLink Client"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Legacy test mode
        print("🔗 Running legacy connection test...")
        test_basic_connection()
        return
        
    # Normal application mode
    app = ZedLinkApp()
    
    try:
        app.start()
    except KeyboardInterrupt:
        app.logger.info("Interrupted by user")
    except Exception as e:
        app.logger.error(f"Application error: {e}")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
