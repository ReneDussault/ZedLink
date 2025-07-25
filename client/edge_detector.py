"""
Edge Detection System for ZedLink Client

Monitors mouse position and detects when the cursor hits screen edges,
triggering remote control mode with configurable delays and edge preferences.
"""

import time
import threading
from typing import Callable, Optional, Tuple, Dict, Any
from enum import Enum
import logging
import platform

try:
    from pynput import mouse
    from pynput.mouse import Listener as MouseListener
    from pynput import keyboard
    from pynput.keyboard import Listener as KeyboardListener
    PYNPUT_AVAILABLE = True
except ImportError:
    # Don't print warning here - let the calling code handle it
    mouse = None
    MouseListener = None
    keyboard = None
    KeyboardListener = None
    PYNPUT_AVAILABLE = False

# Platform-specific imports for mouse capture
try:
    if platform.system() == "Windows":
        import ctypes
        from ctypes import wintypes
        WINDOWS_CAPTURE_AVAILABLE = True
    else:
        WINDOWS_CAPTURE_AVAILABLE = False
except ImportError:
    WINDOWS_CAPTURE_AVAILABLE = False


class TriggerEdge(Enum):
    """Available edge trigger positions"""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class EdgeDetector:
    """
    Monitors mouse position and detects edge collisions for remote control activation.
    
    Features:
    - Configurable trigger edges
    - Adjustable trigger delay to prevent false positives
    - Smooth transition handling
    - Multi-monitor awareness
    """
    
    def __init__(self, 
                 screen_width: int, 
                 screen_height: int,
                 trigger_edge: TriggerEdge = TriggerEdge.RIGHT,
                 trigger_delay: float = 0.1,
                 edge_threshold: int = 2):
        """
        Initialize the edge detector.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels  
            trigger_edge: Which edge triggers remote control
            trigger_delay: Delay in seconds before trigger activates
            edge_threshold: Pixel distance from edge to consider "at edge"
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.trigger_edge = trigger_edge
        self.trigger_delay = trigger_delay
        self.edge_threshold = edge_threshold
        
        # State tracking
        self.is_monitoring = False
        self.is_at_edge = False
        self.is_remote_mode = False  # New: track if we're in remote mode
        self.edge_start_time = None
        self.last_position = (0, 0)
        self.last_sent_time = 0  # For throttling mouse movements
        self.movement_throttle = 0.008  # ~120 FPS (8ms between updates) - reduced lag
        
        # Callbacks
        self.on_edge_triggered: Optional[Callable[[TriggerEdge, Tuple[int, int]], None]] = None
        self.on_edge_left: Optional[Callable[[], None]] = None
        self.on_mouse_move: Optional[Callable[[int, int], None]] = None  # New: for remote mode
        self.on_mouse_delta: Optional[Callable[[int, int], None]] = None  # New: for relative movement
        self.on_mouse_click: Optional[Callable[[int, int, str, bool], None]] = None  # New: for clicks
        self.on_escape_pressed: Optional[Callable[[], None]] = None  # New: for exiting remote mode
        
        # Threading
        self._mouse_listener = None
        self._keyboard_listener = None  # New: for escape key
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._mouse_controller = None  # For local mouse control
        
        # Initialize local mouse controller for capturing
        if PYNPUT_AVAILABLE and mouse:
            self._mouse_controller = mouse.Controller()
        else:
            self._mouse_controller = None
            
        # Mouse capture state
        self._cursor_hidden = False
        self._capture_bounds = None  # Rectangle to confine cursor
        self._remote_mode_start_pos = None  # Position when remote mode started
        self._last_raw_position = None  # For calculating deltas
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
    def _hide_cursor(self):
        """Hide the local cursor (Windows-specific for now)"""
        if WINDOWS_CAPTURE_AVAILABLE and not self._cursor_hidden:
            try:
                # Hide cursor using Windows API
                ctypes.windll.user32.ShowCursor(False)
                self._cursor_hidden = True
                self.logger.debug("Cursor hidden")
            except Exception as e:
                self.logger.warning(f"Could not hide cursor: {e}")
                
    def _show_cursor(self):
        """Show the local cursor"""
        if WINDOWS_CAPTURE_AVAILABLE and self._cursor_hidden:
            try:
                # Show cursor using Windows API
                ctypes.windll.user32.ShowCursor(True)
                self._cursor_hidden = False
                self.logger.debug("Cursor shown")
            except Exception as e:
                self.logger.warning(f"Could not show cursor: {e}")
                
    def _confine_cursor(self, x: int, y: int, width: int = 1, height: int = 1):
        """Confine cursor to a small area (Windows-specific)"""
        if WINDOWS_CAPTURE_AVAILABLE:
            try:
                # Define a small rectangle to confine the cursor
                rect = wintypes.RECT()
                rect.left = x
                rect.top = y
                rect.right = x + width
                rect.bottom = y + height
                
                # Confine cursor to this rectangle
                ctypes.windll.user32.ClipCursor(ctypes.byref(rect))
                self._capture_bounds = (x, y, width, height)
                self.logger.debug(f"Cursor confined to ({x}, {y}, {width}, {height})")
            except Exception as e:
                self.logger.warning(f"Could not confine cursor: {e}")
                
    def _release_cursor(self):
        """Release cursor confinement"""
        if WINDOWS_CAPTURE_AVAILABLE and self._capture_bounds:
            try:
                # Release cursor confinement
                ctypes.windll.user32.ClipCursor(None)
                self._capture_bounds = None
                self.logger.debug("Cursor confinement released")
            except Exception as e:
                self.logger.warning(f"Could not release cursor: {e}")
        
    def set_screen_dimensions(self, width: int, height: int):
        """Update screen dimensions (useful for resolution changes)"""
        self.screen_width = width
        self.screen_height = height
        self.logger.info(f"Screen dimensions updated: {width}x{height}")
        
    def set_trigger_edge(self, edge: TriggerEdge):
        """Change the trigger edge"""
        self.trigger_edge = edge
        self.logger.info(f"Trigger edge set to: {edge.value}")
        
    def set_trigger_delay(self, delay: float):
        """Change the trigger delay in seconds"""
        self.trigger_delay = max(0.05, min(2.0, delay))  # Clamp between 50ms and 2s
        self.logger.info(f"Trigger delay set to: {self.trigger_delay}s")
        
    def enter_remote_mode(self):
        """Enter remote tracking mode - simple position tracking"""
        self.is_remote_mode = True
        self.logger.info("Entered remote tracking mode")
        
        # Just hide the cursor - keep it simple
        if self._mouse_controller:
            current_pos = self._mouse_controller.position
            self._remote_mode_start_pos = current_pos
            self._last_raw_position = current_pos
            
            # Just hide cursor - no complex capture
            self._hide_cursor()
        
    def exit_remote_mode(self):
        """Exit remote tracking mode - return to edge detection"""
        self.is_remote_mode = False
        self._remote_mode_start_pos = None
        self._last_raw_position = None
        self.logger.info("Exited remote tracking mode")
        
        # Release mouse capture
        self._release_cursor()
        self._show_cursor()
        
    def _is_at_trigger_edge(self, x: int, y: int) -> bool:
        """Check if the mouse position is at the configured trigger edge"""
        if self.trigger_edge == TriggerEdge.TOP:
            return y <= self.edge_threshold
        elif self.trigger_edge == TriggerEdge.BOTTOM:
            return y >= (self.screen_height - self.edge_threshold)
        elif self.trigger_edge == TriggerEdge.LEFT:
            return x <= self.edge_threshold
        elif self.trigger_edge == TriggerEdge.RIGHT:
            return x >= (self.screen_width - self.edge_threshold)
        return False
        
    def _calculate_remote_position(self, x: int, y: int) -> Tuple[int, int]:
        """
        Calculate the corresponding position on the remote screen.
        For now, this is a simple 1:1 mapping. In the future, this could
        handle different screen resolutions and scaling.
        """
        # Simple mapping - could be enhanced with screen resolution scaling
        return (x, y)
        
    def _on_mouse_move(self, x: int, y: int):
        """Handle mouse movement events"""
        self.last_position = (x, y)
        
        # If in remote mode, just track position - keep it simple!
        if self.is_remote_mode:
            if self._last_raw_position is not None:
                # Calculate movement delta for callback
                dx = x - self._last_raw_position[0]
                dy = y - self._last_raw_position[1]
                
                # Send movement update if there's actual movement
                if (dx != 0 or dy != 0):
                    current_time = time.time()
                    if current_time - self.last_sent_time >= self.movement_throttle:
                        if self.on_mouse_delta:
                            self.on_mouse_delta(dx, dy)
                        self.last_sent_time = current_time
            
            # Update position for next calculation
            self._last_raw_position = (x, y)
            return  # Skip edge detection when in remote mode
        
        # Normal edge detection logic
        current_at_edge = self._is_at_trigger_edge(x, y)
        
        if current_at_edge and not self.is_at_edge:
            # Mouse just reached the edge
            self.is_at_edge = True
            self.edge_start_time = time.time()
            self.logger.debug(f"Mouse at edge: {x}, {y}")
            
        elif not current_at_edge and self.is_at_edge:
            # Mouse left the edge
            self.is_at_edge = False
            self.edge_start_time = None
            self.logger.debug(f"Mouse left edge: {x}, {y}")
            
            if self.on_edge_left:
                self.on_edge_left()
        
        if current_at_edge and not self.is_at_edge:
            # Mouse just reached the edge
            self.is_at_edge = True
            self.edge_start_time = time.time()
            self.logger.debug(f"Mouse at edge: {x}, {y}")
            
        elif not current_at_edge and self.is_at_edge:
            # Mouse left the edge
            self.is_at_edge = False
            self.edge_start_time = None
            self.logger.debug(f"Mouse left edge: {x}, {y}")
            
            # Notify that we left the edge
            if self.on_edge_left:
                self.on_edge_left()
                
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events"""
        if not self.is_remote_mode:
            return  # Only forward clicks in remote mode
            
        self.logger.debug(f"Click detected: {button} {'press' if pressed else 'release'} at ({x}, {y})")
        
        # Convert button to string
        button_name = "left"
        try:
            if hasattr(button, 'name'):
                button_name = button.name.lower()
            else:
                button_str = str(button).lower()
                if 'left' in button_str:
                    button_name = "left"
                elif 'right' in button_str:
                    button_name = "right"
                elif 'middle' in button_str:
                    button_name = "middle"
        except Exception as e:
            self.logger.warning(f"Button parsing error: {e}, defaulting to 'left'")
            
        # Forward click to remote
        if self.on_mouse_click:
            self.logger.debug(f"Forwarding click: {button_name} {'press' if pressed else 'release'}")
            self.on_mouse_click(x, y, button_name, pressed)
                
    def _on_key_press(self, key):
        """Handle keyboard key press events"""
        if not self.is_remote_mode:
            return
            
        try:
            # Check for Escape key to exit remote mode
            if keyboard and hasattr(keyboard, 'Key') and key == keyboard.Key.esc:
                if self.on_escape_pressed:
                    self.on_escape_pressed()
        except AttributeError:
            # Handle case where key doesn't have expected attributes
            pass
                
    def _monitor_edge_trigger(self):
        """Monitor for edge trigger activation in a separate thread"""
        while not self._stop_event.is_set():
            if (self.is_at_edge and 
                self.edge_start_time and 
                time.time() - self.edge_start_time >= self.trigger_delay):
                
                # Edge trigger activated!
                x, y = self.last_position
                remote_pos = self._calculate_remote_position(x, y)
                
                self.logger.info(f"Edge trigger activated at {x}, {y} -> remote {remote_pos}")
                
                # Reset edge state to prevent immediate re-trigger
                self.is_at_edge = False
                self.edge_start_time = None
                
                # Notify callback
                if self.on_edge_triggered:
                    self.on_edge_triggered(self.trigger_edge, remote_pos)
                    
            time.sleep(0.01)  # Check every 10ms
            
    def start_monitoring(self):
        """Start monitoring mouse movements for edge detection"""
        if self.is_monitoring:
            self.logger.warning("Edge detector already monitoring")
            return
            
        if not PYNPUT_AVAILABLE:
            raise RuntimeError("pynput not available. Cannot start edge detection.")
            
        self.logger.info(f"Starting edge detection on {self.trigger_edge.value} edge")
        
        # Reset state
        self._stop_event.clear()
        self.is_at_edge = False
        self.edge_start_time = None
        
        # Start mouse listener
        if not MouseListener:
            raise RuntimeError("MouseListener not available")
            
        self._mouse_listener = MouseListener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self._mouse_listener.start()
        
        # Start keyboard listener for escape key
        if KeyboardListener:
            self._keyboard_listener = KeyboardListener(on_press=self._on_key_press)
            self._keyboard_listener.start()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_edge_trigger, daemon=True)
        self._monitor_thread.start()
        
        self.is_monitoring = True
        
    def stop_monitoring(self):
        """Stop monitoring mouse movements"""
        if not self.is_monitoring:
            return
            
        self.logger.info("Stopping edge detection")
        
        # Signal threads to stop
        self._stop_event.set()
        
        # Stop mouse listener
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
            
        # Stop keyboard listener
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
            
        # Wait for monitor thread
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
            
        # Release mouse capture if active
        self._release_cursor()
        self._show_cursor()
        
        self.is_monitoring = False
        
    def get_status(self) -> Dict[str, Any]:
        """Get current detector status for debugging"""
        return {
            "is_monitoring": self.is_monitoring,
            "trigger_edge": self.trigger_edge.value,
            "trigger_delay": self.trigger_delay,
            "screen_size": f"{self.screen_width}x{self.screen_height}",
            "is_at_edge": self.is_at_edge,
            "last_position": self.last_position,
            "edge_threshold": self.edge_threshold
        }
        
    def __del__(self):
        """Cleanup when detector is destroyed"""
        try:
            self.stop_monitoring()
            # Ensure cursor is released
            self._release_cursor()
            self._show_cursor()
        except:
            pass


if __name__ == "__main__":
    """Test the edge detector"""
    import sys
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    def on_trigger(edge, position):
        print(f"TRIGGERED! Edge: {edge.value}, Position: {position}")
        
    def on_left():
        print("Left edge area")
    
    # Create detector for a 1920x1080 screen with right edge trigger
    detector = EdgeDetector(
        screen_width=1920,
        screen_height=1080,
        trigger_edge=TriggerEdge.RIGHT,
        trigger_delay=0.2
    )
    
    detector.on_edge_triggered = on_trigger
    detector.on_edge_left = on_left
    
    try:
        print("Starting edge detection test...")
        print("Move mouse to the right edge and hold for 200ms")
        print("Press Ctrl+C to stop")
        
        detector.start_monitoring()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            status = detector.get_status()
            print(f"Status: monitoring={status['is_monitoring']}, at_edge={status['is_at_edge']}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
        detector.stop_monitoring()
        sys.exit(0)
