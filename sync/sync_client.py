"""
Sync Client Module for Hybrid Cloud Deployment
Handles syncing local attendance data to cloud backend
"""

import json
import logging
import queue
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class SyncClient:
    """
    Client for syncing attendance data from local system to cloud backend.
    
    Features:
    - Queues attendance records for sync
    - Retries on network failures
    - Persists unsent data to disk
    - Batch uploads
    - Async non-blocking operation
    """

    def __init__(
        self,
        cloud_url: str,
        local_queue_file: Optional[Path] = None,
        max_retries: int = 5,
        batch_size: int = 10,
        sync_interval: float = 5.0,
    ):
        """
        Initialize Sync Client.
        
        Args:
            cloud_url: Base URL of cloud backend (e.g., "https://your-app.onrender.com")
            local_queue_file: Path to persist unsent records
            max_retries: Maximum retry attempts per record
            batch_size: Number of records to batch per request
            sync_interval: Interval between sync attempts (seconds)
        """
        self.cloud_url = cloud_url.rstrip('/')
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.sync_interval = sync_interval
        
        # Queue for pending records
        self.pending_queue: queue.Queue = queue.Queue()
        
        # Persisted queue file
        self.local_queue_file = local_queue_file or Path(__file__).parent / '.sync_queue.json'
        
        # Tracking
        self.stats = {
            'total_synced': 0,
            'total_failed': 0,
            'total_queued': 0,
            'last_sync_time': None,
            'last_error': None,
        }
        
        # Thread control
        self.running = False
        self.sync_thread: Optional[threading.Thread] = None
        
        # Load persisted queue
        self._load_queue()
        
        logger.info(
            f"Sync Client initialized - Cloud URL: {self.cloud_url}, "
            f"Pending records: {self.pending_queue.qsize()}"
        )

    def queue_attendance(self, record: Dict[str, Any]) -> bool:
        """
        Queue an attendance record for sync.
        
        Args:
            record: Attendance record dict with keys:
                - name: Student name
                - confidence: Recognition confidence (0.0-1.0)
                - camera_id: Camera identifier
                - timestamp_iso: ISO timestamp
                - date: Date string (YYYY-MM-DD)
                - time: Time string (HH:MM:SS)
        
        Returns:
            True if record queued, False otherwise
        """
        try:
            # Validate required fields
            if not record.get('name'):
                logger.warning("Skipping record - missing name field")
                return False
            
            # Add metadata
            record['queued_at'] = datetime.now().isoformat()
            record['retry_count'] = 0
            
            self.pending_queue.put(record)
            self.stats['total_queued'] += 1
            
            logger.debug(f"Record queued for sync: {record['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue attendance record: {e}")
            return False

    def start_sync(self):
        """Start background sync thread."""
        if self.running:
            logger.warning("Sync thread already running")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        logger.info("Sync thread started")

    def stop_sync(self):
        """Stop background sync thread."""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("Sync thread stopped")

    def _sync_worker(self):
        """Background worker that periodically syncs queued records."""
        while self.running:
            try:
                self._process_queue()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                self.stats['last_error'] = str(e)
                time.sleep(self.sync_interval)

    def _process_queue(self):
        """Process pending records in batches."""
        if self.pending_queue.empty():
            return
        
        batch = []
        
        # Collect batch of records
        while len(batch) < self.batch_size and not self.pending_queue.empty():
            batch.append(self.pending_queue.get())
        
        logger.info(f"Processing batch of {len(batch)} records")
        
        # Attempt to sync each record
        failed_records = []
        for record in batch:
            if self._sync_record(record):
                self.stats['total_synced'] += 1
            else:
                failed_records.append(record)
                self.stats['total_failed'] += 1
        
        # Re-queue failed records
        for record in failed_records:
            if record.get('retry_count', 0) < self.max_retries:
                record['retry_count'] = record.get('retry_count', 0) + 1
                self.pending_queue.put(record)
                logger.debug(
                    f"Re-queued {record['name']} "
                    f"(retry {record['retry_count']}/{self.max_retries})"
                )
            else:
                logger.error(
                    f"Dropped record after {self.max_retries} retries: {record['name']}"
                )
        
        # Persist queue if there are remaining items
        if not self.pending_queue.empty():
            self._save_queue()

    def _sync_record(self, record: Dict[str, Any]) -> bool:
        """
        Attempt to sync a single record to cloud.
        
        Args:
            record: Attendance record
        
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f"{self.cloud_url}/api/attendance/mark"
            
            # Remove metadata before sending
            sync_payload = {k: v for k, v in record.items() 
                           if k not in ['queued_at', 'retry_count']}
            
            response = requests.post(
                endpoint,
                json=sync_payload,
                timeout=10,
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Synced record: {record['name']} to {endpoint}")
                self.stats['last_sync_time'] = datetime.now().isoformat()
                return True
            else:
                logger.warning(
                    f"Failed to sync {record['name']}: "
                    f"Status {response.status_code} - {response.text}"
                )
                self.stats['last_error'] = response.text
                return False
                
        except requests.ConnectionError as e:
            logger.warning(f"Connection error syncing {record['name']}: {e}")
            self.stats['last_error'] = f"Connection error: {str(e)}"
            return False
        except requests.Timeout as e:
            logger.warning(f"Timeout syncing {record['name']}: {e}")
            self.stats['last_error'] = f"Request timeout: {str(e)}"
            return False
        except Exception as e:
            logger.error(f"Error syncing {record['name']}: {e}")
            self.stats['last_error'] = str(e)
            return False

    def _save_queue(self):
        """Persist pending queue to disk."""
        try:
            items = []
            temp_queue = queue.Queue()
            
            # Extract all items
            while not self.pending_queue.empty():
                item = self.pending_queue.get()
                items.append(item)
                temp_queue.put(item)
            
            # Restore queue
            self.pending_queue = temp_queue
            
            # Save to file
            with open(self.local_queue_file, 'w') as f:
                json.dump(items, f, indent=2)
            
            logger.debug(f"Persisted {len(items)} pending records to {self.local_queue_file}")
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")

    def _load_queue(self):
        """Load persisted queue from disk."""
        try:
            if self.local_queue_file.exists():
                with open(self.local_queue_file, 'r') as f:
                    items = json.load(f)
                
                for item in items:
                    self.pending_queue.put(item)
                
                logger.info(f"Loaded {len(items)} persisted records from {self.local_queue_file}")
                
                # Remove the file after loading
                self.local_queue_file.unlink()
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics."""
        return {
            **self.stats,
            'pending_records': self.pending_queue.qsize(),
        }

    def force_sync(self):
        """Force immediate sync of pending records."""
        logger.info("Forcing immediate sync...")
        self._process_queue()

    def is_healthy(self) -> bool:
        """Check if sync is healthy."""
        # Considered unhealthy if:
        # - Too many pending records
        # - High failure rate
        pending = self.pending_queue.qsize()
        total_attempts = self.stats['total_synced'] + self.stats['total_failed']
        
        if pending > 100:
            return False
        
        if total_attempts > 0:
            failure_rate = self.stats['total_failed'] / total_attempts
            if failure_rate > 0.5:
                return False
        
        return True


# Global sync client instance
_sync_client: Optional[SyncClient] = None


def init_sync_client(cloud_url: str, **kwargs) -> SyncClient:
    """
    Initialize global sync client.
    
    Args:
        cloud_url: Cloud backend URL
        **kwargs: Additional arguments for SyncClient
    
    Returns:
        SyncClient instance
    """
    global _sync_client
    _sync_client = SyncClient(cloud_url, **kwargs)
    return _sync_client


def get_sync_client() -> Optional[SyncClient]:
    """Get global sync client instance."""
    return _sync_client


def queue_for_sync(record: Dict[str, Any]):
    """Queue a record for sync using global client."""
    if _sync_client:
        _sync_client.queue_attendance(record)
    else:
        logger.warning("Sync client not initialized")
