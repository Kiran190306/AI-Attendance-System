"""
Example: Run AI Attendance with Cloud Sync
This shows how to integrate the cloud sync module into your attendance system.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_file = Path(__file__).parent / '.env.local'
load_dotenv(env_file)

# Configuration
CLOUD_API_URL = os.getenv('CLOUD_API_URL')
CLOUD_SYNC_ENABLED = os.getenv('CLOUD_SYNC_ENABLED', 'true').lower() == 'true'
SYNC_BATCH_SIZE = int(os.getenv('SYNC_BATCH_SIZE', 10))
SYNC_INTERVAL = float(os.getenv('SYNC_INTERVAL_SECONDS', 5))
SYNC_MAX_RETRIES = int(os.getenv('SYNC_MAX_RETRIES', 5))


def init_cloud_sync():
    """Initialize cloud sync client if enabled."""
    if not CLOUD_SYNC_ENABLED or not CLOUD_API_URL:
        logger.info("Cloud sync is disabled")
        return None
    
    try:
        from sync import init_sync_client
        
        logger.info(f"Initializing cloud sync: {CLOUD_API_URL}")
        sync_client = init_sync_client(
            cloud_url=CLOUD_API_URL,
            batch_size=SYNC_BATCH_SIZE,
            sync_interval=SYNC_INTERVAL,
            max_retries=SYNC_MAX_RETRIES
        )
        
        # Start background sync worker
        sync_client.start_sync()
        logger.info("✓ Cloud sync started")
        
        return sync_client
        
    except ImportError:
        logger.error("Sync module not found. Install with: pip install requests")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize cloud sync: {e}")
        return None


def init_attendance_service():
    """Initialize attendance service with cloud sync."""
    try:
        from core.attendance_service_cloud import AttendanceServiceWithCloudSync
        
        logger.info("Initializing attendance service with cloud sync")
        
        attendance = AttendanceServiceWithCloudSync(
            csv_path='attendance/attendance.csv',
            enable_cloud_sync=CLOUD_SYNC_ENABLED
        )
        
        logger.info("✓ Attendance service initialized")
        return attendance
        
    except Exception as e:
        logger.error(f"Failed to initialize attendance service: {e}")
        return None


def print_status(attendance_service, sync_client):
    """Print current system status."""
    print("\n" + "=" * 60)
    print("   AI ATTENDANCE SYSTEM - CLOUD DEPLOYMENT STATUS")
    print("=" * 60)
    
    # Attendance stats
    if attendance_service:
        stats = attendance_service.get_session_stats()
        print(f"\n📋 Attendance Service:")
        print(f"   Recognized: {stats.get('recognized_count', 0)}")
        print(f"   Unknown: {stats.get('unknown_count', 0)}")
        print(f"   Marked today: {stats.get('marked_today', 0)}")
    
    # Sync status
    if sync_client:
        sync_stats = sync_client.get_stats()
        print(f"\n☁️  Cloud Sync:")
        print(f"   Status: {'✓ Running' if sync_client.running else '✗ Stopped'}")
        print(f"   Cloud URL: {CLOUD_API_URL}")
        print(f"   Pending records: {sync_stats.get('pending_records', 0)}")
        print(f"   Total synced: {sync_stats.get('total_synced', 0)}")
        print(f"   Total failed: {sync_stats.get('total_failed', 0)}")
        print(f"   Last sync: {sync_stats.get('last_sync_time', 'Never')}")
        print(f"   Health: {'✓ Good' if sync_client.is_healthy() else '⚠ Warning'}")
    elif CLOUD_SYNC_ENABLED:
        print(f"\n☁️  Cloud Sync: ✗ Disabled or not configured")
    
    print("\n" + "=" * 60)


def example_mark_attendance(attendance_service):
    """Example: Mark attendance for multiple students."""
    if not attendance_service:
        logger.error("Attendance service not initialized")
        return
    
    # Example students
    students = [
        ("Alice Johnson", 0.98, "camera_1"),
        ("Bob Smith", 0.95, "camera_1"),
        ("Charlie Brown", 0.92, "camera_2"),
    ]
    
    logger.info("Marking example attendance records...")
    
    for name, confidence, camera_id in students:
        result = attendance_service.mark(
            student_name=name,
            confidence=confidence,
            camera_id=camera_id
        )
        
        status = "✓ Marked" if result else "✗ Already marked"
        logger.info(f"{status}: {name} (confidence: {confidence:.0%})")
    
    # Show status
    print_status(attendance_service, sync_client=None)


def main():
    """Main entry point."""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   AI ATTENDANCE SYSTEM - HYBRID CLOUD DEPLOYMENT           ║
    ║   Example: Running with Cloud Sync Integration             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting AI Attendance System with Cloud Sync...")
    
    # Initialize components
    sync_client = init_cloud_sync()
    attendance_service = init_attendance_service()
    
    if not attendance_service:
        logger.error("Failed to initialize attendance service")
        return 1
    
    # Print status
    print_status(attendance_service, sync_client)
    
    # Example: Mark some attendance
    example_mark_attendance(attendance_service)
    
    # Wait for sync to complete
    if sync_client:
        logger.info("Waiting for sync to complete...")
        import time
        time.sleep(2)
        
        logger.info("Forcing sync of all pending records...")
        sync_client.force_sync()
        
        logger.info("Final sync status:")
        stats = sync_client.get_stats()
        print(f"  ✓ Synced: {stats['total_synced']}")
        print(f"  ✗ Failed: {stats['total_failed']}")
        print(f"  ⏳ Pending: {stats['pending_records']}")
    
    logger.info("✓ Example completed successfully!")
    
    # Keep running to demonstrate background sync
    if sync_client:
        logger.info("\nKeeping sync running. Press Ctrl+C to exit...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping...")
            sync_client.stop_sync()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
