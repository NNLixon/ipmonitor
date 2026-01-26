# app/models.py
"""
Data Models Module
Defines all Pydantic models for the application
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import ipaddress


class HostStatus(str, Enum):
    """Host status enumeration"""
    UP = "UP"
    DOWN = "DOWN"
    CHECKING = "CHECKING"
    UNKNOWN = "UNKNOWN"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    HOST_DOWN = "HOST_DOWN"
    HOST_UP = "HOST_UP"
    HOST_STATUS = "HOST_STATUS"
    INFO = "INFO"
    ERROR = "ERROR"
    NEW_IP = "NEW_IP"
    FAILED = "FAILED"  # ADDED: For host failure notifications
    RECOVERED = "RECOVERED"  # ADDED: For host recovery notifications


class Notification(BaseModel):
    """Notification model"""
    type: NotificationType
    ip: str
    name: str
    timestamp: int
    extra: Optional[str] = None
    fail_count: Optional[int] = None


class HostState(BaseModel):
    """Host monitoring state"""
    ip: str
    name: str = "Unknown"  # ADDED: Name field
    status: HostStatus = HostStatus.UNKNOWN
    last_check: Optional[int] = None
    last_up: Optional[int] = None
    last_down: Optional[int] = None
    fail_count: int = 0
    consecutive_fails: int = 0
    consecutive_successes: int = 0
    total_downtime: int = 0  # ADDED: Total downtime in seconds
    fail_time: Optional[int] = None  # ADDED: Time when host failed
    
    def get_last_check_str(self) -> str:
        """Get last check time as human-readable string"""
        if not self.last_check:
            return "Never"
        
        from datetime import datetime
        dt = datetime.fromtimestamp(self.last_check)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_downtime_minutes(self) -> float:
        """Calculate downtime in minutes"""
        if self.status == HostStatus.UP or not self.fail_time:
            return 0.0
        
        from time import time
        downtime = time() - self.fail_time
        return round(downtime / 60, 2)  # Convert to minutes


class Host(BaseModel):
    """Host model for monitoring"""
    ip: str
    name: str
    enabled: bool = True
    tags: List[str] = []
    group_id: Optional[int] = None
    mac_address: Optional[str] = None
    vendor_info: Optional[str] = None
    
    @validator('ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")


class HostCreate(BaseModel):
    """Host creation model"""
    ip: str
    name: str
    enabled: bool = True
    tags: List[str] = []
    group_id: Optional[int] = None
    
    @validator('ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")


class HostUpdate(BaseModel):
    """Host update model"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    group_id: Optional[int] = None


class HostResponse(BaseModel):
    """Host response model for API"""
    id: int
    ip: str
    name: str
    status: str
    lastCheck: str
    downtime: float
    failCount: int
    enabled: bool
    tags: List[str]
    group_id: Optional[int]
    group_name: Optional[str]
    group_color: Optional[str]
    mac_address: Optional[str]
    vendor_info: Optional[str]


class GroupCreate(BaseModel):
    """Group creation model"""
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"
    icon: str = "🔵"


class GroupUpdate(BaseModel):
    """Group update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class GroupResponse(BaseModel):
    """Group response model"""
    id: int
    name: str
    description: Optional[str]
    color: str
    icon: str
    host_count: int
    created_at: int


class Stats(BaseModel):
    """System statistics model"""
    total: int = 0
    up: int = 0
    down: int = 0
    unknown: int = 0
    enabled: int = 0
    disabled: int = 0


class SystemStatus(BaseModel):
    """System status model"""
    is_running: bool
    stats: Stats
    uptime: Optional[int]
    recent_logs: List[str]


class ConfigUpdate(BaseModel):
    """Configuration update model"""
    discord_webhook_url: Optional[str] = None
    ping_interval: Optional[int] = None
    max_retries: Optional[int] = None
    ping_timeout: Optional[int] = None
    concurrent_pings: Optional[int] = None
    check_interval: Optional[int] = None
    batch_interval: Optional[int] = None
    max_batch_size: Optional[int] = None


class BulkEnableRequest(BaseModel):
    """Bulk enable/disable request model"""
    ips: List[str]
    enabled: bool


class BulkDeleteRequest(BaseModel):
    """Bulk delete request model"""
    ips: List[str]


class BulkGroupRequest(BaseModel):
    """Bulk group update request model"""
    ips: List[str]
    group_id: Optional[int] = None


class SubnetScanRequest(BaseModel):
    """Subnet scan request model"""
    subnet: str
    group_name: Optional[str] = None
    group_color: str = "#10B981"
    group_icon: str = "🌐"
    scan_mac: bool = True
    
    @validator('subnet')
    def validate_subnet(cls, v):
        """Validate subnet format"""
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f"Invalid subnet: {v}")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]


class PingResult(BaseModel):
    """Ping result model"""
    ip: str
    success: bool
    response_time: Optional[float] = None
    error: Optional[str] = None
    timestamp: int


class MonitorConfig(BaseModel):
    """Monitor configuration model"""
    ping_interval: int = 5
    max_retries: int = 3
    ping_timeout: int = 2
    concurrent_pings: int = 100
    check_interval: int = 10
    batch_interval: int = 5
    max_batch_size: int = 15


# ADDED: OTP Models for webhook validation
class OTPValidationRequest(BaseModel):
    """OTP validation request model"""
    otp: str


class OTPValidationResponse(BaseModel):
    """OTP validation response model"""
    success: bool
    message: str
    expires_in: Optional[int] = None
