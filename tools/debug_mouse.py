#!/usr/bin/env python3
"""
Debug script to test mouse movement on the server side
Run this on your Linux Mint machine to test if mouse control works
"""

import sys
import time
from server.mouse_controller import MouseController

def test_mouse_movement():
    """Test basic mouse movement"""
    print("🖱️  Testing mouse movement...")
    
    # Create controller
    controller = MouseController()
    print(f"Screen size: {controller.get_screen_size()}")
    
    if not controller.controller:
        print("❌ Mouse controller not available!")
        print("   Make sure pynput is installed: pip install pynput")
        return False
    
    print("✅ Mouse controller ready")
    
    # Test movements
    movements = [
        (0.5, 0.5, "Center"),
        (0.1, 0.1, "Top-left"),
        (0.9, 0.1, "Top-right"),
        (0.9, 0.9, "Bottom-right"),
        (0.1, 0.9, "Bottom-left"),
        (0.5, 0.5, "Center again")
    ]
    
    print("\n🎯 Starting mouse movement test...")
    print("   Watch your mouse cursor - it should move around the screen")
    print("   Press Ctrl+C to stop")
    
    try:
        for i, (x, y, description) in enumerate(movements):
            print(f"   {i+1}. Moving to {description} ({x}, {y})")
            controller.move_to(x, y)
            time.sleep(1.5)
    
        print("\n✅ Mouse movement test completed!")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
        return False
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False

def test_mouse_clicks():
    """Test mouse clicking"""
    print("\n🖱️  Testing mouse clicks...")
    
    controller = MouseController()
    
    if not controller.controller:
        print("❌ Mouse controller not available!")
        return False
    
    try:
        # Move to center and click
        print("   Moving to center and clicking...")
        controller.move_to(0.5, 0.5)
        time.sleep(0.5)
        
        # Left click
        controller.click("left", True)   # Press
        time.sleep(0.1)
        controller.click("left", False)  # Release
        
        print("✅ Mouse click test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Click test error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ZedLink Mouse Controller Debug Tool")
    print("=====================================")
    
    # Test mouse movement
    if test_mouse_movement():
        # Test mouse clicks
        test_mouse_clicks()
    
    print("\n📋 Debug Summary:")
    print("   If the mouse moved: ✅ Mouse control works")
    print("   If the mouse didn't move: ❌ Check pynput installation or permissions")
    print("   If you got permission errors: Run with sudo or check X11 permissions")
