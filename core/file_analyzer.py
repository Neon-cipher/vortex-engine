import os
import hashlib
from datetime import datetime, timezone

def generate_file_hash(filepath, blocksize=65536):
    """Generates SHA256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as afile:
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
        return hasher.hexdigest()
    except Exception as e:
        return f"Error reading file: {e}"

def analyze_directory(directory_path):
    """Walks directory, extracts MAC times, hashes, and returns timeline events."""
    events = []
    
    if not os.path.isdir(directory_path):
        return events

    for root, dirs, files in os.walk(directory_path):
        for name in files:
            filepath = os.path.join(root, name)
            
            try:
                stat_info = os.stat(filepath)
            except Exception:
                continue

            # Convert timestamps to UTC datetime objects
            try:
                m_time = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                a_time = datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc)
                c_time = datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc)
            except Exception:
                 continue
                 
            file_hash = generate_file_hash(filepath)

            # Create distinct events for Modified, Accessed, Created
            events.append({
                'timestamp': m_time,
                'source': 'File System',
                'type': 'File Modified',
                'description': f"File: {filepath} | SHA256: {file_hash}"
            })
            
            events.append({
                'timestamp': a_time,
                'source': 'File System',
                'type': 'File Accessed',
                'description': f"File: {filepath} | SHA256: {file_hash}"
            })
            
            events.append({
                'timestamp': c_time,
                'source': 'File System',
                'type': 'File Created/Changed',
                'description': f"File: {filepath} | SHA256: {file_hash}"
            })

    return events
