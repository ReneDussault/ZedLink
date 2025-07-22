#!/usr/bin/env python3
"""
Multi-monitor screen detection and edge calculation for ZedLink
"""

import sys
import os

# Add current directory for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'client'))

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("tkinter not available")
    tk = None

def get_detailed_screen_info():
    """Get detailed information about all monitors"""
    if not tk:
        return None
    
    root = tk.Tk()
    
    # Get primary screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    print(f"🖥️  Primary Screen: {screen_width}x{screen_height}")
    
    # Try to get virtual screen dimensions (all monitors combined)
    try:
        # This should give us the virtual desktop size
        virtual_width = root.winfo_vrootwidth() if hasattr(root, 'winfo_vrootwidth') else screen_width
        virtual_height = root.winfo_vrootheight() if hasattr(root, 'winfo_vrootheight') else screen_height
        
        print(f"🖥️🖥️ Virtual Desktop: {virtual_width}x{virtual_height}")
        
        if virtual_width > screen_width:
            print(f"✅ Multi-monitor setup detected!")
            print(f"   - Primary: {screen_width}x{screen_height}")
            print(f"   - Total width: {virtual_width}")
            print(f"   - Additional width: {virtual_width - screen_width}")
    except:
        virtual_width = screen_width
        virtual_height = screen_height
    
    root.destroy()
    
    return {
        'primary_width': screen_width,
        'primary_height': screen_height,
        'virtual_width': virtual_width,
        'virtual_height': virtual_height,
        'is_multi_monitor': virtual_width > screen_width or virtual_height > screen_height
    }

def calculate_edge_positions(screen_info):
    """Calculate the correct edge positions for triggers"""
    if not screen_info:
        return None
    
    primary_w = screen_info['primary_width']
    primary_h = screen_info['primary_height']
    virtual_w = screen_info['virtual_width']
    virtual_h = screen_info['virtual_height']
    
    # Edge positions
    edges = {
        'left': 0,
        'right': primary_w - 1,  # Right edge of PRIMARY monitor
        'top': 0,
        'bottom': primary_h - 1,
        'virtual_right': virtual_w - 1,  # Right edge of ALL monitors
    }
    
    print(f"\n🎯 Edge Trigger Positions:")
    print(f"   Left edge: x = {edges['left']}")
    print(f"   Right edge (primary): x = {edges['right']}")
    if screen_info['is_multi_monitor']:
        print(f"   Right edge (all monitors): x = {edges['virtual_right']}")
    print(f"   Top edge: y = {edges['top']}")
    print(f"   Bottom edge: y = {edges['bottom']}")
    
    return edges

def test_mouse_position():
    """Test current mouse position relative to screen edges"""
    try:
        from pynput import mouse
        
        def on_move(x, y):
            print(f"🖱️  Mouse: ({x}, {y})")
            
        def on_click(x, y, button, pressed):
            if pressed:
                print(f"🖱️  Click at: ({x}, {y}) - stopping")
                return False  # Stop listener
        
        print(f"\n🖱️  Mouse position test:")
        print(f"   Move mouse around to see coordinates")
        print(f"   Click anywhere to stop")
        
        with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
            listener.join()
            
    except ImportError:
        print("pynput not available for mouse testing")

def main():
    print("🖥️  ZedLink Multi-Monitor Edge Detection")
    print("=" * 50)
    
    # Get screen info
    screen_info = get_detailed_screen_info()
    
    if not screen_info:
        print("❌ Could not detect screen information")
        return
    
    # Calculate edges
    edges = calculate_edge_positions(screen_info)
    
    if not edges:
        print("❌ Could not calculate edge positions")
        return
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if screen_info['is_multi_monitor']:
        print(f"   • For primary monitor edge: use x = {edges['right']}")
        print(f"   • For rightmost monitor edge: use x = {edges['virtual_right']}")
        print(f"   • Consider using 'left' edge instead for easier access")
    else:
        print(f"   • Single monitor detected - standard edge detection should work")
    
    # Test mouse if available
    try:
        choice = input(f"\n🖱️  Test mouse position tracking? (y/n): ").lower()
        if choice == 'y':
            test_mouse_position()
    except:
        pass

if __name__ == "__main__":
    main()
