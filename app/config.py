# app/config.py
"""
Configuration Management Module
Handles all application configuration using Pydantic
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from pathlib import Path
from typing import Optional, Dict, Any
import json


class Settings(BaseSettings):
    """Application Settings"""
    
    # Discord Configuration
    discord_webhook_url: str = Field(default="", env="DISCORD_WEBHOOK_URL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Monitoring Configuration
    ping_interval: int = Field(default=5, env="PING_INTERVAL", ge=1, le=3600)
    max_retries: int = Field(default=3, env="MAX_RETRIES", ge=1, le=10)
    ping_timeout: int = Field(default=2, env="PING_TIMEOUT", ge=1, le=10)
    concurrent_pings: int = Field(default=100, env="CONCURRENT_PINGS", ge=1, le=1000)
    check_interval: int = Field(default=10, env="CHECK_INTERVAL", ge=1, le=300)
    
    # Notification Configuration
    batch_interval: int = Field(default=5, env="BATCH_INTERVAL", ge=1, le=60)
    max_batch_size: int = Field(default=15, env="MAX_BATCH_SIZE", ge=1, le=50)
    
    # Data Paths
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    log_dir: Path = Field(default=Path("./data/logs"), env="LOG_DIR")
    config_file: Path = Field(default=Path("./data/config.json"), env="CONFIG_FILE")
    hosts_file: Path = Field(default=Path("./data/hosts.json"), env="HOSTS_FILE")
    states_file: Path = Field(default=Path("./data/states.json"), env="STATES_FILE")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_rotation: str = Field(default="10 MB", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("data_dir", "log_dir", pre=True)
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_to_file(self):
        """Save current configuration to JSON file"""
        config_data = {
            "discord_webhook_url": self.discord_webhook_url,
            "ping_interval": self.ping_interval,
            "max_retries": self.max_retries,
            "ping_timeout": self.ping_timeout,
            "concurrent_pings": self.concurrent_pings,
            "check_interval": self.check_interval,
            "batch_interval": self.batch_interval,
            "max_batch_size": self.max_batch_size,
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_from_file(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def update(self, **kwargs):
        """Update configuration values and save to file"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save_to_file()
    
    def reload(self):
        """Reload configuration from file"""
        self.load_from_file()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "discord_webhook_url": self.discord_webhook_url,
            "ping_interval": self.ping_interval,
            "max_retries": self.max_retries,
            "ping_timeout": self.ping_timeout,
            "concurrent_pings": self.concurrent_pings,
            "check_interval": self.check_interval,
            "batch_interval": self.batch_interval,
            "max_batch_size": self.max_batch_size,
        }


# Global settings instance
settings = Settings()

# Load from file if exists
settings.load_from_file()
