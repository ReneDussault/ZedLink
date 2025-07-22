"""
Configuration Management for ZedLink

Handles user preferences, settings persistence, and configuration validation.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

try:
    from .edge_detector import TriggerEdge
except ImportError:
    # For standalone testing
    from edge_detector import TriggerEdge


@dataclass
class ZedLinkConfig:
    """ZedLink configuration settings"""
    
    # Edge Detection Settings
    trigger_edge: str = "right"
    trigger_delay: float = 0.1
    edge_threshold: int = 2
    
    # Network Settings
    server_host: str = "192.168.1.100"
    server_port: int = 9876
    connection_timeout: float = 5.0
    auto_reconnect: bool = True
    
    # Hotkey Settings
    enable_hotkeys: bool = True
    activation_hotkey: str = "ctrl+alt+m"
    escape_hotkey: str = "esc"
    
    # UI Settings
    show_notifications: bool = True
    minimize_to_tray: bool = True
    start_minimized: bool = False
    
    # Advanced Settings
    mouse_sensitivity: float = 1.0
    smooth_movement: bool = True
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZedLinkConfig':
        """Create from dictionary"""
        # Validate and filter known fields
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def validate(self) -> bool:
        """Validate configuration values"""
        try:
            # Validate trigger edge
            TriggerEdge(self.trigger_edge)
            
            # Validate numeric ranges
            assert 0.05 <= self.trigger_delay <= 2.0, "trigger_delay must be between 0.05 and 2.0"
            assert 1 <= self.edge_threshold <= 50, "edge_threshold must be between 1 and 50"
            assert 1024 <= self.server_port <= 65535, "server_port must be between 1024 and 65535"
            assert 1.0 <= self.connection_timeout <= 30.0, "connection_timeout must be between 1.0 and 30.0"
            assert 0.1 <= self.mouse_sensitivity <= 5.0, "mouse_sensitivity must be between 0.1 and 5.0"
            
            return True
        except (ValueError, AssertionError) as e:
            logging.error(f"Configuration validation failed: {e}")
            return False


class ConfigManager:
    """Manages ZedLink configuration persistence and loading"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Custom config directory. If None, uses platform default.
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = self._get_default_config_dir()
            
        self.config_file = self.config_dir / "zedlink_config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Config file: {self.config_file}")
        
    def _get_default_config_dir(self) -> Path:
        """Get platform-appropriate config directory"""
        if os.name == 'nt':  # Windows
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            return Path(base) / "ZedLink"
        else:  # Linux/macOS
            base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
            return Path(base) / "zedlink"
    
    def load_config(self) -> ZedLinkConfig:
        """Load configuration from file, create default if not exists"""
        if not self.config_file.exists():
            self.logger.info("No config file found, creating default configuration")
            config = ZedLinkConfig()
            self.save_config(config)
            return config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = ZedLinkConfig.from_dict(data)
            
            if not config.validate():
                self.logger.warning("Invalid config loaded, falling back to defaults")
                config = ZedLinkConfig()
                self.save_config(config)
                
            self.logger.info("Configuration loaded successfully")
            return config
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Failed to load config: {e}")
            self.logger.info("Creating default configuration")
            config = ZedLinkConfig()
            self.save_config(config)
            return config
    
    def save_config(self, config: ZedLinkConfig) -> bool:
        """Save configuration to file"""
        try:
            if not config.validate():
                self.logger.error("Cannot save invalid configuration")
                return False
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
                
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Update specific configuration values"""
        config = self.load_config()
        
        # Update provided values
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                self.logger.debug(f"Updated config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown config key: {key}")
        
        return self.save_config(config)
    
    def reset_config(self) -> bool:
        """Reset configuration to defaults"""
        self.logger.info("Resetting configuration to defaults")
        config = ZedLinkConfig()
        return self.save_config(config)
    
    def get_config_path(self) -> str:
        """Get the path to the config file"""
        return str(self.config_file)
    
    def backup_config(self, backup_suffix: Optional[str] = None) -> bool:
        """Create a backup of the current config"""
        if not self.config_file.exists():
            self.logger.warning("No config file to backup")
            return False
            
        try:
            if backup_suffix is None:
                import datetime
                backup_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
            backup_file = self.config_file.with_suffix(f".backup_{backup_suffix}.json")
            
            import shutil
            shutil.copy2(self.config_file, backup_file)
            
            self.logger.info(f"Config backed up to: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup config: {e}")
            return False


# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> ZedLinkConfig:
    """Get the current configuration"""
    return get_config_manager().load_config()

def save_config(config: ZedLinkConfig) -> bool:
    """Save configuration"""
    return get_config_manager().save_config(config)

def update_config(**kwargs) -> bool:
    """Update configuration values"""
    return get_config_manager().update_config(**kwargs)


if __name__ == "__main__":
    """Test configuration management"""
    import tempfile
    import sys
    import os
    
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(__file__))
    from edge_detector import TriggerEdge
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing config in: {temp_dir}")
        
        # Create config manager
        manager = ConfigManager(temp_dir)
        
        # Load default config
        config = manager.load_config()
        print(f"Default config: {config}")
        
        # Update some values
        config.trigger_edge = "left"
        config.trigger_delay = 0.3
        config.server_host = "192.168.1.50"
        
        # Save updated config
        success = manager.save_config(config)
        print(f"Save success: {success}")
        
        # Load again to verify persistence
        config2 = manager.load_config()
        print(f"Loaded config: {config2}")
        print(f"Configs match: {config == config2}")
        
        # Test validation
        config.trigger_delay = 10.0  # Invalid value
        print(f"Invalid config validates: {config.validate()}")
        
        # Test update method
        manager.update_config(debug_mode=True, trigger_edge="top")
        config3 = manager.load_config()
        print(f"Updated config: debug_mode={config3.debug_mode}, trigger_edge={config3.trigger_edge}")
