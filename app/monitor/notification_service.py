# app/monitor/notification_service.py
"""
Notification Service Module
Handles Discord notifications with batching and rate limiting
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from loguru import logger
from datetime import datetime, timedelta
import secrets
import time
from ..config import settings
from ..models import Notification, NotificationType


class NotificationService:
    """Discord notification service with batching"""
    
    def __init__(self):
        self._webhook_url = None
        self.notification_queue: List[Notification] = []
        self._session: Optional[aiohttp.ClientSession] = None
        self._stop_event = asyncio.Event()
        self._pending_otp: Dict[str, Tuple[str, float]] = {}  # webhook_url: (otp, expiry_time)
        self._load_webhook()
    
    def _load_webhook(self):
        """Load webhook URL from settings"""
        self._webhook_url = settings.discord_webhook_url
    
    @property
    def webhook_url(self):
        """Get current webhook URL"""
        return self._webhook_url
    
    @webhook_url.setter
    def webhook_url(self, value: str):
        """Set webhook URL"""
        self._webhook_url = value
    
    def reload_config(self):
        """Reload configuration from settings"""
        self._load_webhook()
    
    async def initialize(self):
        """Initialize the service"""
        self._session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the service"""
        if self._session:
            await self._session.close()
    
    async def validate_webhook(self) -> Tuple[bool, str]:
        """Validate Discord webhook"""
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False, "Webhook URL not configured"
        
        try:
            payload = {
                "username": "IP Monitor",
                "content": "Webhook validation test"
            }
            
            async with self._session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 204]:
                    logger.info("✓ Discord webhook validated successfully")
                    return True, "Webhook validated successfully"
                else:
                    error_msg = f"Webhook validation failed: HTTP {resp.status}"
                    logger.error(f"✗ {error_msg}")
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"Webhook validation error: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def validate_webhook_with_otp(self, webhook_url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate webhook by sending OTP and expecting it to be verified
        
        Args:
            webhook_url: Discord webhook URL to validate
            
        Returns:
            Tuple of (success, message, otp)
        """
        if not webhook_url:
            return False, "Webhook URL is empty", None
        
        try:
            # Generate OTP (6-digit code)
            otp = secrets.randbelow(1000000)
            otp_str = f"{otp:06d}"
            expiry_time = time.time() + 600  # 10 minutes from now
            
            # Store OTP for verification
            self._pending_otp[webhook_url] = (otp_str, expiry_time)
            
            # Send OTP via Discord
            payload = {
                "username": "IP Monitor",
                "embeds": [{
                    "title": "🔐 Webhook Validation OTP",
                    "description": f"**OTP:** `{otp_str}`\n**Expires:** <t:{int(expiry_time)}:R>",
                    "color": 3447003,
                    "fields": [
                        {
                            "name": "Instructions",
                            "value": "Enter this OTP in the dashboard to validate your webhook.",
                            "inline": False
                        },
                        {
                            "name": "Important",
                            "value": "This OTP will expire in 10 minutes.",
                            "inline": False
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            async with self._session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 204]:
                    logger.info(f"OTP sent to webhook for validation: {otp_str}")
                    return True, f"OTP sent to webhook. Check Discord and enter the OTP below.", otp_str
                else:
                    error_text = await resp.text()
                    error_msg = f"Failed to send OTP: HTTP {resp.status} - {error_text}"
                    logger.error(error_msg)
                    
                    # Clean up pending OTP
                    if webhook_url in self._pending_otp:
                        del self._pending_otp[webhook_url]
                    
                    return False, error_msg, None
                    
        except Exception as e:
            error_msg = f"Error sending OTP: {e}"
            logger.error(error_msg)
            
            # Clean up pending OTP
            if webhook_url in self._pending_otp:
                del self._pending_otp[webhook_url]
            
            return False, error_msg, None
    
    async def verify_otp(self, webhook_url: str, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for webhook validation
        
        Args:
            webhook_url: Discord webhook URL
            otp: OTP to verify
            
        Returns:
            Tuple of (success, message)
        """
        if not webhook_url or not otp:
            return False, "Webhook URL and OTP are required"
        
        # Clean up expired OTPs first
        current_time = time.time()
        expired_urls = []
        for url, (stored_otp, expiry) in self._pending_otp.items():
            if current_time > expiry:
                expired_urls.append(url)
        
        for url in expired_urls:
            del self._pending_otp[url]
        
        # Check if OTP exists and is valid
        if webhook_url not in self._pending_otp:
            return False, "OTP not found or expired. Please request a new OTP."
        
        stored_otp, expiry = self._pending_otp[webhook_url]
        
        if current_time > expiry:
            del self._pending_otp[webhook_url]
            return False, "OTP has expired. Please request a new OTP."
        
        if otp != stored_otp:
            return False, "Invalid OTP. Please try again."
        
        # OTP is valid - remove it and update webhook
        del self._pending_otp[webhook_url]
        self.webhook_url = webhook_url
        
        # Save to settings
        settings.update(discord_webhook_url=webhook_url)
        
        # Send confirmation
        await self.send_webhook_validated_notification(webhook_url)
        
        logger.info(f"Webhook validated successfully: {webhook_url}")
        return True, "Webhook validated successfully!"
    
    async def send_webhook_validated_notification(self, webhook_url: str):
        """Send notification that webhook has been validated"""
        try:
            payload = {
                "username": "IP Monitor",
                "embeds": [{
                    "title": "✅ Webhook Validated Successfully",
                    "description": "Your webhook has been successfully validated and is now active.",
                    "color": 5763719,  # Green
                    "fields": [
                        {
                            "name": "Status",
                            "value": "Active ✓",
                            "inline": True
                        },
                        {
                            "name": "URL",
                            "value": f"`{webhook_url[:50]}...`",
                            "inline": False
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            async with self._session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 204]:
                    logger.info("Webhook validation confirmation sent")
                else:
                    logger.warning(f"Failed to send validation confirmation: HTTP {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error sending validation confirmation: {e}")
    
    def queue_notification(self, notification: Notification):
        """Queue a single notification"""
        if self.webhook_url:
            self.notification_queue.append(notification)
            logger.debug(f"Queued notification: {notification.type} for {notification.name}")
        else:
            logger.debug(f"Notification skipped (no webhook): {notification.type} for {notification.name}")
    
    def queue_notifications(self, notifications: List[Notification]):
        """Queue multiple notifications"""
        if self.webhook_url:
            self.notification_queue.extend(notifications)
            logger.debug(f"Queued {len(notifications)} notifications")
        elif notifications:
            logger.debug(f"Notifications skipped (no webhook): {len(notifications)}")
    
    def clear_queue(self):
        """Clear all queued notifications"""
        self.notification_queue.clear()
    
    def _create_embed(self, notification: Notification) -> Dict:
        """Create Discord embed from notification"""
        colors = {
            NotificationType.HOST_DOWN: 15548997,    # Red
            NotificationType.HOST_UP: 5763719,       # Green
            NotificationType.HOST_STATUS: 16776960,  # Yellow
            NotificationType.INFO: 3447003,          # Blue
            NotificationType.ERROR: 15548997,        # Red
            NotificationType.NEW_IP: 10181046,       # Purple
            NotificationType.FAILED: 15548997,       # Red
            NotificationType.RECOVERED: 5763719,     # Green
        }
        
        color = colors.get(notification.type, 3447003)
        
        # Set titles based on notification type
        titles = {
            NotificationType.HOST_DOWN: "🔴 Host Offline",
            NotificationType.HOST_UP: "🟢 Host Online",
            NotificationType.HOST_STATUS: "🟡 Status Change",
            NotificationType.INFO: "ℹ️ Information",
            NotificationType.ERROR: "🚨 Error",
            NotificationType.NEW_IP: "🆕 New Host Added",
            NotificationType.FAILED: "🔴 Host Failed",
            NotificationType.RECOVERED: "✅ Host Recovered",
        }
        
        embed = {
            "title": titles.get(notification.type, "Notification"),
            "color": color,
            "timestamp": datetime.utcfromtimestamp(notification.timestamp).isoformat(),
            "fields": []
        }
        
        # Add name field
        if notification.name:
            embed["fields"].append({
                "name": "Name",
                "value": notification.name,
                "inline": True
            })
        
        # Add IP field if not "0.0.0.0" (which indicates system notification)
        if notification.ip and notification.ip != "0.0.0.0":
            embed["fields"].append({
                "name": "IP Address",
                "value": f"`{notification.ip}`",
                "inline": True
            })
        
        # Add type-specific fields
        if notification.type == NotificationType.NEW_IP:
            embed["fields"].append({
                "name": "Action",
                "value": "New host added to monitoring",
                "inline": False
            })
        elif notification.type == NotificationType.FAILED:
            embed["fields"].append({
                "name": "Status",
                "value": "Host is now offline",
                "inline": False
            })
        elif notification.type == NotificationType.RECOVERED:
            embed["fields"].append({
                "name": "Status",
                "value": f"Host is back online after {notification.extra} minutes of downtime",
                "inline": False
            })
        
        # Add extra info if present
        if notification.extra:
            embed["fields"].append({
                "name": "Details",
                "value": notification.extra[:1024],  # Discord field value limit
                "inline": False
            })
        
        # Add fail count if present
        if notification.fail_count and notification.fail_count > 0:
            embed["fields"].append({
                "name": "Fail Count",
                "value": str(notification.fail_count),
                "inline": True
            })
        
        return embed
    
    def _create_batch_embed(self, notifications: List[Notification]) -> Dict:
        """Create batch notification embed"""
        # Group notifications by type
        grouped = defaultdict(list)
        for notif in notifications:
            grouped[notif.type].append(notif)
        
        embed = {
            "title": "📊 Batch Status Update",
            "color": 16776960,  # Yellow
            "timestamp": datetime.utcnow().isoformat(),
            "fields": []
        }
        
        # Add summary for each type
        type_order = [
            NotificationType.NEW_IP,
            NotificationType.RECOVERED,
            NotificationType.FAILED,
            NotificationType.HOST_UP,
            NotificationType.HOST_DOWN,
            NotificationType.INFO,
            NotificationType.ERROR
        ]
        
        for notif_type in type_order:
            notifs = grouped.get(notif_type, [])
            if notifs:
                type_titles = {
                    NotificationType.NEW_IP: "🆕 New Hosts",
                    NotificationType.RECOVERED: "✅ Recovered Hosts",
                    NotificationType.FAILED: "🔴 Failed Hosts",
                    NotificationType.HOST_UP: "🟢 Hosts Back Online",
                    NotificationType.HOST_DOWN: "🔴 Hosts Offline",
                    NotificationType.INFO: "ℹ️ Information",
                    NotificationType.ERROR: "🚨 Errors"
                }
                
                field_value = []
                for notif in notifs[:5]:  # Show first 5 of each type
                    if notif.ip and notif.ip != "0.0.0.0":
                        field_value.append(f"• {notif.name} (`{notif.ip}`)")
                    else:
                        field_value.append(f"• {notif.name}")
                
                if len(notifs) > 5:
                    field_value.append(f"... and {len(notifs) - 5} more")
                
                embed["fields"].append({
                    "name": f"{type_titles.get(notif_type, notif_type.name)} ({len(notifs)})",
                    "value": "\n".join(field_value) if field_value else "No details",
                    "inline": False
                })
        
        return embed
    
    async def send_batch_notification(self, notifications: List[Notification]) -> bool:
        """Send batch notification"""
        if not self.webhook_url or not notifications:
            return False
        
        try:
            embeds = [self._create_batch_embed(notifications)]
            
            payload = {
                "username": "IP Monitor",
                "embeds": embeds,
                "content": f"📊 **Batch Update** ({len(notifications)} events)"
            }
            
            async with self._session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 204]:
                    logger.info(f"✓ Batch notification sent ({len(notifications)} events)")
                    return True
                else:
                    logger.error(f"✗ Batch notification failed: HTTP {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Batch notification error: {e}")
            return False
    
    async def send_simple_notification(self, message: str, color: int = 3447003) -> bool:
        """Send simple text notification"""
        if not self.webhook_url:
            return False
        
        try:
            payload = {
                "username": "IP Monitor",
                "content": message
            }
            
            async with self._session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status in [200, 204]
                    
        except Exception as e:
            logger.error(f"Simple notification error: {e}")
            return False
    
    async def send_startup_notification(self, host_count: int):
        """Send monitoring started notification"""
        if not self.webhook_url:
            logger.info("Skipping startup notification (no webhook configured)")
            return False
        
        message = (
            f"✅ **Monitoring Started**\n"
            f"**Hosts:** {host_count}\n"
            f"**Ping Interval:** {settings.ping_interval}s\n"
            f"**Max Retries:** {settings.max_retries}\n"
            f"**Concurrent Pings:** {settings.concurrent_pings}"
        )
        return await self.send_simple_notification(message, 3447003)
    
    async def send_shutdown_notification(self):
        """Send monitoring stopped notification"""
        if not self.webhook_url:
            logger.info("Skipping shutdown notification (no webhook configured)")
            return False
        
        message = "🛑 **Monitoring Stopped**"
        return await self.send_simple_notification(message, 15548997)
    
    def stop(self):
        """Stop the notification service"""
        self._stop_event.set()
    
    def reset(self):
        """Reset the notification service"""
        self._stop_event.clear()
    
    async def continuous_sender(self):
        """Continuous loop to send notifications"""
        logger.info("Starting notification sender")
        
        while not self._stop_event.is_set():
            try:
                if not self.webhook_url:
                    await asyncio.sleep(settings.batch_interval)
                    continue
                
                # Wait for batch interval or max size
                await asyncio.sleep(settings.batch_interval)
                
                if self.notification_queue:
                    # Take up to max batch size
                    batch_size = min(len(self.notification_queue), settings.max_batch_size)
                    batch = self.notification_queue[:batch_size]
                    
                    if batch:
                        await self.send_batch_notification(batch)
                        # Remove sent notifications
                        self.notification_queue = self.notification_queue[batch_size:]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Notification loop error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Notification sender stopped")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.notification_queue)
    
    def has_webhook(self) -> bool:
        """Check if webhook is configured"""
        return bool(self.webhook_url)
