# ZedLink - Remote Mouse Control

A lightweight tool to control a remote PC's mouse pointer over the network using edge triggers and hotkey controls.

## Features

- **Edge Trigger**: Move mouse to screen edge to control remote PC (like multi-monitor)
- **Hotkey Fallback**: Keyboard shortcuts for explicit control
- **Cross-Platform**: Windows ↔ Linux ↔ macOS (any combination)
- **Low Latency**: Sub-10ms response time on local network
- **Minimal Dependencies**: Just pynput + Python standard library
- **Auto-Detection**: Screen resolution and platform-specific optimizations

## Platform Support

| Client (Controller) | Server (Remote PC) | Status       |
| ------------------- | ------------------ | ------------ |
| Windows 10/11       | Linux              | ✅ Primary   |
| Linux               | Linux              | ✅ Excellent |
| Windows 10/11       | Windows 10/11      | ✅ Works     |
| macOS               | Any                | ⚠️ Untested  |

See `COMPATIBILITY.md` for detailed platform information.

## Quick Start

### Server (Remote PC)

```bash
cd server/
python server.py
```

### Client (Controller PC)

```bash
cd client/
python main.py
```

## Configuration

- Choose trigger edge (top/bottom/left/right)
- Adjust trigger delay sensitivity
- Customize hotkey combinations
- Auto-discovery or manual IP connection

## Status: 🚧 In Development

See `TODO.md` for current progress and roadmap.
