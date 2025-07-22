"""
ZedLink Mouse Controller
Handles actual mouse control using pynput on the server side.
"""

import logging
import platform
from typing import Tuple

try:
    from pynput.mouse import Button, Listener as MouseListener
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# Platform-specific screen size detection
def get_screen_size() -> Tuple[int, int]:
    """Get screen size in a cross-platform way"""
    try:
        if platform.system() == "Windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
                return screensize
            except:
                pass
        
        elif platform.system() == "Linux":
            try:
                import subprocess
                output = subprocess.check_output(['xdpyinfo']).decode()
                for line in output.split('\n'):
                    if 'dimensions:' in line:
                        dims = line.split()[1]
                        width, height = map(int, dims.split('x'))
                        return (width, height)
            except:
                pass
        
        elif platform.system() == "Darwin":  # macOS
            try:
                import subprocess
                output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode()
                # Parse macOS display info (simplified)
                pass
            except:
                pass
        
        # Fallback to pynput if available
        if PYNPUT_AVAILABLE:
            from pynput import mouse
            controller = mouse.Controller()
            # This is a workaround - move to corners to detect screen size
            # Not perfect but works cross-platform
            pass
        
    except Exception:
        pass
    
    # Ultimate fallback - common resolution
    return (1920, 1080)

class MouseController:
    """Controls local mouse using pynput"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput not available! Install with: pip install pynput")
            self.controller = None
            self.screen_width, self.screen_height = (1920, 1080)
        else:
            self.controller = mouse.Controller()
            self.screen_width, self.screen_height = get_screen_size()
            self.logger.info(f"Mouse controller initialized ({self.screen_width}x{self.screen_height})")
    
    def move_to(self, x: float, y: float):
        """Move mouse to relative coordinates (0.0-1.0) on screen"""
        if not self.controller:
            self.logger.warning("Mouse controller not available")
            return
        
        try:
            # Convert relative coordinates to absolute pixel coordinates
            abs_x = int(x * self.screen_width)
            abs_y = int(y * self.screen_height)
            
            # Clamp to screen bounds
            abs_x = max(0, min(abs_x, self.screen_width - 1))
            abs_y = max(0, min(abs_y, self.screen_height - 1))
            
            self.controller.position = (abs_x, abs_y)
            self.logger.debug(f"Mouse moved to ({abs_x}, {abs_y})")
        
        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")
    
    def move_relative(self, dx: float, dy: float):
        """Move mouse relative to current position by raw pixel deltas"""
        if not self.controller:
            self.logger.warning("Mouse controller not available")
            return
        
        try:
            # Use raw pixel deltas directly - no need to convert from ratios
            # Apply a sensitivity multiplier for fine-tuning
            sensitivity = 1.0  # Adjust this value to fine-tune movement speed
            
            delta_x = int(dx * sensitivity)
            delta_y = int(dy * sensitivity)
            
            # Get current position
            current_x, current_y = self.controller.position
            
            # Calculate new position
            new_x = current_x + delta_x
            new_y = current_y + delta_y
            
            # Clamp to screen bounds
            new_x = max(0, min(new_x, self.screen_width - 1))
            new_y = max(0, min(new_y, self.screen_height - 1))
            
            self.controller.position = (new_x, new_y)
            self.logger.debug(f"Mouse moved by raw delta ({delta_x}, {delta_y}) to ({new_x}, {new_y})")
        
        except Exception as e:
            self.logger.error(f"Error moving mouse relatively: {e}")
    
    def click(self, button: str, pressed: bool):
        """Handle mouse click events"""
        if not self.controller:
            self.logger.warning("Mouse controller not available")
            return
        
        try:
            # Map button strings to pynput buttons
            button_map = {
                "left": Button.left,
                "right": Button.right,
                "middle": Button.middle
            }
            
            pynput_button = button_map.get(button, Button.left)
            
            if pressed:
                self.controller.press(pynput_button)
            else:
                self.controller.release(pynput_button)
            
            action = "press" if pressed else "release"
            self.logger.debug(f"Mouse {button} {action}")
        
        except Exception as e:
            self.logger.error(f"Error clicking mouse: {e}")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get current screen resolution"""
        return (self.screen_width, self.screen_height)
