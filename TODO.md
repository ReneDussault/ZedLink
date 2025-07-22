# ZedLink - Remote Mouse Control Tool

## Project Overview

A lightweight tool to control a Linux Mint PC's mouse pointer from a Windows/Ubuntu main PC using edge triggers and hotkey fallbacks.

## Architecture

- **Client**: Windows/Ubuntu main PC (captures & sends mouse events)
- **Server**: Linux Mint small PC (receives & executes mouse commands)
- **Communication**: TCP sockets with JSON protocol
- **Dependencies**: pynput + Python standard library

---

## Development Roadmap

### Phase 1: Core Foundation ✅ Complete

- [x] Define project requirements
- [x] Choose technology stack
- [x] Design UX flow and activation methods
- [x] Create project structure
- [x] Set up basic server/client architecture

### Phase 2: Basic Networking ✅ Complete

- [x] **Server (Linux Mint)**
  - [x] Create basic TCP server
  - [x] Implement mouse control using pynput
  - [x] Handle connection/disconnection gracefully
  - [x] Basic logging and error handling
- [x] **Client (Windows/Ubuntu)**

  - [x] Create basic TCP client
  - [x] Implement mouse position tracking
  - [x] Send mouse coordinates to server
  - [x] Connection management

- [x] **Shared Protocol**
  - [x] Define JSON message format
  - [x] Mouse movement messages
  - [x] Click event messages
  - [x] Connection handshake protocol

### Phase 3: Edge Detection System ✅ Complete

- [x] **Edge Trigger Logic**

  - [x] Monitor mouse position continuously
  - [x] Detect edge collision with configurable delay
  - [x] Prevent false triggers from fast movements
  - [x] Smooth transition animations
  - [x] Switch to continuous tracking in remote mode
  - [x] Real-time mouse movement synchronization

- [x] **Configuration System**
  - [x] Configurable trigger edge (top/bottom/left/right)
  - [x] Adjustable trigger delay (50-500ms)
  - [x] Return method selection (opposite edge/specific edge)
  - [x] Save/load user preferences
  - [x] Escape key exit mechanism

### Phase 4: Network Discovery ✅ Complete

- [x] **Auto-Discovery**

  - [x] Broadcast/multicast server discovery
  - [x] Local network scanning
  - [x] Device identification and naming
  - [x] Remember known devices
  - [x] Automatic fallback to discovered servers

- [x] **Manual Connection**
  - [x] IP address input
  - [x] Port configuration
  - [x] Connection testing
  - [x] Persistent connection list

### Phase 5: Hotkey System

- [ ] **Hotkey Handler**

  - [ ] Global hotkey registration (Ctrl+Alt+M default)
  - [x] Emergency escape key (Esc) ✅ Implemented
  - [ ] Toggle between local/remote control
  - [ ] Customizable key combinations

- [ ] **Integration**
  - [x] Coordinate with edge detection system ✅ Working
  - [x] Priority handling (escape overrides remote mode) ✅ Working
  - [x] State synchronization ✅ Working

### Phase 6: User Interface

- [ ] **System Tray Integration**

  - [ ] Connection status indicators (🔴🟡🟢)
  - [ ] Right-click context menu
  - [ ] Quick connect/disconnect
  - [ ] Settings access

- [ ] **Settings Window**

  - [ ] Edge selection dropdown
  - [ ] Trigger delay slider
  - [ ] Hotkey customization
  - [ ] Server discovery/manual IP entry
  - [ ] Connection preferences

- [ ] **Optimization**

  - [ ] Target <10ms latency
  - [ ] 60+ updates/second smoothness
  - [ ] Sub-pixel precision
  - [ ] Memory usage optimization

- [ ] **User Experience**

  - [ ] Smooth cursor transitions
  - [ ] Visual feedback for state changes
  - [ ] Error message improvements
  - [ ] Connection retry logic

- [ ] **Cross-Platform Testing**
  - [ ] Windows 11 client testing
  - [ ] Ubuntu client testing
  - [ ] Linux Mint server testing
  - [ ] Different screen resolutions
  - [ ] Multiple monitor setups

### Phase 7: Advanced Features (Future)

- [ ] **Enhanced Control**

  - [ ] Mouse scroll wheel support
  - [ ] Right-click context menus
  - [ ] Drag and drop operations
  - [ ] Acceleration/sensitivity matching

- [ ] **Multi-Device**

  - [ ] Connect to multiple servers
  - [ ] Device switching hotkeys
  - [ ] Simultaneous connections

- [ ] **Security**
  - [ ] Basic authentication
  - [ ] Encrypted communication
  - [ ] Access control lists

---

## Technical Specifications

### Message Protocol

```json
{
  "type": "mouse_move|mouse_click|mouse_scroll",
  "x": 0.0-1.0,           # Relative coordinates
  "y": 0.0-1.0,
  "button": "left|right|middle",  # For clicks
  "scroll_x": 0,          # For scroll events
  "scroll_y": 0,
  "timestamp": 1234567890
}
```

### Configuration Format

```json
{
  "trigger_edge": "right",
  "trigger_delay_ms": 150,
  "return_method": "opposite_edge",
  "hotkey": "ctrl+alt+m",
  "server_ip": "192.168.1.100",
  "server_port": 9876,
  "auto_connect": true
}
```

### File Structure

```
ZedLink/
├── client/
│   ├── main.py
│   ├── edge_detector.py
│   ├── hotkey_handler.py
│   ├── network_client.py
│   └── ui/
│       ├── tray_icon.py
│       └── settings.py
├── server/
│   ├── server.py
│   ├── mouse_controller.py
│   └── network_server.py
├── shared/
│   ├── protocol.py
│   └── config.py
├── requirements.txt
└── README.md
```

---

## Current Status: 🚧 **CORE FUNCTIONALITY WORKING - REFINEMENTS NEEDED**

**ZedLink basic remote mouse control is functional!**

✅ **Working:**

- Edge detection triggers (right edge → remote control)
- Real-time mouse movement synchronization
- Auto-discovery of Linux servers
- Clean escape mechanism (Esc key)
- Cross-platform compatibility (Windows ↔ Linux)

� **Current Issues Being Fixed:**

- Local mouse still moves when in remote mode (needs capture)
- Mouse clicks not forwarded to remote (implementing)

🚀 **Next Steps:** Mouse capture, click forwarding, UI improvements

## Notes

- Keep it simple and reliable
- Focus on low latency and smooth experience
- Edge trigger should feel natural like extending to another monitor
- Hotkey provides reliable fallback and emergency exit
