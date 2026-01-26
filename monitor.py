#!/usr/bin/env python3
"""
Standalone Monitor Script
Run monitoring without web dashboard
"""

import asyncio
import signal
import sys
from loguru import logger
from pathlib import Path

from app.config import settings
from app.monitor.ping_service import PingService
from app.monitor.state_manager import StateManager
from app.monitor.notification_service import NotificationService


class StandaloneMonitor:
    """Standalone monitoring service"""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.ping_service = PingService()
        self.notification_service = NotificationService()
        self.running = True
        self.tasks = []
    
    def setup_logging(self):
        """Configure logging"""
        logger.remove()
        
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level=settings.log_level,
            colorize=True
        )
        
        log_file = settings.log_dir / "monitor.log"
        logger.add(
            log_file,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        )
    
    async def get_hosts(self):
        """Get current hosts"""
        return await self.state_manager.load_hosts()
    
    async def get_states(self):
        """Get current states"""
        return await self.state_manager.load_states()
    
    async def save_states(self, states):
        """Save states"""
        await self.state_manager.save_states(states)
    
    async def handle_notifications(self, notifications):
        """Handle notifications"""
        self.notification_service.queue_notifications(notifications)
    
    async def start(self):
        """Start monitoring"""
        logger.info("=" * 60)
        logger.info("IP Monitor - Standalone Mode")
        logger.info("=" * 60)
        
        # Initialize notification service
        await self.notification_service.initialize()
        
        # Get host count
        hosts = await self.state_manager.load_hosts()
        logger.info(f"Loaded {len(hosts)} hosts for monitoring")
        
        if not hosts:
            logger.warning("No hosts configured. Please add hosts to data/hosts.json")
            logger.info("Example format:")
            logger.info('[{"ip": "8.8.8.8", "name": "Google DNS", "enabled": true, "tags": []}]')
            return
        
        # Send startup notification
        await self.notification_service.send_startup_notification(len(hosts))
        
        # Configuration info
        logger.info(f"Configuration:")
        logger.info(f"  - Ping Interval: {settings.ping_interval}s")
        logger.info(f"  - Max Retries: {settings.max_retries}")
        logger.info(f"  - Concurrent Pings: {settings.concurrent_pings}")
        logger.info(f"  - Batch Interval: {settings.batch_interval}s")
        logger.info("=" * 60)
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(
            self.ping_service.continuous_monitor(
                self.get_hosts,
                self.get_states,
                self.save_states,
                self.handle_notifications
            )
        )
        
        notifier_task = asyncio.create_task(
            self.notification_service.continuous_sender()
        )
        
        self.tasks = [monitor_task, notifier_task]
        
        logger.info("✓ Monitoring started")
        logger.info("✓ Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Wait for tasks
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")
    
    async def stop(self):
        """Stop monitoring"""
        logger.info("\nStopping monitor...")
        
        self.running = False
        
        # Stop services
        self.ping_service.stop()
        self.notification_service.stop()
        
        # Cancel tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Send shutdown notification
        await self.notification_service.send_shutdown_notification()
        
        # Close notification service
        await self.notification_service.close()
        
        logger.info("✓ Monitor stopped")


async def main():
    """Main function"""
    monitor = StandaloneMonitor()
    monitor.setup_logging()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(monitor.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        await monitor.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await monitor.stop()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nExiting...")
        sys.exit(0)
