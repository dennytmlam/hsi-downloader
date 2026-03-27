import os
import logging
from datetime import datetime, timedelta
from config import *

logger = logging.getLogger(__name__)

class HSIHousekeeper:
    """
    Housekeeping module for HSI data downloader.
    
    Responsibilities:
    - Clean up old downloaded raw files (older than DOWNLOAD_RETENTION_DAYS)
    - Maintain organized folder structure
    - Report cleanup statistics
    """
    
    def __init__(self):
        self.downloads_dir = DOWNLOADS_DIR
        self.retention_days = DOWNLOAD_RETENTION_DAYS
    
    def run(self):
        """
        Run housekeeping tasks.
        
        Returns:
            dict with cleanup statistics
        """
        if not HOUSEKEEPING_ENABLED:
            logger.info("Housekeeping is disabled")
            return {"skipped": True, "files_deleted": 0, "space_freed_bytes": 0}
        
        if not os.path.exists(self.downloads_dir):
            logger.info(f"Downloads directory does not exist: {self.downloads_dir}")
            return {"skipped": True, "files_deleted": 0, "space_freed_bytes": 0}
        
        logger.info(f"Running housekeeping: cleaning files older than {self.retention_days} days")
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        files_deleted = 0
        space_freed_bytes = 0
        
        for filename in os.listdir(self.downloads_dir):
            file_path = os.path.join(self.downloads_dir, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
            
            try:
                # Get file modification time
                mtime = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(mtime)
                
                # Delete if older than cutoff
                if file_date < cutoff_date:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    files_deleted += 1
                    space_freed_bytes += file_size
                    logger.debug(f"Deleted old file: {filename} ({file_size} bytes, modified {file_date.strftime('%Y-%m-%d')})")
                    
            except OSError as e:
                logger.warning(f"Failed to process file {filename}: {e}")
        
        logger.info(f"Housekeeping complete: deleted {files_deleted} files, freed {self._format_bytes(space_freed_bytes)}")
        
        return {
            "skipped": False,
            "files_deleted": files_deleted,
            "space_freed_bytes": space_freed_bytes,
            "space_freed": self._format_bytes(space_freed_bytes)
        }
    
    def _format_bytes(self, size_bytes):
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def get_stats(self):
        """
        Get current statistics about downloads directory.
        
        Returns:
            dict with directory statistics
        """
        if not os.path.exists(self.downloads_dir):
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size": "0 B",
                "oldest_file": None,
                "newest_file": None
            }
        
        files = []
        for filename in os.listdir(self.downloads_dir):
            file_path = os.path.join(self.downloads_dir, filename)
            if os.path.isfile(file_path):
                try:
                    mtime = os.path.getmtime(file_path)
                    size = os.path.getsize(file_path)
                    files.append({
                        "name": filename,
                        "path": file_path,
                        "mtime": datetime.fromtimestamp(mtime),
                        "size": size
                    })
                except OSError:
                    continue
        
        if not files:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size": "0 B",
                "oldest_file": None,
                "newest_file": None
            }
        
        total_size = sum(f["size"] for f in files)
        files.sort(key=lambda x: x["mtime"])
        
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size": self._format_bytes(total_size),
            "oldest_file": files[0]["name"],
            "oldest_file_date": files[0]["mtime"].strftime('%Y-%m-%d'),
            "newest_file": files[-1]["name"],
            "newest_file_date": files[-1]["mtime"].strftime('%Y-%m-%d')
        }
